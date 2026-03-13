"""
Reset ChromaDB - Delete all collections and recreate
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import chromadb
import shutil

def reset_chromadb():
    """Delete and recreate ChromaDB"""
    project_root = Path(__file__).parent.parent
    chroma_path = project_root / "data" / "chroma_db"
    
    print(f"🗑️  Resetting ChromaDB at: {chroma_path}")
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path=str(chroma_path))
        
        # Delete all collections
        collections = client.list_collections()
        print(f"Found {len(collections)} collections")
        
        for collection in collections:
            print(f"  - Deleting collection: {collection.name}")
            client.delete_collection(collection.name)
        
        print("✅ ChromaDB reset complete!")
        print(f"   Collections deleted: {len(collections)}")
        
    except Exception as e:
        print(f"❌ Error resetting ChromaDB: {e}")
        return False
    
    return True

if __name__ == "__main__":
    reset_chromadb()
