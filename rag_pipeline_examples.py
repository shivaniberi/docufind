#!/usr/bin/env python3
"""
RAG Pipeline Examples - Phase 3B Integration

Demonstrates the complete Retrieval-Augmented Generation pipeline:
1. Load and index documents
2. Ask questions with context retrieval
3. Generate answers with Gemini
4. Display sources and confidence scores

Run with: python rag_pipeline_examples.py
Run with auto-execution: python rag_pipeline_examples.py --auto
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
def load_env():
    """Load .env file."""
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val


def example_1_initialize_pipeline():
    """Example 1: Initialize the RAG Pipeline."""
    print("\n" + "="*70)
    print(" Example 1: Initialize RAG Pipeline")
    print("="*70)
    
    from rag import RAGPipeline, RAGConfig
    
    # Create config with custom settings
    config = RAGConfig(
        k=4,  # Retrieve top 4 documents
        llm_model="gemini-2.0-flash",  # Use fastest Gemini model
        temperature=0.7,
        include_sources=True
    )
    
    # Initialize pipeline
    pipeline = RAGPipeline(config=config)
    
    print("\n Pipeline initialized successfully!")
    
    # Get status
    status = pipeline.get_status()
    print("\n Pipeline Status:")
    for key, value in status["config"].items():
        print(f"   {key}: {value}")
    
    return pipeline


def example_2_index_documents(pipeline):
    """Example 2: Load and index documents."""
    print("\n" + "="*70)
    print(" Example 2: Load and Index Documents")
    print("="*70)
    
    # Create sample documents if they don't exist
    docs_dir = Path("documents")
    docs_dir.mkdir(exist_ok=True)
    
    # Create sample documents
    sample_docs = {
        "ai_basics.txt": """
        Artificial Intelligence (AI) is the simulation of human intelligence processes 
        by computer systems. These processes include learning, reasoning, and self-correction.
        
        Key aspects of AI:
        1. Machine Learning: Systems that learn from data
        2. Deep Learning: Neural networks with multiple layers
        3. Natural Language Processing: Understanding human language
        4. Computer Vision: Understanding images and video
        
        AI has applications in healthcare, finance, transportation, and many other fields.
        """,
        "machine_learning.txt": """
        Machine Learning is a subset of AI that focuses on systems learning from data
        without being explicitly programmed.
        
        Types of Machine Learning:
        1. Supervised Learning: Learning with labeled data
        2. Unsupervised Learning: Finding patterns in unlabeled data
        3. Reinforcement Learning: Learning through interaction and rewards
        
        Common algorithms include:
        - Decision Trees
        - Random Forests
        - Neural Networks
        - Support Vector Machines
        - K-Means Clustering
        """
    }
    
    print("\n Creating sample documents...")
    for filename, content in sample_docs.items():
        filepath = docs_dir / filename
        if not filepath.exists():
            filepath.write_text(content)
            print(f"   Created: {filename}")
        else:
            print(f"    Already exists: {filename}")
    
    # Index documents
    print("\n Indexing documents...")
    result = pipeline.index_documents(collection_name="demo")
    
    print("\n Indexing complete!")
    print(f"   Documents loaded: {result['documents_loaded']}")
    print(f"   Chunks created: {result['chunks_created']}")


def example_3_search_documents(pipeline):
    """Example 3: Search documents without generating."""
    print("\n" + "="*70)
    print(" Example 3: Search Documents")
    print("="*70)
    
    query = "What is machine learning?"
    print(f"\n Searching for: '{query}'")
    
    results = pipeline.search(query, collection_name="demo", k=3)
    
    print(f"\n Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"     File: {result['file']}")
        print(f"     Score: {result['score']}")
        print(f"     Content: {result['content']}")


def example_4_answer_question(pipeline):
    """Example 4: Answer a question with context."""
    print("\n" + "="*70)
    print(" Example 4: Answer Question with RAG")
    print("="*70)
    
    question = "What are the main types of machine learning?"
    print(f"\n Question: {question}")
    
    result = pipeline.answer_question(
        question,
        collection_name="demo",
        use_multi_query=False
    )
    
    if result["status"] == "success":
        print("\n Answer generated successfully!")
        print(f"\n Answer:\n{result['answer']}")
        print(f"\n Documents retrieved: {result['documents_retrieved']}")
        
        print("\n Sources:")
        for i, source in enumerate(result['sources'], 1):
            print(f"  {i}. {source['file']} (Score: {source['score']})")
    else:
        print(f"\n Error: {result.get('error', 'Unknown error')}")


def example_5_complex_question(pipeline):
    """Example 5: Complex question with multi-query expansion."""
    print("\n" + "="*70)
    print(" Example 5: Complex Question with Multi-Query")
    print("="*70)
    
    question = "How does machine learning differ from artificial intelligence?"
    print(f"\n Question: {question}")
    
    result = pipeline.answer_question(
        question,
        collection_name="demo",
        use_multi_query=True  # Use multi-query expansion
    )
    
    if result["status"] == "success":
        print("\n Answer generated with multi-query expansion!")
        print(f"\n Answer:\n{result['answer']}")
        print(f"\n Documents retrieved: {result['documents_retrieved']}")
    else:
        print(f"\n Error: {result.get('error', 'Unknown error')}")


def interactive_mode(pipeline):
    """Interactive Q&A mode."""
    print("\n" + "="*70)
    print(" Interactive Q&A Mode")
    print("="*70)
    print("\nEnter questions to ask the RAG system. Type 'quit' to exit.")
    
    while True:
        question = input("\n Your question: ").strip()
        
        if question.lower() in ["quit", "exit", "q"]:
            print("\n Goodbye!")
            break
        
        if not question:
            print("Please enter a question.")
            continue
        
        result = pipeline.answer_question(
            question,
            collection_name="demo",
            use_multi_query=True
        )
        
        if result["status"] == "success":
            print(f"\n Answer:\n{result['answer']}")
            print(f"\n Documents retrieved: {result['documents_retrieved']}")
        else:
            print(f"\n Error: {result.get('error', 'Unknown error')}")


def main():
    """Run examples."""
    # Load environment
    load_env()
    
    # Check for auto mode
    auto_mode = "--auto" in sys.argv
    
    try:
        # Example 1: Initialize
        pipeline = example_1_initialize_pipeline()
        
        # Example 2: Index documents
        example_2_index_documents(pipeline)
        
        if auto_mode:
            # Run all examples automatically
            print("\n" + "="*70)
            print(" Running auto examples...")
            print("="*70)
            
            example_3_search_documents(pipeline)
            example_4_answer_question(pipeline)
            example_5_complex_question(pipeline)
            
            print("\n" + "="*70)
            print(" All examples completed!")
            print("="*70)
        else:
            # Interactive menu
            print("\n" + "="*70)
            print(" Available Examples")
            print("="*70)
            print("\n1. Search documents")
            print("2. Simple question answering")
            print("3. Complex question with multi-query")
            print("4. Interactive Q&A mode")
            print("5. Exit")
            
            while True:
                choice = input("\n Choose an example (1-5): ").strip()
                
                if choice == "1":
                    example_3_search_documents(pipeline)
                elif choice == "2":
                    example_4_answer_question(pipeline)
                elif choice == "3":
                    example_5_complex_question(pipeline)
                elif choice == "4":
                    interactive_mode(pipeline)
                elif choice == "5":
                    print("\n Goodbye!")
                    break
                else:
                    print("Invalid choice. Please try again.")
    
    except Exception as e:
        print(f"\n Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
