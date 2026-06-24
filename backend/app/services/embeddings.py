import logging
import threading

from django.conf import settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_model = None
_ready = False


class EmbeddingService:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.batch_size = 32

    def warmup(self):
        global _model, _ready
        with _lock:
            if _ready:
                return
            logger.info("Loading embedding model: %s", self.model_name)
            _model = SentenceTransformer(self.model_name)
            _ready = True
            logger.info("Embedding model loaded.")

    @property
    def is_ready(self):
        return _ready

    def _get_model(self):
        if not _ready:
            self.warmup()
        return _model

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._get_model()
        embeddings = model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def encode_query(self, query: str) -> list[float]:
        model = self._get_model()
        prefixed = f"Represent this sentence for searching relevant passages: {query}"
        embedding = model.encode(
            [prefixed],
            batch_size=1,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return embedding[0].tolist()


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
