import chromadb
from sentence_transformers import SentenceTransformer
from typing import Dict, Optional
import torch
from ..config.chroma_settings import (
    CHROMA_HOST, CHROMA_PORT,
    EMBEDDING_MODEL, CHROMA_CLIENT_TYPE, EMBEDDING_DEVICE
)

class VectorService:
    def __init__(self, ):
        # Use HTTP client to connect to separate ChromaDB container
        if CHROMA_CLIENT_TYPE == "http":
            self.client = chromadb.HttpClient(
                host=CHROMA_HOST,
                port=CHROMA_PORT
            )
        else:
            # Fallback for development
            self.client = chromadb.PersistentClient(path="./chroma_db")
        
        # Select device for embeddings (prefer GPU if available, or override via env)
        if EMBEDDING_DEVICE:
            device = EMBEDDING_DEVICE
        else:
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL, device=device)
        print(f"SentenceTransformer device: {device}")

    def create_collection(self, collection_id: str):
        """Create a new collection in the vector store"""
        try:
            self.client.create_collection(name=collection_id)
        except Exception as e:
            print(f"Error creating collection {collection_id}: {e}")

    def create_collection_by_course_id(self, course_id: int):
        """Create a collection for a specific course"""
        collection_id = "course_" + str(course_id)
        self.create_collection(collection_id)
    
    def add_content_by_course_id(self, course_id: int, content_id: str, text: str, metadata: Dict):
        """Add content to vector store"""
        embedding = self.embedding_model.encode([text])
        self.client.get_or_create_collection("course_" + str(course_id)).add(
            documents=[text],
            embeddings=embedding.tolist(),
            metadatas=[metadata],
            ids=[content_id]
        )
    
    def search_by_course_id(self, course_id: int, query: str, n_results: int = 5, filter_metadata: Optional[Dict] = None):
        """Search for similar content"""
        query_embedding = self.embedding_model.encode([query])
        results = self.client.get_or_create_collection("course_" + str(course_id)).query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results,
            where=filter_metadata
        )
        return results

    
    def delete_content_by_course_id(self, course_id: int, content_id: str):
        """Delete content from vector store"""
        try:
            self.client.get_or_create_collection("course_" + str(course_id)).delete(ids=[content_id])
        except Exception as e:
            print(f"Error deleting content {content_id}: {e}")
    
    def update_content_by_course_id(self, course_id: int, content_id: str, text: str, metadata: Dict):
        """Update existing content"""
        self.delete_content_by_course_id(course_id, content_id)
        self.add_content_by_course_id(course_id, content_id, text, metadata)

    def get_collection_by_course_id(self, course_id: int):
        """Get collection by course ID"""
        return self.client.get_or_create_collection("course_" + str(course_id))
