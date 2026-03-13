import os
from pathlib import Path
from typing import List, Dict
import re
from datetime import datetime


def load_markdown_files(data_dir: str) -> List[Dict[str, str]]:
    documents = []
    
    for filepath in Path(data_dir).glob('*.md'):
        content = filepath.read_text(encoding='utf-8')
        document = {
            'content': content,
            'filename': filepath.name,
            'filepath': str(filepath)
        }
        documents.append(document)
    
    return documents

def find_section_for_position(text: str, position: int) -> str:
    # Find all headers with their positions
    headers = []
    for match in re.finditer(r'^##\s+(.+)$', text, re.MULTILINE):
        headers.append((match.start(), match.group(1).strip()))
    
    # Find the most recent header before this position
    current_section = "Introduction"
    for header_pos, header_text in headers:
        if header_pos <= position:
            # Remove leading numbers like "1. " or "2. "
            current_section = re.sub(r'^\d+\.\s+', '', header_text)
        else:
            break
    
    return current_section


def create_chunks_with_metadata(
    documents: List[Dict[str, str]],
    chunk_size: int = 800,
    chunk_overlap: int = 100
) -> List[Dict[str, str]]:
    all_chunks = []
    
    for document in documents:
        content = document['content']
        filename = document['filename']
        
        # Create doc_id from filename (remove .md and replace _ with spaces, then snake_case)
        doc_id = "ncie_" + filename.replace('.md', '').replace('_', '_')
        
        # Track positions for section detection
        position = 0
        text_length = len(content)
        
        while position < text_length:
            chunk_text = content[position:position + chunk_size]
            
            # Find which section this chunk belongs to
            section = find_section_for_position(content, position)
            
            chunk_metadata = {
                'type': 'canonical_knowledge',
                'doc_id': doc_id,
                'section': section,
                'text': chunk_text.strip(),
                'confidence': 1.0,
                'active': True,
                # Phase 3: Policy Unlearning metadata
                'status': 'active',  # 'active' or 'deprecated'
                'version': 1,        # Policy version number
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            all_chunks.append(chunk_metadata)
            position += (chunk_size - chunk_overlap)
    
    return all_chunks


# ============================================================================
# TESTING SECTION
# ============================================================================

# if __name__ == "__main__":
#     print("🧪 Testing Document Ingestion...")
    
#     # Test 1: Load documents
#     print("\n1️⃣ Loading markdown files...")
#     data_path = "data/raw"
#     documents = load_markdown_files(data_path)
#     print(f"   ✓ Loaded {len(documents)} documents")
    
#     if documents:
#         print(f"   ✓ First document: {documents[0]['filename']}")
#         print(f"   ✓ Content length: {len(documents[0]['content'])} characters")
    
#     # Test 2: Chunk documents
#     print("\n2️⃣ Creating chunks...")
#     chunks = create_chunks_with_metadata(documents, chunk_size=800, chunk_overlap=100)
#     print(f"   ✓ Created {len(chunks)} chunks from all documents")
    
#     if chunks:
#         print(f"\n   Example chunk:")
#         print(f"   Type: {chunks[0]['type']}")
#         print(f"   Doc ID: {chunks[0]['doc_id']}")
#         print(f"   Section: {chunks[0]['section']}")
#         print(f"   Text preview: {chunks[0]['text'][:150]}...")
#         print(f"   Confidence: {chunks[0]['confidence']}")
#         print(f"   Active: {chunks[0]['active']}")
    
#     # Test 3: Analyze chunk distribution
#     print("\n3️⃣ Analyzing chunks per document...")
#     from collections import Counter
#     chunk_distribution = Counter(chunk['doc_id'] for chunk in chunks)
#     for doc_id, count in chunk_distribution.most_common():
#         print(f"   {doc_id}: {count} chunks")
    
#     # Test 4: Check for reasonable chunk sizes
#     print("\n4️⃣ Checking chunk sizes...")
#     chunk_sizes = [len(chunk['text']) for chunk in chunks]
#     print(f"   Min size: {min(chunk_sizes)} chars")
#     print(f"   Max size: {max(chunk_sizes)} chars")
#     print(f"   Average: {sum(chunk_sizes)/len(chunk_sizes):.0f} chars")
    
#     # Test 5: Section distribution
#     print("\n5️⃣ Analyzing section distribution...")
#     section_distribution = Counter(chunk['section'] for chunk in chunks)
#     print(f"   Found {len(section_distribution)} unique sections")
#     print(f"   Top 5 sections:")
#     for section, count in section_distribution.most_common(5):
#         print(f"      - {section}: {count} chunks")
    
#     print("\n✅ Ingestion tests complete!")
#     print("\n💡 Chunk structure now matches canonical knowledge format:")
#     print("   - type: canonical_knowledge")
#     print("   - doc_id: derived from filename")
#     print("   - section: extracted from markdown headers")
#     print("   - text: chunk content")
#     print("   - confidence: 1.0 (authoritative)")
#     print("   - active: True (available for retrieval)")