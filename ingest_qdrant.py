import os
import json
import uuid
import hashlib
import argparse

from qdrant_client import QdrantClient, models

import rag_core as core

# Configs (single source of truth lives in rag_core)
DOCS_DIR = core.DOCS_DIR
QDRANT_HOST = core.QDRANT_HOST
QDRANT_PORT = core.QDRANT_PORT
COLLECTION_NAME = core.COLLECTION_NAME
MANIFEST_PATH = ".ingest_manifest.json"            # per-file content hashes for incremental ingest
ID_NAMESPACE = uuid.UUID("a3f1c9e2-1b6d-4e8a-9c0f-7d2b5e4a8c11")  # deterministic point IDs


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_manifest(manifest):
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def chunk_point_id(rel_path, idx):
    return str(uuid.uuid5(ID_NAMESPACE, f"{rel_path}::{idx}"))


def delete_points_for_source(client, rel_path):
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=models.Filter(must=[models.FieldCondition(
                key="metadata.source", match=models.MatchValue(value=rel_path),
            )])
        ),
    )


def build_points(rel_path, chunks):
    """Embed chunks into dense + (optional) BM25 sparse vectors and build PointStructs."""
    texts = [c["text"] for c in chunks]
    dense = core.embed_dense(texts, show_progress_bar=False)
    sparse = core.embed_sparse(texts)  # [] if fastembed unavailable
    have_sparse = len(sparse) == len(texts)

    points = []
    for idx, c in enumerate(chunks):
        vector = {core.DENSE_VECTOR: dense[idx].tolist()}
        if have_sparse:
            vector[core.SPARSE_VECTOR] = core.to_sparse_vector(sparse[idx])
        points.append(models.PointStruct(
            id=chunk_point_id(rel_path, idx),
            vector=vector,
            payload={"page_content": c["text"], "metadata": c["metadata"]},
        ))
    return points, have_sparse


def ingest_documents(full_reindex=False):
    print(f"Loading dense model '{core.DENSE_MODEL_NAME}'...")
    embedder = core.load_dense_model()
    vector_size = embedder.encode("test string").shape[0]
    print(f"Dense model ready. dim={vector_size}, max_seq_length={embedder.max_seq_length}")

    sparse_ok = core.load_sparse_model() is not None
    print(f"Sparse (BM25) model: {'ready' if sparse_ok else 'UNAVAILABLE (install fastembed) -> dense-only index'}")

    print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        existing = [c.name for c in client.get_collections().collections]
    except Exception as e:
        print(f"\n[Error] Could not connect to Qdrant: {e}")
        print("Start Qdrant first (qdrant\\qdrant.exe, or run_chatbot.bat option [4]). Hybrid search needs Qdrant >= 1.10.")
        return

    if full_reindex and COLLECTION_NAME in existing:
        print(f"--full: deleting existing collection '{COLLECTION_NAME}'...")
        client.delete_collection(COLLECTION_NAME)
        existing.remove(COLLECTION_NAME)

    if COLLECTION_NAME not in existing:
        sparse_config = (
            {core.SPARSE_VECTOR: models.SparseVectorParams(modifier=models.Modifier.IDF)}
            if sparse_ok else None
        )
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={core.DENSE_VECTOR: models.VectorParams(size=vector_size, distance=models.Distance.COSINE)},
            sparse_vectors_config=sparse_config,
        )
        print(f"Created collection '{COLLECTION_NAME}' (dense{'+bm25' if sparse_ok else ' only'}).")
        manifest = {}
    else:
        print(f"Using existing collection '{COLLECTION_NAME}' (incremental mode).")
        manifest = load_manifest()

    # Gather markdown files + current hashes
    md_files = []
    for root, _dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))

    new_manifest, changed_files = {}, []
    for path in md_files:
        rel = os.path.relpath(path, DOCS_DIR)
        h = file_hash(path)
        new_manifest[rel] = h
        if manifest.get(rel) != h:
            changed_files.append(path)

    removed = [rel for rel in manifest if rel not in new_manifest]

    if not changed_files and not removed:
        print("No changes detected. Index is already up to date.")
        save_manifest(new_manifest)
        return

    print(f"To (re)index: {len(changed_files)}, removed: {len(removed)}, "
          f"unchanged: {len(md_files) - len(changed_files)}")

    for rel in removed:
        print(f"  Deleting points for removed file: {rel}")
        delete_points_for_source(client, rel)

    total_points = 0
    for path in changed_files:
        rel = os.path.relpath(path, DOCS_DIR)
        try:
            chunks = core.chunk_markdown(path, DOCS_DIR)
        except Exception as e:
            print(f"  Error parsing {path}: {e}")
            continue

        delete_points_for_source(client, rel)  # clear stale points first (handles chunk-count changes)
        if not chunks:
            continue

        points, _ = build_points(rel, chunks)
        for i in range(0, len(points), 100):
            client.upsert(collection_name=COLLECTION_NAME, wait=True, points=points[i:i + 100])
        total_points += len(points)
        print(f"  Indexed {rel}: {len(points)} chunks")

    save_manifest(new_manifest)
    print(f"\n[Success] Ingestion complete. Upserted {total_points} chunks across "
          f"{len(changed_files)} file(s); removed {len(removed)} file(s).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest Runway docs into Qdrant as a hybrid (dense+BM25) index. Incremental by default."
    )
    parser.add_argument("--full", action="store_true",
                        help="Force a full re-index (drop & recreate the collection).")
    args = parser.parse_args()
    ingest_documents(full_reindex=args.full)
