"""
ChromaDB Chunk Viewer
Visualizes all chunks stored in ChromaDB with their metadata
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import chromadb
from datetime import datetime
import json


def view_all_chunks(limit=None, show_text_preview=True, filter_status=None):
    """
    Display all chunks from ChromaDB
    
    Args:
        limit: Maximum number of chunks to display (None = all)
        show_text_preview: Show first 200 chars of text
        filter_status: Filter by status ('active', 'deprecated', or None for all)
    """
    # Connect to ChromaDB
    project_root = Path(__file__).parent.parent
    chroma_path = str(project_root / "data" / "chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    
    print("=" * 80)
    print("CHROMADB CHUNK VIEWER")
    print("=" * 80)
    print(f"Database location: {chroma_path}\n")
    
    try:
        collection = client.get_collection("academic_docs")
    except Exception as e:
        print(f"❌ Error: Collection 'academic_docs' not found!")
        print(f"   {e}")
        return
    
    # Get total count
    total_count = collection.count()
    print(f"📊 Total chunks in collection: {total_count}\n")
    
    # Get chunks
    where_filter = {"status": filter_status} if filter_status else None
    results = collection.get(
        limit=limit,
        include=["metadatas", "documents"],
        where=where_filter
    )
    
    chunks_to_display = len(results['ids'])
    print(f"Displaying {chunks_to_display} chunks")
    if filter_status:
        print(f"Filter: status = {filter_status}")
    print("=" * 80)
    print()
    
    # Display each chunk
    for idx, (chunk_id, text, metadata) in enumerate(zip(
        results['ids'],
        results['documents'],
        results['metadatas']
    ), 1):
        status = metadata.get('status', 'unknown')
        status_emoji = "✅" if status == "active" else "🚫" if status == "deprecated" else "❓"
        
        print(f"{status_emoji} CHUNK #{idx}")
        print(f"   ID: {chunk_id}")
        print(f"   Status: {status}")
        print(f"   Doc ID: {metadata.get('doc_id', 'N/A')}")
        print(f"   Section: {metadata.get('section', 'N/A')}")
        print(f"   Type: {metadata.get('type', 'N/A')}")
        print(f"   Version: {metadata.get('version', 'N/A')}")
        print(f"   Created: {metadata.get('created_at', 'N/A')}")
        
        if status == "deprecated":
            print(f"   🔴 DEPRECATED INFO:")
            print(f"      Deprecated At: {metadata.get('deprecated_at', 'N/A')}")
            print(f"      Deprecated By: {metadata.get('deprecated_by', 'N/A')}")
            print(f"      Reason: {metadata.get('deprecation_reason', 'N/A')}")
            print(f"      Audit ID: {metadata.get('audit_id', 'N/A')}")
        
        if show_text_preview:
            preview = text[:200] + "..." if len(text) > 200 else text
            print(f"   Text Preview: {preview}")
        
        print()
    
    # Summary statistics
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    # Count by status
    all_results = collection.get(include=["metadatas"])
    status_counts = {}
    doc_id_counts = {}
    section_counts = {}
    
    for metadata in all_results['metadatas']:
        status = metadata.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        doc_id = metadata.get('doc_id', 'unknown')
        doc_id_counts[doc_id] = doc_id_counts.get(doc_id, 0) + 1
        
        section = metadata.get('section', 'unknown')
        section_counts[section] = section_counts.get(section, 0) + 1
    
    print(f"\n📊 By Status:")
    for status, count in sorted(status_counts.items()):
        percentage = (count / total_count) * 100
        print(f"   {status}: {count} ({percentage:.1f}%)")
    
    print(f"\n📚 By Document (Top 10):")
    for doc_id, count in sorted(doc_id_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {doc_id}: {count} chunks")
    
    print(f"\n📑 By Section (Top 10):")
    for section, count in sorted(section_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {section}: {count} chunks")
    
    print("\n" + "=" * 80)


def export_to_json(output_file="chromadb_export.json"):
    """Export all chunks to JSON file"""
    project_root = Path(__file__).parent.parent
    chroma_path = str(project_root / "data" / "chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    
    collection = client.get_collection("academic_docs")
    results = collection.get(include=["metadatas", "documents"])
    
    chunks = []
    for chunk_id, text, metadata in zip(
        results['ids'],
        results['documents'],
        results['metadatas']
    ):
        chunks.append({
            "id": chunk_id,
            "text": text,
            "metadata": metadata
        })
    
    output_path = Path(__file__).parent / output_file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total_chunks": len(chunks),
            "exported_at": datetime.now().isoformat(),
            "chunks": chunks
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exported {len(chunks)} chunks to {output_path}")


def search_chunks(query_text, top_k=5):
    """Search for chunks similar to query"""
    from embeddings.embedder import Embedder
    
    project_root = Path(__file__).parent.parent
    chroma_path = str(project_root / "data" / "chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    
    collection = client.get_collection("academic_docs")
    embedder = Embedder()
    
    print(f"\n🔍 Searching for: '{query_text}'\n")
    
    # Embed query
    query_embedding = embedder.embed_text(query_text)
    
    # Search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["metadatas", "documents", "distances"]
    )
    
    print(f"Found {len(results['ids'][0])} results:")
    print("=" * 80)
    
    for idx, (chunk_id, text, distance, metadata) in enumerate(zip(
        results['ids'][0],
        results['documents'][0],
        results['distances'][0],
        results['metadatas'][0]
    ), 1):
        similarity = 1 - distance
        status = metadata.get('status', 'unknown')
        status_emoji = "✅" if status == "active" else "🚫"
        
        print(f"\n{status_emoji} RESULT #{idx} (Similarity: {similarity:.3f})")
        print(f"   ID: {chunk_id}")
        print(f"   Status: {status}")
        print(f"   Doc: {metadata.get('doc_id', 'N/A')}")
        print(f"   Section: {metadata.get('section', 'N/A')}")
        print(f"   Text: {text[:150]}...")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ChromaDB Chunk Viewer")
    parser.add_argument("--limit", type=int, help="Limit number of chunks to display")
    parser.add_argument("--no-text", action="store_true", help="Don't show text preview")
    parser.add_argument("--status", choices=["active", "deprecated"], help="Filter by status")
    parser.add_argument("--export", action="store_true", help="Export to JSON file")
    parser.add_argument("--search", type=str, help="Search for similar chunks")
    parser.add_argument("--top-k", type=int, default=5, help="Number of search results")
    
    args = parser.parse_args()
    
    if args.export:
        export_to_json()
    elif args.search:
        search_chunks(args.search, args.top_k)
    else:
        view_all_chunks(
            limit=args.limit,
            show_text_preview=not args.no_text,
            filter_status=args.status
        )
