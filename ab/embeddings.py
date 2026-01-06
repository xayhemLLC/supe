"""Embedding computation for semantic search on Cards.

This module provides embedding generation for card content, enabling:
- Semantic similarity search (find conceptually similar cards)
- Clustering of related memories
- Query expansion and understanding

Supports multiple embedding backends:
- Local: sentence-transformers (all-MiniLM-L6-v2, etc.)
- API: OpenAI, Anthropic, Cohere, etc.
- Simple: TF-IDF based (no dependencies)
"""

import hashlib
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import math


# =============================================================================
# Embedding Cache
# =============================================================================

class EmbeddingCache:
    """Simple file-based cache for embeddings."""

    def __init__(self, cache_dir: str = "~/.cache/supe/embeddings"):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, List[float]] = {}

    def _hash_text(self, text: str) -> str:
        """Create hash key for text."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def get(self, text: str) -> Optional[List[float]]:
        """Get cached embedding."""
        key = self._hash_text(text)

        # Check memory cache first
        if key in self._memory_cache:
            return self._memory_cache[key]

        # Check file cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    embedding = json.load(f)
                    self._memory_cache[key] = embedding
                    return embedding
            except:
                pass

        return None

    def set(self, text: str, embedding: List[float]) -> None:
        """Cache embedding."""
        key = self._hash_text(text)
        self._memory_cache[key] = embedding

        # Save to file
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(embedding, f)
        except:
            pass


# =============================================================================
# Embedding Providers
# =============================================================================

class EmbeddingProvider(ABC):
    """Abstract base for embedding providers."""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding dimension."""
        pass


class TFIDFEmbedder(EmbeddingProvider):
    """Simple TF-IDF based embedder (no external dependencies).

    Creates sparse-ish embeddings based on term frequency.
    Good for keyword overlap, less good for semantic similarity.
    """

    def __init__(self, dimension: int = 384, vocab_size: int = 10000):
        self._dimension = dimension
        self.vocab_size = vocab_size
        self.idf: Dict[str, float] = {}
        self.vocab: Dict[str, int] = {}
        self._doc_count = 0

    @property
    def dimension(self) -> int:
        return self._dimension

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        text = text.lower()
        tokens = re.findall(r'[a-z0-9]+', text)
        # Filter stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are'}
        return [t for t in tokens if t not in stopwords and len(t) > 2]

    def _hash_token(self, token: str) -> int:
        """Hash token to dimension index."""
        return int(hashlib.md5(token.encode()).hexdigest(), 16) % self._dimension

    def embed(self, text: str) -> List[float]:
        """Generate TF-IDF-like embedding."""
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self._dimension

        # Count term frequencies
        tf: Dict[str, int] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1

        # Build embedding vector
        embedding = [0.0] * self._dimension

        for token, count in tf.items():
            # TF component (log normalized)
            tf_score = 1 + math.log(count) if count > 0 else 0

            # IDF component (use default if not seen)
            idf_score = self.idf.get(token, 5.0)

            # Hash to dimension
            idx = self._hash_token(token)
            embedding[idx] += tf_score * idf_score

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]

        return embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""
        return [self.embed(t) for t in texts]

    def fit(self, texts: List[str]) -> None:
        """Fit IDF weights from corpus."""
        # Count document frequencies
        df: Dict[str, int] = {}
        for text in texts:
            tokens = set(self._tokenize(text))
            for token in tokens:
                df[token] = df.get(token, 0) + 1

        # Compute IDF
        n_docs = len(texts)
        self.idf = {
            token: math.log(n_docs / (1 + count))
            for token, count in df.items()
        }
        self._doc_count = n_docs


class SentenceTransformerEmbedder(EmbeddingProvider):
    """Embedding using sentence-transformers library.

    Requires: pip install sentence-transformers
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._dimension = None

    def _load_model(self):
        """Lazy load model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._dimension

    def embed(self, text: str) -> List[float]:
        """Generate embedding using sentence-transformers."""
        self._load_model()
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embed texts."""
        self._load_model()
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return [e.tolist() for e in embeddings]


class OpenAIEmbedder(EmbeddingProvider):
    """Embedding using OpenAI API.

    Requires: OPENAI_API_KEY environment variable
    """

    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self._client = None
        # Dimensions for common models
        self._dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }

    def _get_client(self):
        """Get OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI()
            except ImportError:
                raise ImportError("openai not installed. Run: pip install openai")
        return self._client

    @property
    def dimension(self) -> int:
        return self._dimensions.get(self.model, 1536)

    def embed(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        client = self._get_client()
        response = client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embed texts."""
        client = self._get_client()
        response = client.embeddings.create(
            input=texts,
            model=self.model
        )
        return [d.embedding for d in response.data]


# =============================================================================
# Card Embedder
# =============================================================================

@dataclass
class CardEmbedderConfig:
    """Configuration for card embedding."""
    provider: str = "tfidf"  # "tfidf", "sentence-transformers", "openai"
    model_name: str = "all-MiniLM-L6-v2"  # For sentence-transformers
    use_cache: bool = True
    cache_dir: str = "~/.cache/supe/embeddings"

    # Which buffers to include in embedding text
    include_buffers: List[str] = field(default_factory=lambda: [
        "title", "subtitle", "narrative", "facts", "concepts"
    ])

    # Weights for different buffers (title is most important)
    buffer_weights: Dict[str, float] = field(default_factory=lambda: {
        "title": 3.0,
        "subtitle": 2.0,
        "narrative": 1.0,
        "facts": 1.5,
        "concepts": 2.0,
    })


class CardEmbedder:
    """Generates embeddings for cards based on their buffer content."""

    def __init__(self, config: CardEmbedderConfig = None):
        self.config = config or CardEmbedderConfig()

        # Initialize provider
        if self.config.provider == "tfidf":
            self.provider = TFIDFEmbedder()
        elif self.config.provider == "sentence-transformers":
            self.provider = SentenceTransformerEmbedder(self.config.model_name)
        elif self.config.provider == "openai":
            self.provider = OpenAIEmbedder()
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")

        # Initialize cache
        self.cache = EmbeddingCache(self.config.cache_dir) if self.config.use_cache else None

    def _extract_text(self, buffers: Dict[str, Any]) -> str:
        """Extract weighted text from card buffers."""
        parts = []

        for buf_name in self.config.include_buffers:
            value = buffers.get(buf_name)
            if not value:
                continue

            # Convert to string
            if isinstance(value, list):
                text = " ".join(str(v) for v in value)
            else:
                text = str(value)

            # Apply weight by repeating
            weight = self.config.buffer_weights.get(buf_name, 1.0)
            repeat = max(1, int(weight))
            parts.extend([text] * repeat)

        return " ".join(parts)

    def embed_card(self, buffers: Dict[str, Any]) -> List[float]:
        """Generate embedding for a card's buffers.

        Args:
            buffers: Card buffer dict

        Returns:
            Embedding vector
        """
        text = self._extract_text(buffers)

        if not text.strip():
            return [0.0] * self.provider.dimension

        # Check cache
        if self.cache:
            cached = self.cache.get(text)
            if cached:
                return cached

        # Generate embedding
        embedding = self.provider.embed(text)

        # Cache result
        if self.cache:
            self.cache.set(text, embedding)

        return embedding

    def embed_cards_batch(self, cards_buffers: List[Dict[str, Any]]) -> List[List[float]]:
        """Batch embed multiple cards.

        Args:
            cards_buffers: List of card buffer dicts

        Returns:
            List of embedding vectors
        """
        texts = [self._extract_text(b) for b in cards_buffers]

        # Check cache for each
        results = []
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            if not text.strip():
                results.append([0.0] * self.provider.dimension)
            elif self.cache:
                cached = self.cache.get(text)
                if cached:
                    results.append(cached)
                else:
                    results.append(None)  # Placeholder
                    uncached_indices.append(i)
                    uncached_texts.append(text)
            else:
                results.append(None)
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Batch embed uncached
        if uncached_texts:
            embeddings = self.provider.embed_batch(uncached_texts)

            for idx, emb, text in zip(uncached_indices, embeddings, uncached_texts):
                results[idx] = emb
                if self.cache:
                    self.cache.set(text, emb)

        return results

    def embed_query(self, query: str) -> List[float]:
        """Embed a search query.

        Args:
            query: Search query text

        Returns:
            Query embedding vector
        """
        if not query.strip():
            return [0.0] * self.provider.dimension

        return self.provider.embed(query)

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self.provider.dimension


# =============================================================================
# Semantic Search
# =============================================================================

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def semantic_search(
    query_embedding: List[float],
    card_embeddings: Dict[int, List[float]],
    top_k: int = 10,
    threshold: float = 0.0
) -> List[Tuple[int, float]]:
    """Search cards by semantic similarity.

    Args:
        query_embedding: Query vector
        card_embeddings: Dict of card_id → embedding
        top_k: Max results
        threshold: Min similarity threshold

    Returns:
        List of (card_id, similarity) tuples, sorted by similarity desc
    """
    results = []

    for card_id, embedding in card_embeddings.items():
        sim = cosine_similarity(query_embedding, embedding)
        if sim >= threshold:
            results.append((card_id, sim))

    # Sort by similarity descending
    results.sort(key=lambda x: x[1], reverse=True)

    return results[:top_k]


# =============================================================================
# Convenience Functions
# =============================================================================

def create_embedder(
    provider: str = "tfidf",
    model_name: str = None,
    use_cache: bool = True
) -> CardEmbedder:
    """Create a card embedder with the specified provider.

    Args:
        provider: "tfidf", "sentence-transformers", or "openai"
        model_name: Model name for sentence-transformers
        use_cache: Enable caching

    Returns:
        Configured CardEmbedder
    """
    config = CardEmbedderConfig(
        provider=provider,
        use_cache=use_cache
    )

    if model_name:
        config.model_name = model_name

    return CardEmbedder(config)


def quick_embed(text: str, provider: str = "tfidf") -> List[float]:
    """Quick one-off embedding.

    Args:
        text: Text to embed
        provider: Embedding provider

    Returns:
        Embedding vector
    """
    if provider == "tfidf":
        embedder = TFIDFEmbedder()
    elif provider == "sentence-transformers":
        embedder = SentenceTransformerEmbedder()
    else:
        raise ValueError(f"Unknown provider: {provider}")

    return embedder.embed(text)
