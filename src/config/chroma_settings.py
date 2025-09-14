import os

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8338"))
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "vidyasetu_content")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Allow overriding the device used by SentenceTransformer: "cuda", "cpu", "mps", e.g., "cuda:0"
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "")

# For production, use HTTP client
CHROMA_CLIENT_TYPE = os.getenv("CHROMA_CLIENT_TYPE", "http")  # "http" or "persistent"