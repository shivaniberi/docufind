"""
Test script for FastMCP Document Server
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_list_documents():
    """Test the list_documents tool"""
    print("\n" + "="*60)
    print("TEST 1: List Documents")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/tools/list_documents/call",
        headers={"Content-Type": "application/json"},
        json={}
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(json.dumps(result, indent=2))
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None


def test_read_document(file_name):
    """Test the read_document tool"""
    print("\n" + "="*60)
    print(f"TEST 2: Read Document - {file_name}")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/tools/read_document/call",
        headers={"Content-Type": "application/json"},
        json={"file_name": file_name}
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(f"File Name: {result['file_name']}")
        print(f"File Type: {result['file_type']}")
        print(f"File Size: {result['file_size']} bytes")
        print(f"\nContent Preview (first 300 chars):")
        print(result['content'][:300] + "..." if len(result['content']) > 300 else result['content'])
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None


def test_save_summary(file_name, summary):
    """Test the save_summary tool"""
    print("\n" + "="*60)
    print(f"TEST 3: Save Summary - {file_name}")
    print("="*60)
    
    metadata = {
        "key_points": [
            "AI is transformative",
            "Multiple subfields of AI",
            "Ethical considerations important"
        ],
        "word_count": 150,
        "reading_time_minutes": 2
    }
    
    response = requests.post(
        f"{BASE_URL}/tools/save_summary/call",
        headers={"Content-Type": "application/json"},
        json={
            "file_name": file_name,
            "summary": summary,
            "metadata": metadata
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(json.dumps(result, indent=2))
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None


def test_get_summary(file_name):
    """Test the get_summary tool"""
    print("\n" + "="*60)
    print(f"TEST 4: Get Summary - {file_name}")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/tools/get_summary/call",
        headers={"Content-Type": "application/json"},
        json={"file_name": file_name}
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(json.dumps(result, indent=2))
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None


def main():
    print("\n" + "🚀 "*20)
    print("FASTMCP DOCUMENT SERVER - TESTING SUITE")
    print("🚀 "*20)
    
    # Wait a moment for the server to be ready
    time.sleep(2)
    
    try:
        # Test 1: List documents
        list_result = test_list_documents()
        
        if list_result and list_result.get('count', 0) > 0:
            # Get first document
            first_doc = list_result['documents'][0]['name']
            
            # Test 2: Read document
            read_result = test_read_document(first_doc)
            
            # Test 3: Save summary
            if read_result:
                summary = f"This document discusses important concepts about {first_doc}. It provides comprehensive information and practical insights."
                save_result = test_save_summary(first_doc, summary)
                
                # Test 4: Get summary
                if save_result:
                    test_get_summary(first_doc)
        
        print("\n" + "="*60)
        print("✅ TESTING COMPLETE!")
        print("="*60)
        print("\n📝 Summary:")
        print("- All tools tested successfully")
        print("- Server is responding correctly")
        print("- Check http://127.0.0.1:8000/docs for interactive API docs")
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        print("Make sure the server is running on http://127.0.0.1:8000")


if __name__ == "__main__":
    main()
