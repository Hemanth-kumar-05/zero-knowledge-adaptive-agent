"""
Generate HTML Viewer for ChromaDB Chunks
Creates an interactive HTML file to view chunks in a browser
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime
import html
from config import config


def generate_html_viewer():
    """Generate an HTML file to view ChromaDB chunks"""
    
    # Connect to ChromaDB
    project_root = Path(__file__).parent.parent
    chroma_path = str(project_root / "data" / "chroma_db")
    client = config.get_chroma_client(chroma_path)
    connection_info = config.get_chroma_connection_info(chroma_path)
    
    try:
        collection = client.get_collection("academic_docs")
    except Exception as e:
        print(f"❌ Error: Collection 'academic_docs' not found!")
        return
    
    # Get all chunks
    results = collection.get(include=["metadatas", "documents"])
    
    total_count = len(results['ids'])
    
    # Count statistics
    status_counts = {}
    for metadata in results['metadatas']:
        status = metadata.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Generate HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChromaDB Chunk Viewer</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .stats {{
            display: flex;
            justify-content: space-around;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}
        
        .stat-card {{
            text-align: center;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            min-width: 150px;
        }}
        
        .stat-card h3 {{
            color: #667eea;
            font-size: 2em;
            margin-bottom: 5px;
        }}
        
        .stat-card p {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        
        .controls {{
            padding: 20px 30px;
            background: white;
            border-bottom: 2px solid #e9ecef;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .controls input,
        .controls select {{
            padding: 10px 15px;
            border: 2px solid #e9ecef;
            border-radius: 6px;
            font-size: 1em;
            flex: 1;
            min-width: 200px;
        }}
        
        .controls input:focus,
        .controls select:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .chunks {{
            padding: 30px;
            max-height: 800px;
            overflow-y: auto;
        }}
        
        .chunk {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .chunk:hover {{
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .chunk.deprecated {{
            border-left-color: #dc3545;
            background: #fff5f5;
        }}
        
        .chunk-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .chunk-id {{
            font-family: 'Courier New', monospace;
            font-weight: bold;
            color: #667eea;
            font-size: 1.1em;
        }}
        
        .chunk-status {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .chunk-status.active {{
            background: #d4edda;
            color: #155724;
        }}
        
        .chunk-status.deprecated {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .chunk-meta {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
            font-size: 0.9em;
        }}
        
        .chunk-meta-item {{
            color: #6c757d;
        }}
        
        .chunk-meta-item strong {{
            color: #495057;
        }}
        
        .chunk-text {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #e9ecef;
            line-height: 1.6;
            color: #212529;
            max-height: 200px;
            overflow-y: auto;
        }}
        
        .deprecation-info {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 6px;
            padding: 12px;
            margin-top: 10px;
            font-size: 0.9em;
        }}
        
        .deprecation-info strong {{
            color: #856404;
        }}
        
        .no-results {{
            text-align: center;
            padding: 60px;
            color: #6c757d;
        }}
        
        .no-results h2 {{
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 ChromaDB Chunk Viewer</h1>
            <p>Interactive viewer for academic document chunks</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Connection: {connection_info["url"] if connection_info["mode"] == "http" else chroma_path}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>{total_count}</h3>
                <p>Total Chunks</p>
            </div>
            <div class="stat-card">
                <h3>{status_counts.get('active', 0)}</h3>
                <p>Active Chunks</p>
            </div>
            <div class="stat-card">
                <h3>{status_counts.get('deprecated', 0)}</h3>
                <p>Deprecated</p>
            </div>
        </div>
        
        <div class="controls">
            <input type="text" id="searchInput" placeholder="🔍 Search by text, doc ID, or section...">
            <select id="statusFilter">
                <option value="all">All Status</option>
                <option value="active">Active Only</option>
                <option value="deprecated">Deprecated Only</option>
            </select>
        </div>
        
        <div class="chunks" id="chunksContainer">
"""
    
    # Add each chunk
    for chunk_id, text, metadata in zip(
        results['ids'],
        results['documents'],
        results['metadatas']
    ):
        status = metadata.get('status', 'unknown')
        status_class = 'deprecated' if status == 'deprecated' else 'active'
        
        deprecated_info = ""
        if status == 'deprecated':
            deprecated_info = f"""
            <div class="deprecation-info">
                <strong>🚫 Deprecated Information:</strong><br>
                <strong>When:</strong> {metadata.get('deprecated_at', 'N/A')}<br>
                <strong>By:</strong> {metadata.get('deprecated_by', 'N/A')}<br>
                <strong>Reason:</strong> {metadata.get('deprecation_reason', 'N/A')}<br>
                <strong>Audit ID:</strong> {metadata.get('audit_id', 'N/A')}
            </div>
            """
        
        html_content += f"""
            <div class="chunk {status_class}" data-status="{status}" data-search="{html.escape(chunk_id + ' ' + text + ' ' + metadata.get('doc_id', '') + ' ' + metadata.get('section', '')).lower()}">
                <div class="chunk-header">
                    <span class="chunk-id">{html.escape(chunk_id)}</span>
                    <span class="chunk-status {status_class}">{html.escape(status.upper())}</span>
                </div>
                <div class="chunk-meta">
                    <div class="chunk-meta-item"><strong>Doc ID:</strong> {html.escape(metadata.get('doc_id', 'N/A'))}</div>
                    <div class="chunk-meta-item"><strong>Section:</strong> {html.escape(metadata.get('section', 'N/A'))}</div>
                    <div class="chunk-meta-item"><strong>Type:</strong> {html.escape(metadata.get('type', 'N/A'))}</div>
                    <div class="chunk-meta-item"><strong>Version:</strong> {metadata.get('version', 'N/A')}</div>
                    <div class="chunk-meta-item"><strong>Created:</strong> {metadata.get('created_at', 'N/A')[:10]}</div>
                </div>
                <div class="chunk-text">{html.escape(text)}</div>
                {deprecated_info}
            </div>
"""
    
    html_content += """
        </div>
    </div>
    
    <script>
        const searchInput = document.getElementById('searchInput');
        const statusFilter = document.getElementById('statusFilter');
        const chunks = document.querySelectorAll('.chunk');
        
        function filterChunks() {
            const searchTerm = searchInput.value.toLowerCase();
            const statusValue = statusFilter.value;
            
            let visibleCount = 0;
            
            chunks.forEach(chunk => {
                const searchData = chunk.getAttribute('data-search');
                const status = chunk.getAttribute('data-status');
                
                const matchesSearch = searchData.includes(searchTerm);
                const matchesStatus = statusValue === 'all' || status === statusValue;
                
                if (matchesSearch && matchesStatus) {
                    chunk.style.display = 'block';
                    visibleCount++;
                } else {
                    chunk.style.display = 'none';
                }
            });
            
            // Show "no results" message if needed
            const noResults = document.querySelector('.no-results');
            if (visibleCount === 0 && !noResults) {
                const container = document.getElementById('chunksContainer');
                container.innerHTML = '<div class="no-results"><h2>No chunks found</h2><p>Try adjusting your filters</p></div>';
            }
        }
        
        searchInput.addEventListener('input', filterChunks);
        statusFilter.addEventListener('change', filterChunks);
    </script>
</body>
</html>
"""
    
    # Save to file
    output_path = Path(__file__).parent / "chromadb_viewer.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML viewer generated: {output_path}")
    print(f"📊 Total chunks: {total_count}")
    print(f"   Active: {status_counts.get('active', 0)}")
    print(f"   Deprecated: {status_counts.get('deprecated', 0)}")
    print(f"\n🌐 Open in browser: file://{output_path.absolute()}")


if __name__ == "__main__":
    generate_html_viewer()
