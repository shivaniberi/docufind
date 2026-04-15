#!/usr/bin/env python3
"""
Quick test script to diagnose the FastMCP server
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

print(" FastMCP Server Diagnostic Test\n")

# Test 1: Root endpoint
print("=" * 60)
print("TEST 1: Root endpoint")
print("=" * 60)
try:
    response = requests.get(f"{BASE_URL}/", timeout=5)
    print(f" Server is running (Status: {response.status_code})")
    print(f"Response headers: {dict(response.headers)}")
except Exception as e:
    print(f" Cannot connect to server: {e}")
    sys.exit(1)

# Test 2: Docs endpoint
print("\n" + "=" * 60)
print("TEST 2: API Docs endpoint")
print("=" * 60)
try:
    response = requests.get(f"{BASE_URL}/docs", timeout=5)
    print(f" Docs available (Status: {response.status_code})")
except Exception as e:
    print(f" Docs not available: {e}")

# Test 3: List tools
print("\n" + "=" * 60)
print("TEST 3: List documents tool")
print("=" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/tools/list_documents/call",
        json={},
        timeout=5,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f" Error: {e}")
    try:
        print(f"Response text: {response.text}")
    except:
        pass

# Test 4: Read document
print("\n" + "=" * 60)
print("TEST 4: Read document tool")
print("=" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/tools/read_document/call",
        json={"file_name": "ai_future.txt"},
        timeout=5,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"File: {result.get('file_name')}")
    print(f"Size: {result.get('file_size')} bytes")
    print(f"Type: {result.get('file_type')}")
    if result.get('content'):
        print(f"Content preview: {result.get('content')[:200]}...")
except Exception as e:
    print(f" Error: {e}")

print("\n" + "=" * 60)
print(" All tests completed!")
print("=" * 60)
