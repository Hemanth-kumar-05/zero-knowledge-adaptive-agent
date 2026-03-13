"""
Test: Can semantic search find ALL chunks about "CA 40%" without keywords?

This validates whether we can use pure semantic search for policy unlearning.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import chromadb
from embeddings.embedder import Embedder
import json


def test_semantic_vs_keyword():
    """
    Compare semantic search vs keyword search for CA 40% policy
    """
    
    print("=" * 80)
    print("🧪 TEST: Semantic Search vs Keyword Search for 'CA 40%' Policy")
    print("=" * 80)
    
    # Connect to ChromaDB (use absolute path)
    project_root = Path(__file__).parent.parent
    chroma_path = str(project_root / "data" / "chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection("academic_docs")
    embedder = Embedder()
    
    # GROUND TRUTH: Keyword search for "40%"
    print("\n" + "="*80)
    print("STEP 1: GROUND TRUTH (Keyword Search)")
    print("="*80)
    
    all_data = collection.get()
    keyword_chunks = []
    
    for doc_id, text, metadata in zip(all_data['ids'], all_data['documents'], all_data['metadatas']):
        if "40%" in text or "40 %" in text or "forty percent" in text.lower():
            keyword_chunks.append({
                'id': doc_id,
                'text': text,
                'doc_id': metadata.get('doc_id', 'unknown'),
                'section': metadata.get('section', 'unknown')
            })
    
    print(f"✅ Keyword search found: {len(keyword_chunks)} chunks")
    print(f"   IDs: {[c['id'] for c in keyword_chunks]}")
    
    # SEMANTIC SEARCH: Different query formulations
    print("\n" + "="*80)
    print("STEP 2: SEMANTIC SEARCH (Various Queries)")
    print("="*80)
    
    semantic_queries = [
        "What is the weightage contribution of Continuous Assessment to total course evaluation?",
        "Continuous Assessment percentage in total marks",
        "CA weightage distribution in grading",
        "How much does internal assessment contribute to final grade?",
        "Continuous Assessment and End Semester Examination ratio"
    ]
    
    all_semantic_chunks = {}
    
    for query_idx, query in enumerate(semantic_queries, 1):
        print(f"\n🔍 Query {query_idx}: '{query}'")
        
        query_embedding = embedder.embed_text(query)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=20  # Get top 20 to ensure we don't miss any
            # No 'where' filter - we want ALL chunks for this test
        )
        
        found_in_this_query = []
        for chunk_id, text, distance, metadata in zip(
            results['ids'][0],
            results['documents'][0],
            results['distances'][0],
            results['metadatas'][0]
        ):
            similarity = 1 - distance
            
            # Check if this chunk is in our ground truth
            is_ground_truth = chunk_id in [c['id'] for c in keyword_chunks]
            
            if chunk_id not in all_semantic_chunks:
                all_semantic_chunks[chunk_id] = {
                    'id': chunk_id,
                    'text': text[:200] + "..." if len(text) > 200 else text,
                    'full_text': text,  # Store full text for detailed display
                    'doc_id': metadata.get('doc_id', 'unknown'),
                    'section': metadata.get('section', 'unknown'),
                    'max_similarity': similarity,
                    'matched_queries': [],
                    'is_ground_truth': is_ground_truth
                }
            
            all_semantic_chunks[chunk_id]['matched_queries'].append({
                'query': query,
                'similarity': similarity
            })
            all_semantic_chunks[chunk_id]['max_similarity'] = max(
                all_semantic_chunks[chunk_id]['max_similarity'],
                similarity
            )
            
            if is_ground_truth:
                found_in_this_query.append(chunk_id)
        
        print(f"   Total results: {len(results['ids'][0])}")
        print(f"   Ground truth chunks found: {len(found_in_this_query)}")
        if found_in_this_query:
            print(f"   IDs: {found_in_this_query}")
    
    # ANALYSIS
    print("\n" + "="*80)
    print("STEP 3: COMPARISON ANALYSIS")
    print("="*80)
    
    # Which ground truth chunks were found by semantic search?
    ground_truth_ids = set([c['id'] for c in keyword_chunks])
    semantic_ids = set(all_semantic_chunks.keys())
    found_by_semantic = ground_truth_ids.intersection(semantic_ids)
    missed_by_semantic = ground_truth_ids - semantic_ids
    
    print(f"\n📊 Ground Truth (Keyword): {len(ground_truth_ids)} chunks")
    print(f"📊 Semantic Search Found: {len(semantic_ids)} chunks total")
    
    if len(ground_truth_ids) == 0:
        print("\n❌ ERROR: No chunks found in database!")
        print("   Collection is empty. You need to run:")
        print("   python embeddings/build_index.py")
        return {
            'ground_truth_count': 0,
            'semantic_found_count': 0,
            'recall': 0,
            'false_positives': 0,
            'missed_chunks': [],
            'found_chunks': []
        }
    
    print(f"✅ Correctly Found: {len(found_by_semantic)} chunks ({len(found_by_semantic)/len(ground_truth_ids)*100:.1f}%)")
    print(f"❌ Missed: {len(missed_by_semantic)} chunks ({len(missed_by_semantic)/len(ground_truth_ids)*100:.1f}%)")
    
    if missed_by_semantic:
        print(f"\n⚠️ MISSED CHUNKS:")
        for chunk_id in missed_by_semantic:
            chunk = next(c for c in keyword_chunks if c['id'] == chunk_id)
            print(f"\n   ID: {chunk_id}")
            print(f"   Doc: {chunk['doc_id']}")
            print(f"   Section: {chunk['section']}")
            print(f"   Text: {chunk['text'][:150]}...")
    
    # Show correctly found chunks with their similarities and FULL TEXT
    print(f"\n✅ SUCCESSFULLY FOUND BY SEMANTIC SEARCH (TRUE MATCHES):")
    for chunk_id in sorted(found_by_semantic):
        chunk = all_semantic_chunks[chunk_id]
        print(f"\n{'='*80}")
        print(f"   ID: {chunk_id}")
        print(f"   Doc: {chunk['doc_id']}")
        print(f"   Section: {chunk.get('section', 'unknown')}")
        print(f"   Max Similarity: {chunk['max_similarity']:.3f}")
        print(f"   Matched {len(chunk['matched_queries'])} queries")
        print(f"\n   📝 FULL TEXT:")
        print(f"   {chunk['full_text'][:500]}...")
        print(f"{'='*80}")
    
    # False positives - SHOW ALL WITH DETAILS
    false_positives = semantic_ids - ground_truth_ids
    print(f"\n⚠️ FALSE POSITIVES (found by semantic but don't contain '40%'): {len(false_positives)}")
    print("These are semantically related to CA/grading but don't mention the specific 40% value")
    
    for idx, chunk_id in enumerate(sorted(false_positives), 1):
        chunk = all_semantic_chunks[chunk_id]
        print(f"\n{'='*80}")
        print(f"FP #{idx}: {chunk_id}")
        print(f"   Doc: {chunk['doc_id']}")
        print(f"   Section: {chunk.get('section', 'unknown')}")
        print(f"   Similarity: {chunk['max_similarity']:.3f}")
        has_40 = "40%" in chunk['full_text'] or "40 %" in chunk['full_text']
        print(f"   Contains '40%': {has_40}")
        print(f"\n   📝 TEXT:")
        print(f"   {chunk['full_text'][:400]}...")
        print(f"{'='*80}")
    
    # CONCLUSION
    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    
    if len(found_by_semantic) == len(ground_truth_ids):
        print("✅ SUCCESS: Semantic search found ALL chunks with CA 40% policy!")
        print("   Pure semantic search is viable for policy unlearning.")
    elif len(found_by_semantic) >= len(ground_truth_ids) * 0.9:
        print("⚠️ PARTIAL SUCCESS: Semantic search found 90%+ of chunks.")
        print(f"   Missing {len(missed_by_semantic)} chunks - may need hybrid approach.")
    else:
        print("❌ INSUFFICIENT: Semantic search missed too many chunks.")
        print("   Need to combine with keyword search or improve queries.")
    
    # Save results
    output = {
        'ground_truth_count': len(ground_truth_ids),
        'semantic_found_count': len(found_by_semantic),
        'recall': len(found_by_semantic) / len(ground_truth_ids) if ground_truth_ids else 0,
        'false_positives': len(false_positives),
        'missed_chunks': list(missed_by_semantic),
        'found_chunks': list(found_by_semantic)
    }
    
    output_file = Path(__file__).parent / 'semantic_search_test_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    return output


if __name__ == "__main__":
    results = test_semantic_vs_keyword()
    
    if results and results['ground_truth_count'] > 0:
        print("\n" + "="*80)
        print(f"🎯 FINAL SCORE: {results['recall']*100:.1f}% Recall")
        print("="*80)
    else:
        print("\n⚠️ Test could not complete - database is empty")
