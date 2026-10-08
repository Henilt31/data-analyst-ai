from typing import List
from sentence_transformers import SentenceTransformer
from app.config import settings

class LocalEmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            try:
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"SentenceTransformer offline/error: {e}. Using deterministic local embeddings.")
                self._model = "fallback"
        return self._model

    def encode(self, texts: List[str]) -> List[List[float]]:
        if self.model == "fallback":
            import hashlib
            results = []
            for t in texts:
                vec = []
                for i in range(384):
                    h = hashlib.sha256(f"{t}_{i}".encode("utf-8")).digest()
                    val = (int.from_bytes(h[:4], "little") / 0xFFFFFFFF) * 2 - 1
                    vec.append(round(val, 6))
                results.append(vec)
            return results

        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

embedding_service = LocalEmbeddingService()
