"""
Debug script to understand ChromaDB result structure
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config import config
from vector_store import VectorStore


def debug_chromadb_structure():
    """Debug ChromaDB query result structure"""
    print("🔍 Debugging ChromaDB Query Structure")
    print("=" * 50)

    # Create vector store instance
    store = VectorStore(config.CHROMA_PATH, config.EMBEDDING_MODEL, config.MAX_RESULTS)

    # Try to query the course catalog directly
    print("Querying course catalog...")
    try:
        results = store.course_catalog.query(query_texts=["MCP"], n_results=1)

        print(f"Results type: {type(results)}")
        print(f"Results keys: {results.keys()}")

        print(f"\nDocuments: {results['documents']}")
        print(f"Documents type: {type(results['documents'])}")

        print(f"\nMetadatas: {results['metadatas']}")
        print(f"Metadatas type: {type(results['metadatas'])}")

        if results["metadatas"] and len(results["metadatas"]) > 0:
            print(f"\nFirst metadata: {results['metadatas'][0]}")
            print(f"First metadata type: {type(results['metadatas'][0])}")

            if (
                isinstance(results["metadatas"][0], list)
                and len(results["metadatas"][0]) > 0
            ):
                print(f"First metadata item: {results['metadatas'][0][0]}")
                print(f"First metadata item type: {type(results['metadatas'][0][0])}")

    except Exception as e:
        print(f"Error querying course catalog: {e}")
        import traceback

        traceback.print_exc()


def debug_get_method():
    """Debug the get method to understand data structure"""
    print("\n🔍 Debugging Course Catalog Get Method")
    print("=" * 50)

    store = VectorStore(config.CHROMA_PATH, config.EMBEDDING_MODEL, config.MAX_RESULTS)

    # Get all course titles first
    titles = store.get_existing_course_titles()
    print(f"Existing course titles: {titles}")

    if titles:
        # Try to get first course
        first_title = titles[0]
        print(f"\nGetting course: {first_title}")

        try:
            results = store.course_catalog.get(ids=[first_title])
            print(f"Get results: {results}")
            print(f"Get results type: {type(results)}")

            if "metadatas" in results:
                print(f"Metadatas: {results['metadatas']}")
                print(f"Metadatas type: {type(results['metadatas'])}")

                if results["metadatas"] and len(results["metadatas"]) > 0:
                    print(f"First metadata: {results['metadatas'][0]}")
                    print(f"First metadata type: {type(results['metadatas'][0])}")
        except Exception as e:
            print(f"Error getting course: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    debug_chromadb_structure()
    debug_get_method()
