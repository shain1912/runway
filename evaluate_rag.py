"""
Offline retrieval-quality harness for the Runway RAG index.

Runs a small golden question set through the SAME retrieval path as production
(rag_core.retrieve -> hybrid dense+BM25 with optional rerank) and reports Hit@K
and MRR@K based on whether a retrieved chunk's source path matches the expected
document. Requires only Qdrant + the local models (no LLM/API), so it is cheap to
run repeatedly to measure the effect of chunking/retrieval changes.

Usage:
    python evaluate_rag.py            # K=5, hybrid
    python evaluate_rag.py --k 8
    python evaluate_rag.py --rerank   # add cross-encoder reranking
"""
import argparse

from qdrant_client import QdrantClient

import rag_core as core

# Golden set: each question -> substrings expected in the source path of a
# relevant chunk. A retrieval counts as a hit if ANY expected substring is found.
GOLDEN = [
    {"q": "GPU 할당은 어떻게 설정하나요?", "expect": ["gpu-guide"]},
    {"q": "kubeconfig 다운로드하고 적용하는 방법", "expect": ["kubeconfig"]},
    {"q": "워크스페이스에서 새 프로젝트를 생성하려면?", "expect": ["project-create"]},
    {"q": "모델 배포 엔드포인트는 어떻게 설정하나요?", "expect": ["model-serving", "endpoint", "model-deployment"]},
    {"q": "스토리지 볼륨 생성과 관리", "expect": ["storage", "volume"]},
    {"q": "사용자 인증과 액세스 키 발급", "expect": ["authentication", "access-keys"]},
    {"q": "커스텀 앱을 만드는 방법", "expect": ["custom-app"]},
    {"q": "역할과 권한 체계 설명", "expect": ["roles-and-permissions", "roles"]},
    {"q": "추론 요청을 보내는 방법", "expect": ["inference"]},
    {"q": "프로젝트 모니터링 보는 법", "expect": ["monitoring"]},
]


def is_hit(source, expects):
    s = (source or "").lower().replace("\\", "/")
    return any(e.lower() in s for e in expects)


def evaluate(top_k, use_reranker):
    print(f"Loading models (dense + {'rerank ' if use_reranker else ''}sparse)...")
    core.load_dense_model()

    try:
        client = QdrantClient(host=core.QDRANT_HOST, port=core.QDRANT_PORT, timeout=10)
        names = [c.name for c in client.get_collections().collections]
    except Exception as e:
        print(f"[Error] Could not connect to Qdrant: {e}")
        return
    if core.COLLECTION_NAME not in names:
        print(f"[Error] Collection '{core.COLLECTION_NAME}' not found. Run: python ingest_qdrant.py --full")
        return

    hits, rr_sum = 0, 0.0
    print(f"\n{'='*64}\nEvaluating {len(GOLDEN)} questions (K={top_k}, rerank={'on' if use_reranker else 'off'})\n{'='*64}")
    for item in GOLDEN:
        results, meta = core.retrieve(client, item["q"], top_k=top_k, use_reranker=use_reranker)
        rank = None
        for i, r in enumerate(results, 1):
            if is_hit(r["source"], item["expect"]):
                rank = i
                break
        if rank:
            hits += 1
            rr_sum += 1.0 / rank
            status = f"rank {rank}"
        else:
            status = "MISS"
        print(f"  [{status:>7}] (mode={meta['mode']}, conf={meta['confidence']:.3f}) {item['q']}")

    n = len(GOLDEN)
    print(f"\n{'-'*64}")
    print(f"Hit@{top_k}: {hits}/{n} = {hits / n:.1%}")
    print(f"MRR@{top_k}: {rr_sum / n:.3f}")
    print(f"{'-'*64}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality of the Runway RAG index.")
    parser.add_argument("--k", type=int, default=5, help="Top-K chunks to retrieve (default 5).")
    parser.add_argument("--rerank", action="store_true", help="Apply cross-encoder reranking.")
    args = parser.parse_args()
    evaluate(args.k, args.rerank)
