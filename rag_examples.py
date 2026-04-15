"""
RAG System Example and Test Script

Demonstrates the usage of the LangChain RAG components:
- DocumentLoader: Load and split documents
- VectorStore: Create and manage embeddings
- Retriever: Perform semantic search and retrieve context
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

from rag.loader import DocumentLoader
from rag.embedder import VectorStore
from rag.retriever import Retriever


def example_1_load_documents():
    """Example 1: Load and split documents"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Load and Split Documents")
    print("="*80)
    
    try:
        # Initialize loader
        loader = DocumentLoader(chunk_size=1000, chunk_overlap=200)
        
        # List available documents
        print("\nAvailable documents:")
        for file_path in Path("./documents").glob("*"):
            if file_path.is_file():
                info = loader.get_document_info(file_path.name)
                print(f"  - {info['name']}: {info['size']} bytes, {info['estimated_tokens']} tokens")
        
        # Load a specific document
        test_file = "ml_basics.txt"
        if Path("./documents").joinpath(test_file).exists():
            print(f"\nLoading document: {test_file}")
            chunks = loader.load_document(test_file)
            print(f" Loaded {len(chunks)} chunks")
            print(f"  First chunk preview: {chunks[0].page_content[:100]}...")
        
    except Exception as e:
        logger.error(f"Error in example 1: {str(e)}")


def example_2_create_embeddings():
    """Example 2: Create and store embeddings"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Create and Store Embeddings")
    print("="*80)
    
    try:
        # Initialize components
        loader = DocumentLoader()
        vector_store = VectorStore()
        
        # Load all documents
        print("\nLoading all documents...")
        all_docs = loader.load_all_documents()
        
        if not all_docs:
            print(" No documents found to embed")
            return
        
        total_chunks = sum(len(chunks) for chunks in all_docs.values())
        print(f" Loaded {len(all_docs)} files with {total_chunks} total chunks")
        
        # Add documents to vector store
        print("\nCreating embeddings with Google Generative AI...")
        for file_name, chunks in all_docs.items():
            print(f"  Processing {file_name} ({len(chunks)} chunks)...")
            vector_store.add_documents(chunks, collection_name="documents")
        
        # Display store info
        info = vector_store.get_store_info()
        print(f"\n Vector store created:")
        print(f"  - Model: {info['model']}")
        print(f"  - Documents: {info['documents']}")
        print(f"  - Collections: {info['collections']}")
        
        # Save to disk
        print("\nSaving embeddings to disk...")
        vector_store.save_to_disk("documents")
        print(" Embeddings saved to ./embeddings/documents/")
        
    except Exception as e:
        logger.error(f"Error in example 2: {str(e)}")


def example_3_semantic_search():
    """Example 3: Perform semantic search"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Semantic Search and Retrieval")
    print("="*80)
    
    try:
        # Initialize components
        vector_store = VectorStore()
        
        # Load existing embeddings
        print("\nLoading embeddings from disk...")
        if not vector_store.load_from_disk("documents"):
            print(" No saved embeddings found. Run example 2 first.")
            return
        
        print(" Embeddings loaded")
        
        # Initialize retriever
        retriever = Retriever(vector_store, k=4, score_threshold=0.0)
        
        # Example queries
        queries = [
            "What is machine learning?",
            "neural networks",
            "deep learning algorithms"
        ]
        
        for query in queries:
            print(f"\n{''*80}")
            print(f"Query: '{query}'")
            print(''*80)
            
            # Retrieve documents
            results = retriever.retrieve(query, k=3)
            
            if not results:
                print("No results found")
                continue
            
            # Print results
            for i, (doc, score) in enumerate(results, 1):
                source = doc.metadata.get("source", "unknown")
                chunk_idx = doc.metadata.get("chunk_index", "?")
                print(f"\nResult {i}: {source} (chunk {chunk_idx}) - Score: {score:.4f}")
                print(f"Preview: {doc.page_content[:200]}...")
            
            # Get summary
            summary = retriever.get_summary(results)
            print(f"\nSummary:")
            print(f"  - Total documents: {summary['total_documents']}")
            print(f"  - Unique sources: {summary['unique_sources']}")
            print(f"  - Average score: {summary['average_score']}")
        
    except Exception as e:
        logger.error(f"Error in example 3: {str(e)}")


def example_4_multi_query_rag():
    """Example 4: Multi-query RAG for better retrieval"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Multi-Query RAG")
    print("="*80)
    
    try:
        # Initialize components
        vector_store = VectorStore()
        
        # Load embeddings
        if not vector_store.load_from_disk("documents"):
            print(" No saved embeddings found. Run example 2 first.")
            return
        
        retriever = Retriever(vector_store, k=3)
        
        # Original query with multiple reformulations
        original_query = "How do neural networks learn?"
        reformulated_queries = [
            "How do neural networks learn?",
            "What is the learning process in neural networks?",
            "Neural network training mechanisms",
            "How are neural network weights updated?"
        ]
        
        print(f"\nOriginal query: '{original_query}'")
        print(f"\nReformulated queries:")
        for i, q in enumerate(reformulated_queries, 1):
            print(f"  {i}. '{q}'")
        
        # Multi-query retrieval
        print("\nPerforming multi-query retrieval...")
        results = retriever.retrieve_multi_query(reformulated_queries, k=3, deduplicate=True)
        
        print(f"\n Retrieved {len(results)} unique documents")
        
        for i, (doc, score, queries_matched) in enumerate(results, 1):
            source = doc.metadata.get("source", "unknown")
            print(f"\nResult {i}: {source} - Score: {score:.4f}")
            print(f"  Matched {len(queries_matched)} reformulations")
            print(f"  Preview: {doc.page_content[:150]}...")
        
        # Assemble context
        context = retriever.assemble_context_with_queries(results, max_tokens=2000)
        print(f"\n Assembled context ({len(context)} characters)")
        print(f"Context preview:\n{context[:300]}...\n")
        
    except Exception as e:
        logger.error(f"Error in example 4: {str(e)}")


def example_5_rag_pipeline():
    """Example 5: Complete RAG pipeline"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Complete RAG Pipeline")
    print("="*80)
    
    try:
        # Initialize components
        loader = DocumentLoader()
        vector_store = VectorStore()
        
        # Load embeddings (or create if not exists)
        if not vector_store.load_from_disk("documents"):
            print("Creating embeddings...")
            all_docs = loader.load_all_documents()
            for file_name, chunks in all_docs.items():
                vector_store.add_documents(chunks, collection_name="documents")
            vector_store.save_to_disk("documents")
        
        retriever = Retriever(vector_store, k=4)
        
        # RAG query
        user_query = "Explain the concept of gradient descent"
        
        print(f"\nUser Query: '{user_query}'")
        print("\n" + ""*80)
        print("RAG Pipeline Execution")
        print(""*80)
        
        # Step 1: Retrieve relevant documents
        print("\n1  Retrieving relevant documents...")
        retrieved = retriever.retrieve(user_query, k=4)
        print(f"    Retrieved {len(retrieved)} documents")
        
        # Step 2: Assemble context
        print("\n2  Assembling context for LLM...")
        context = retriever.assemble_context(retrieved, max_tokens=2000)
        print(f"    Context assembled ({len(context)} characters)")
        
        # Step 3: Format prompt for LLM
        print("\n3  Formatting LLM prompt...")
        llm_prompt = f"""Use the following context to answer the question. If the context doesn't contain relevant information, say so.

Context:
{context}

Question: {user_query}

Answer:"""
        
        print(f"    Prompt ready for LLM")
        print(f"\nPrompt Preview (first 300 chars):")
        print(f"{llm_prompt[:300]}...")
        
        # Step 4: Summary
        print("\n4  Retrieval Summary")
        summary = retriever.get_summary(retrieved)
        print(f"   - Documents retrieved: {summary['total_documents']}")
        print(f"   - Average relevance: {summary['average_score']:.4f}")
        print(f"   - Source documents: {summary['unique_sources']}")
        
    except Exception as e:
        logger.error(f"Error in example 5: {str(e)}")


def main():
    """Run all examples"""
    print("\n" + ""+ "="*78 + "")
    print("" + " "*20 + "LangChain RAG System - Examples & Tests" + " "*20 + "")
    print("" + "="*78 + "")
    
    examples = [
        ("1", "Load and Split Documents", example_1_load_documents),
        ("2", "Create and Store Embeddings", example_2_create_embeddings),
        ("3", "Semantic Search", example_3_semantic_search),
        ("4", "Multi-Query RAG", example_4_multi_query_rag),
        ("5", "Complete RAG Pipeline", example_5_rag_pipeline),
    ]
    
    print("\nAvailable Examples:")
    for num, name, _ in examples:
        print(f"  {num}. {name}")
    print("  6. Run All Examples")
    print("  0. Exit")
    
    while True:
        choice = input("\nSelect example (0-6): ").strip()
        
        if choice == "0":
            print("\nGoodbye! ")
            break
        
        elif choice == "6":
            for num, name, func in examples:
                print(f"\n\n{'#'*80}")
                print(f"# Running Example {num}: {name}")
                print(f"{'#'*80}")
                func()
            break
        
        else:
            for num, name, func in examples:
                if choice == num:
                    func()
                    break
            else:
                print("Invalid choice")


if __name__ == "__main__":
    # If run with --auto flag, run all examples
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        example_1_load_documents()
        example_2_create_embeddings()
        example_3_semantic_search()
        example_4_multi_query_rag()
        example_5_rag_pipeline()
    else:
        main()
