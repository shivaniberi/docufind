"""
Vector Embedder Module

Handles creation and management of vector embeddings using
Google Generative AI embeddings and FAISS vector store.

Uses:
- GoogleGenerativeAIEmbeddings: For generating embeddings
- FAISS: For efficient similarity search
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Manages vector embeddings and similarity search using FAISS and Google Generative AI.
    
    Features:
    - Create embeddings from documents
    - Store and retrieve embeddings efficiently using FAISS
    - Persist embeddings to disk
    - Similarity search with score filtering
    - Update and manage vector collections
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        embeddings_dir: Optional[str] = None,
        model_name: str = "models/gemini-embedding-001"
    ):
        """
        Initialize the VectorStore.
        
        Args:
            api_key (str): Google API key. If None, uses GOOGLE_API_KEY env var
            embeddings_dir (str): Directory to store embeddings. Default: ./embeddings
            model_name (str): Embedding model name. Default: models/gemini-embedding-001
        """
        # Get API key
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment or parameters")
        
        # Set embeddings directory
        self.embeddings_dir = Path(embeddings_dir or "./embeddings")
        self.embeddings_dir.mkdir(exist_ok=True)
        
        self.model_name = model_name
        
        # Initialize embeddings model
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=self.api_key
        )
        
        # Vector store (will be loaded or created)
        self.faiss_store: Optional[FAISS] = None
        self.metadata_store: Dict[str, Dict] = {}  # Store additional metadata
        
        logger.info(f"VectorStore initialized with model={model_name}")
    
    def add_documents(
        self,
        documents: List[Document],
        collection_name: str = "default"
    ) -> bool:
        """
        Add documents to the vector store.
        
        Args:
            documents (List[Document]): List of documents to add
            collection_name (str): Name of the collection for organization
            
        Returns:
            bool: True if successful
        """
        if not documents:
            logger.warning("No documents to add")
            return False
        
        try:
            logger.info(f"Adding {len(documents)} documents to collection '{collection_name}'")
            
            # Create or update FAISS store
            if self.faiss_store is None:
                logger.info("Creating new FAISS store")
                self.faiss_store = FAISS.from_documents(
                    documents,
                    self.embeddings
                )
            else:
                logger.info("Adding to existing FAISS store")
                self.faiss_store.add_documents(documents)
            
            # Store metadata
            for doc in documents:
                doc_id = doc.metadata.get("source", "unknown")
                if doc_id not in self.metadata_store:
                    self.metadata_store[doc_id] = {
                        "collection": collection_name,
                        "added_at": doc.metadata.get("loaded_at", ""),
                        "chunk_count": 0,
                        "total_size": 0
                    }
                
                self.metadata_store[doc_id]["chunk_count"] += 1
                self.metadata_store[doc_id]["total_size"] += len(doc.page_content)
            
            logger.info(f"Successfully added documents to collection '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        score_threshold: float = 0.0
    ) -> List[Tuple[Document, float]]:
        """
        Search for similar documents using semantic similarity.
        
        Args:
            query (str): Search query
            k (int): Number of results to return. Default: 4
            score_threshold (float): Minimum similarity score (0-1). Default: 0.0
            
        Returns:
            List[Tuple[Document, float]]: List of (document, score) tuples
        """
        if self.faiss_store is None:
            logger.warning("Vector store is empty, no search results")
            return []
        
        try:
            logger.info(f"Searching for: '{query}' (k={k})")
            
            # Perform similarity search with scores
            results = self.faiss_store.similarity_search_with_score(query, k=k)
            
            # Filter by score threshold
            filtered_results = [
                (doc, score) for doc, score in results 
                if score >= score_threshold
            ]
            
            logger.info(f"Found {len(filtered_results)} relevant documents")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error during similarity search: {str(e)}")
            raise
    
    def save_to_disk(self, collection_name: str = "default") -> bool:
        """
        Save the vector store to disk for persistence.
        
        Args:
            collection_name (str): Name for the saved collection
            
        Returns:
            bool: True if successful
        """
        if self.faiss_store is None:
            logger.warning("No vector store to save")
            return False
        
        try:
            save_path = self.embeddings_dir / collection_name
            logger.info(f"Saving vector store to {save_path}")
            
            # Save FAISS index
            self.faiss_store.save_local(str(save_path))
            
            # Save metadata
            metadata_path = self.embeddings_dir / f"{collection_name}_metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(self.metadata_store, f, indent=2)
            
            logger.info(f"Successfully saved to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}")
            raise
    
    def load_from_disk(self, collection_name: str = "default") -> bool:
        """
        Load a saved vector store from disk.
        
        Args:
            collection_name (str): Name of the collection to load
            
        Returns:
            bool: True if successful, False if collection doesn't exist
        """
        try:
            load_path = self.embeddings_dir / collection_name
            
            if not load_path.exists():
                logger.warning(f"Collection '{collection_name}' not found")
                return False
            
            logger.info(f"Loading vector store from {load_path}")
            
            # Load FAISS index
            self.faiss_store = FAISS.load_local(
                str(load_path),
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            # Load metadata
            metadata_path = self.embeddings_dir / f"{collection_name}_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    self.metadata_store = json.load(f)
            
            logger.info(f"Successfully loaded collection '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            raise
    
    def clear_store(self) -> bool:
        """
        Clear the current vector store.
        
        Returns:
            bool: True if successful
        """
        try:
            self.faiss_store = None
            self.metadata_store = {}
            logger.info("Vector store cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")
            raise
    
    def get_store_info(self) -> Dict:
        """
        Get information about the current vector store.
        
        Returns:
            Dict: Store information
        """
        if self.faiss_store is None:
            return {
                "status": "empty",
                "documents": 0,
                "collections": 0
            }
        
        return {
            "status": "ready",
            "model": self.model_name,
            "documents": len(self.metadata_store),
            "collections": list(set(
                v.get("collection", "unknown") 
                for v in self.metadata_store.values()
            )),
            "metadata_store": self.metadata_store
        }
    
    def list_collections(self) -> List[str]:
        """
        List all saved collections on disk.
        
        Returns:
            List[str]: List of collection names
        """
        collections = []
        
        for item in self.embeddings_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                collections.append(item.name)
        
        return collections
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a saved collection from disk.
        
        Args:
            collection_name (str): Name of collection to delete
            
        Returns:
            bool: True if successful
        """
        try:
            import shutil
            
            collection_path = self.embeddings_dir / collection_name
            metadata_path = self.embeddings_dir / f"{collection_name}_metadata.json"
            
            if collection_path.exists():
                shutil.rmtree(collection_path)
            
            if metadata_path.exists():
                metadata_path.unlink()
            
            logger.info(f"Deleted collection '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            raise
