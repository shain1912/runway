import os
import re
import json
import urllib.request
import urllib.parse
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configs
DOCS_DIR = "docs_markdown"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "runway_docs"
EMBEDDING_MODEL_NAME = "jhgan/ko-sbert-multitask"  # Fully public, high-quality Korean SentenceBERT

def parse_markdown_to_chunks(file_path):
    """
    Parse markdown files and split them semantically based on heading structures (#, ##, ###).
    Maintains hierarchical context as metadata for each chunk.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    chunks = []
    current_h1 = ""
    current_h2 = ""
    current_h3 = ""
    current_h4 = ""
    
    accumulated_lines = []
    
    # Extract file clean name
    rel_path = os.path.relpath(file_path, DOCS_DIR)
    clean_source_name = rel_path.replace("\\", " > ").replace("/", " > ").replace("index.md", "").strip(" > ")

    def flush_chunk():
        nonlocal accumulated_lines
        content = "".join(accumulated_lines).strip()
        if content:
            # Build context prefix to inject semantic meaning directly into the vector
            header_context = " > ".join([h for h in [current_h1, current_h2, current_h3, current_h4] if h])
            full_text = f"Source: {clean_source_name}\nContext: {header_context}\n\nContent:\n{content}"
            
            chunks.append({
                "text": full_text,
                "metadata": {
                    "source": rel_path,
                    "h1": current_h1,
                    "h2": current_h2,
                    "h3": current_h3,
                    "h4": current_h4,
                    "clean_source": clean_source_name
                }
            })
        accumulated_lines = []

    for line in lines:
        # Match headings
        h1_match = re.match(r"^#\s+(.+)$", line)
        h2_match = re.match(r"^##\s+(.+)$", line)
        h3_match = re.match(r"^###\s+(.+)$", line)
        h4_match = re.match(r"^####\s+(.+)$", line)

        if h1_match:
            flush_chunk()
            current_h1 = h1_match.group(1).strip().replace("\n", "")
            current_h2, current_h3, current_h4 = "", "", ""
        elif h2_match:
            flush_chunk()
            current_h2 = h2_match.group(1).strip().replace("\n", "")
            current_h3, current_h4 = "", ""
        elif h3_match:
            flush_chunk()
            current_h3 = h3_match.group(1).strip().replace("\n", "")
            current_h4 = ""
        elif h4_match:
            flush_chunk()
            current_h4 = h4_match.group(1).strip().replace("\n", "")
        else:
            accumulated_lines.append(line)
            
    # Flush remaining text
    flush_chunk()
    return chunks

def ingest_documents():
    print(f"Loading local embedding model '{EMBEDDING_MODEL_NAME}'...")
    # Will download once and run completely locally on CPU/GPU
    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    # Get vector size dynamically
    dummy_vector = embedder.encode("test string")
    vector_size = dummy_vector.shape[0]
    print(f"Embedding model loaded successfully. Vector size: {vector_size}")

    # Initialize Qdrant Client
    print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if COLLECTION_NAME in collection_names:
            print(f"Collection '{COLLECTION_NAME}' already exists. Recreating it...")
            client.delete_collection(COLLECTION_NAME)
            
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=vector_size, 
                distance=models.Distance.COSINE
            )
        )
        print(f"Collection '{COLLECTION_NAME}' initialized successfully.")
    except Exception as e:
        print(f"\n[Error] Could not connect to Qdrant: {e}")
        print("Please make sure Qdrant is running locally (e.g. docker run -p 6333:6333 qdrant/qdrant) or deployed on Runway.")
        return

    # Process all markdown files
    all_chunks = []
    print(f"\nProcessing markdown documents inside '{DOCS_DIR}'...")
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    chunks = parse_markdown_to_chunks(file_path)
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"  Error parsing {file_path}: {e}")

    print(f"Total semantic chunks generated: {len(all_chunks)}")
    
    if not all_chunks:
        print("No chunks generated. Ingestion aborted.")
        return

    # Batch embedding generation
    print("\nGenerating embeddings for all chunks...")
    texts = [chunk["text"] for chunk in all_chunks]
    embeddings = embedder.encode(texts, show_progress_bar=True, batch_size=32)

    # Upserting to Qdrant
    print(f"Uploading {len(all_chunks)} points to Qdrant collection '{COLLECTION_NAME}'...")
    points = []
    for i, (chunk, vector) in enumerate(zip(all_chunks, embeddings)):
        points.append(
            models.PointStruct(
                id=i,
                vector=vector.tolist(),
                payload={
                    "page_content": chunk["text"],
                    "metadata": chunk["metadata"]
                }
            )
        )

    # Batch upload points
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(
            collection_name=COLLECTION_NAME,
            wait=True,
            points=batch
        )
        print(f"  Uploaded points {i} to {i + len(batch)}")

    print("\n[Success] Ingestion pipeline completed! All documentation is indexed in Qdrant Vector DB.")

if __name__ == "__main__":
    ingest_documents()
