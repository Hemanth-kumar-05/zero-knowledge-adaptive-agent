"""
Reset ChromaDB - Delete all collections and recreate.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import config


def reset_chromadb():
    """Delete and recreate ChromaDB."""
    project_root = Path(__file__).parent.parent
    chroma_path = project_root / "data" / "chroma_db"
    connection_info = config.get_chroma_connection_info(str(chroma_path))

    if connection_info["mode"] == "http":
        print(f"Resetting ChromaDB over HTTP at: {connection_info['url']}")
    else:
        print(f"Resetting ChromaDB at: {chroma_path}")

    try:
        client = config.get_chroma_client(str(chroma_path))

        collections = client.list_collections()
        print(f"Found {len(collections)} collections")

        for collection in collections:
            collection_name = collection.name if hasattr(collection, "name") else collection
            print(f"  - Deleting collection: {collection_name}")
            client.delete_collection(collection_name)

        print("ChromaDB reset complete")
        print(f"  Collections deleted: {len(collections)}")

    except Exception as e:
        print(f"Error resetting ChromaDB: {e}")
        return False

    return True


if __name__ == "__main__":
    reset_chromadb()
