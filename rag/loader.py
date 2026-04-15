"""
Document Loader Module

Handles loading various document formats and splitting them into chunks
for semantic search and RAG applications.

Uses:
- PyPDFLoader: For PDF document loading
- RecursiveCharacterTextSplitter: For intelligent text splitting
- UnstructuredFileLoader: For other document formats
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class DocumentLoader:
    """
    Handles document loading and text splitting for RAG applications.
    
    Features:
    - Supports multiple file formats (PDF, TXT, MD, etc.)
    - Intelligent text splitting with configurable chunk size and overlap
    - Metadata preservation
    - Error handling and logging
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        documents_dir: Optional[str] = None
    ):
        """
        Initialize the DocumentLoader.
        
        Args:
            chunk_size (int): Size of text chunks in characters. Default: 1000
            chunk_overlap (int): Overlap between chunks in characters. Default: 200
            documents_dir (str): Path to documents directory. Default: ./documents
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Set documents directory
        self.documents_dir = Path(
            documents_dir or os.getenv("DOCUMENTS_DIR", "./documents")
        )
        self.documents_dir.mkdir(exist_ok=True)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",      # Double newline (paragraph)
                "\n",        # Single newline (line)
                ". ",        # Sentence
                " ",         # Word
                ""           # Character
            ],
            is_separator_regex=False
        )
        
        logger.info(f"DocumentLoader initialized with chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def load_document(self, file_name: str) -> List[Document]:
        """
        Load a single document and split into chunks.
        
        Args:
            file_name (str): Name of the file to load (in documents directory)
            
        Returns:
            List[Document]: List of Document objects with metadata
            
        Raises:
            FileNotFoundError: If file not found
            ValueError: If file format not supported
            Exception: If loading fails
        """
        file_path = self.documents_dir / file_name
        
        # Security check
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Verify file is within documents directory
        try:
            file_path.resolve().relative_to(self.documents_dir.resolve())
        except ValueError:
            raise ValueError(f"File path outside documents directory: {file_path}")
        
        logger.info(f"Loading document: {file_name}")
        
        try:
            file_ext = file_path.suffix.lower()
            
            if file_ext == ".pdf":
                documents = self._load_pdf(file_path)
            elif file_ext in [".txt", ".md"]:
                documents = self._load_text(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            # Split into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            # Add metadata
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "source": file_name,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "loaded_at": datetime.now().isoformat(),
                    "file_size": file_path.stat().st_size
                })
            
            logger.info(f"Successfully loaded {file_name}: {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error loading document {file_name}: {str(e)}")
            raise
    
    def load_all_documents(self) -> Dict[str, List[Document]]:
        """
        Load all documents from the documents directory.
        
        Returns:
            Dict[str, List[Document]]: Dictionary mapping file names to chunk lists
        """
        all_documents = {}
        
        for file_path in self.documents_dir.glob("*"):
            if file_path.is_file():
                file_ext = file_path.suffix.lower()
                
                # Only load supported formats
                if file_ext in [".pdf", ".txt", ".md"]:
                    try:
                        chunks = self.load_document(file_path.name)
                        all_documents[file_path.name] = chunks
                    except Exception as e:
                        logger.warning(f"Skipped {file_path.name}: {str(e)}")
                        continue
        
        logger.info(f"Loaded {len(all_documents)} documents total")
        return all_documents
    
    def _load_pdf(self, file_path: Path) -> List[Document]:
        """
        Load a PDF file using PyPDFLoader.
        
        Args:
            file_path (Path): Path to PDF file
            
        Returns:
            List[Document]: List of Document objects
        """
        loader = PyPDFLoader(str(file_path))
        documents = loader.load()
        
        # Add metadata
        for doc in documents:
            doc.metadata["file_type"] = "pdf"
        
        return documents
    
    def _load_text(self, file_path: Path) -> List[Document]:
        """
        Load a text file (TXT, MD) using TextLoader.
        
        Args:
            file_path (Path): Path to text file
            
        Returns:
            List[Document]: List of Document objects
        """
        try:
            loader = TextLoader(str(file_path), encoding="utf-8")
            documents = loader.load()
        except UnicodeDecodeError:
            # Try with different encoding
            loader = TextLoader(str(file_path), encoding="latin-1")
            documents = loader.load()
        
        # Add metadata
        for doc in documents:
            doc.metadata["file_type"] = "text"
        
        return documents
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough estimate: 1 token  4 characters).
        
        Args:
            text (str): Text to estimate tokens for
            
        Returns:
            int: Estimated token count
        """
        return len(text) // 4
    
    def get_document_info(self, file_name: str) -> Dict:
        """
        Get information about a document without loading it fully.
        
        Args:
            file_name (str): Name of the file
            
        Returns:
            Dict: Document information (size, type, created, modified)
        """
        file_path = self.documents_dir / file_name
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_name}")
        
        stat_info = file_path.stat()
        
        return {
            "name": file_name,
            "path": str(file_path),
            "size": stat_info.st_size,
            "type": file_path.suffix.lower(),
            "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "estimated_tokens": self.estimate_tokens(file_path.read_text(errors="ignore"))
        }
