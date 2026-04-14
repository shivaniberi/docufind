#!/usr/bin/env python3
"""
Verification script to check Phase 2 setup
Run this to verify everything is configured correctly
"""

import os
import sys
from pathlib import Path
import json
import subprocess

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def check(condition, message):
    """Print check result"""
    if condition:
        print(f"  {Colors.GREEN}✅{Colors.RESET} {message}")
        return True
    else:
        print(f"  {Colors.RED}❌{Colors.RESET} {message}")
        return False

def section(title):
    """Print section header"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")

def main():
    print(f"\n{Colors.YELLOW}🚀 PHASE 2 VERIFICATION SCRIPT{Colors.RESET}\n")
    
    docufind_dir = Path("/Users/vallabhnaik/Desktop/docufind")
    all_passed = True
    
    # Check 1: Directory structure
    section("1. DIRECTORY STRUCTURE")
    
    required_dirs = {
        "mcp_server": "FastMCP server module",
        "documents": "Documents directory",
        "summaries": "Summaries directory",
        "venv": "Virtual environment"
    }
    
    for dir_name, desc in required_dirs.items():
        dir_path = docufind_dir / dir_name
        exists = dir_path.exists()
        all_passed &= check(exists, f"{desc} exists: {dir_name}/")
    
    # Check 2: Python files
    section("2. PYTHON FILES")
    
    required_files = {
        "mcp_server/document_server.py": "FastMCP server implementation",
        "run_server.py": "Server runner",
        "serve_test_ui.py": "Test UI server",
        "test_server.py": "Python test script",
        "example_usage.py": "Usage examples",
    }
    
    for file_path, desc in required_files.items():
        full_path = docufind_dir / file_path
        exists = full_path.exists() and full_path.stat().st_size > 0
        all_passed &= check(exists, f"{desc}: {file_path}")
    
    # Check 3: Documentation files
    section("3. DOCUMENTATION")
    
    doc_files = {
        "README.md": "Main documentation",
        "PHASE2_COMPLETE.md": "Phase 2 details",
        "QUICKSTART.md": "Quick start guide",
    }
    
    for file_path, desc in doc_files.items():
        full_path = docufind_dir / file_path
        exists = full_path.exists() and full_path.stat().st_size > 0
        all_passed &= check(exists, f"{desc}: {file_path}")
    
    # Check 4: Testing files
    section("4. TESTING FILES")
    
    test_files = {
        "test_ui.html": "Interactive web tester",
        ".env": "Environment configuration",
    }
    
    for file_path, desc in test_files.items():
        full_path = docufind_dir / file_path
        exists = full_path.exists()
        all_passed &= check(exists, f"{desc}: {file_path}")
    
    # Check 5: Sample documents
    section("5. SAMPLE DOCUMENTS")
    
    sample_docs = {
        "documents/ai_future.txt": "AI Future sample",
        "documents/ml_basics.txt": "ML Basics sample",
    }
    
    for file_path, desc in sample_docs.items():
        full_path = docufind_dir / file_path
        exists = full_path.exists() and full_path.stat().st_size > 0
        all_passed &= check(exists, f"{desc}: {file_path}")
    
    # Check 6: Environment variables
    section("6. ENVIRONMENT VARIABLES")
    
    env_file = docufind_dir / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
        
        has_api_key = "GOOGLE_API_KEY=" in content
        has_project_id = "PROJECT_ID=" in content
        
        all_passed &= check(has_api_key, "GOOGLE_API_KEY configured")
        all_passed &= check(has_project_id, "PROJECT_ID configured")
    else:
        check(False, ".env file exists")
        all_passed = False
    
    # Check 7: Python dependencies
    section("7. PYTHON DEPENDENCIES")
    
    required_packages = [
        ("fastmcp", "fastmcp"),
        ("pydantic-ai", "pydantic_ai"),
        ("langchain", "langchain"),
        ("google-genai", "google"),
        ("faiss-cpu", "faiss"),
        ("pypdf", "pypdf"),
        ("gradio", "gradio"),
        ("python-dotenv", "dotenv"),
    ]
    
    for display_name, import_name in required_packages:
        try:
            __import__(import_name)
            all_passed &= check(True, f"Package installed: {display_name}")
        except ImportError:
            all_passed &= check(False, f"Package installed: {display_name}")
    
    # Check 8: Code quality
    section("8. CODE QUALITY")
    
    server_file = docufind_dir / "mcp_server" / "document_server.py"
    if server_file.exists():
        with open(server_file, 'r') as f:
            content = f.read()
        
        has_decorators = "@mcp.tool()" in content
        has_error_handling = "try:" in content
        has_logging = "logging" in content
        
        all_passed &= check(has_decorators, "MCP decorators used")
        all_passed &= check(has_error_handling, "Error handling implemented")
        all_passed &= check(has_logging, "Logging implemented")
    
    # Summary
    section("SUMMARY")
    
    if all_passed:
        print(f"\n{Colors.GREEN}✅ ALL CHECKS PASSED!{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Your Phase 2 setup is complete and ready!{Colors.RESET}\n")
        print("🚀 Next steps:")
        print("  1. Open Terminal 1: cd /Users/vallabhnaik/Desktop/docufind")
        print("  2. Run: source venv/bin/activate && python run_server.py")
        print("  3. Open Terminal 2: cd /Users/vallabhnaik/Desktop/docufind")
        print("  4. Run: source venv/bin/activate && python serve_test_ui.py")
        print("  5. Visit: http://127.0.0.1:8001/test_ui.html")
        print("\n")
        return 0
    else:
        print(f"\n{Colors.RED}❌ SOME CHECKS FAILED{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Please fix the issues above and try again.{Colors.RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
