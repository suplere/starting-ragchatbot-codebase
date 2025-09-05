"""
Live system test to verify RAG functionality works after bug fixes
"""

import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config import config
from rag_system import RAGSystem


def test_vector_store_data():
    """Test if vector store has data loaded"""
    print("Testing vector store data...")
    rag = RAGSystem(config)

    # Check course count
    analytics = rag.get_course_analytics()
    print(f"Found {analytics['total_courses']} courses")
    print(f"Course titles: {analytics['course_titles']}")

    if analytics["total_courses"] == 0:
        print("❌ No courses found in vector store!")
        return False
    else:
        print(f"✅ Vector store has {analytics['total_courses']} courses loaded")
        return True


def test_course_search_tool():
    """Test CourseSearchTool directly"""
    print("\nTesting CourseSearchTool directly...")
    rag = RAGSystem(config)

    try:
        # Test direct search
        result = rag.search_tool.execute("What is MCP?")
        print(f"Search result length: {len(result)} characters")
        print(f"First 200 characters: {result[:200]}")

        # Check sources
        print(f"Sources found: {len(rag.search_tool.last_sources)}")
        for i, source in enumerate(rag.search_tool.last_sources):
            print(f"  Source {i+1}: {source}")

        if "No relevant content found" in result or "error" in result.lower():
            print("❌ Search tool returned error or no results")
            return False
        else:
            print("✅ Search tool returned results successfully")
            return True
    except Exception as e:
        print(f"❌ Search tool failed with exception: {e}")
        return False


def test_rag_query():
    """Test full RAG query without API key"""
    print(
        "\nTesting RAG query (will fail without API key, but should get to AI call)..."
    )
    rag = RAGSystem(config)

    try:
        response, sources = rag.query("What is MCP?")
        print("❌ This should not succeed without proper API key")
        return False
    except Exception as e:
        error_str = str(e).lower()
        if "api" in error_str or "key" in error_str or "anthropic" in error_str:
            print("✅ Query reached AI generator (expected API key error)")
            print(f"Expected error: {e}")
            return True
        else:
            print(f"❌ Unexpected error before reaching AI: {e}")
            return False


def main():
    print("🧪 Testing RAG System After Bug Fixes")
    print("=" * 50)

    results = []

    # Test 1: Vector store data
    results.append(test_vector_store_data())

    # Test 2: Search tool
    results.append(test_course_search_tool())

    # Test 3: RAG query flow
    results.append(test_rag_query())

    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print(f"Tests passed: {sum(results)}/{len(results)}")

    if sum(results) == len(results):
        print("🎉 All tests passed! The 'query failed' issue should be resolved.")
    else:
        print("⚠️  Some tests failed. Additional fixes may be needed.")

    # Check if API key is set
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        print(
            "\n💡 To test full functionality, set ANTHROPIC_API_KEY in your .env file"
        )
    else:
        print("✅ API key is configured")


if __name__ == "__main__":
    main()
