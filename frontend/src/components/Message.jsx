import React, { useState } from 'react';
import './Message.css';

function Message({ message }) {
  const isUser = message.role === 'user';
  const [showSources, setShowSources] = useState(null); // Changed from boolean to index
  const hasSources = message.metadata?.sources && message.metadata.sources.length > 0;
  const isError = message.metadata?.isError;

  // Helper to clean up document names
  const formatDocName = (docId) => {
    if (!docId) return 'Unknown Document';
    return docId
      .replace('ncie_', '')
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Get relevance color based on similarity score
  const getRelevanceColor = (similarity) => {
    if (similarity >= 0.8) return '#10a37f'; // High - green
    if (similarity >= 0.6) return '#fbbf24'; // Medium - yellow
    return '#94a3b8'; // Low - gray
  };

  // Get relevance label
  const getRelevanceLabel = (similarity) => {
    if (similarity >= 0.8) return 'Highly Relevant';
    if (similarity >= 0.6) return 'Relevant';
    return 'Related';
  };

  // Show only top 3 sources
  const topSources = message.metadata?.sources?.slice(0, 3) || [];

  // Clean up answer text - remove source citations but keep markdown
  const cleanAnswer = (text) => {
    if (!text) return '';
    return text
      // Remove all variations of source citations
      .replace(/\(Source:[^)]*\)/gi, '')
      .replace(/\(Source:[^)]*$/gi, '')
      .replace(/Source:[^.]*\./gi, '')
      .replace(/\s*\(Source:.*$/gi, '')
      // Clean up extra whitespace
      .replace(/\s+/g, ' ')
      .replace(/\s+\./g, '.')
      .replace(/\s+,/g, ',')
      .trim();
  };

  // Convert markdown to HTML
  const renderMarkdown = (text) => {
    let html = cleanAnswer(text);
    
    // Aggressively normalize inline lists to separate lines
    // Split numbered lists: any pattern like "1. text 2. text" becomes separate lines
    html = html.replace(/(\d+)\.\s+/g, '\n$1. ');
    
    // Split bullet lists: any pattern like "* text * text" or "- text - text" 
    html = html.replace(/\s+\*\s+/g, '\n* ');
    html = html.replace(/\s+-\s+/g, '\n- ');
    
    const lines = html.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    let inOrderedList = false;
    let inUnorderedList = false;
    let processedLines = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Check if line is a numbered list item (starts with number followed by period)
      if (line.match(/^\d+\.\s+(.+)/)) {
        if (!inOrderedList) {
          if (inUnorderedList) {
            processedLines.push('</ul>');
            inUnorderedList = false;
          }
          processedLines.push('<ol>');
          inOrderedList = true;
        }
        const content = line.replace(/^\d+\.\s+/, '');
        processedLines.push(`<li>${content}</li>`);
      }
      // Check if line is a bullet point
      else if (line.match(/^[\*\-]\s+(.+)/)) {
        if (!inUnorderedList) {
          if (inOrderedList) {
            processedLines.push('</ol>');
            inOrderedList = false;
          }
          processedLines.push('<ul>');
          inUnorderedList = true;
        }
        const content = line.replace(/^[\*\-]\s+/, '');
        processedLines.push(`<li>${content}</li>`);
      } else {
        if (inOrderedList) {
          processedLines.push('</ol>');
          inOrderedList = false;
        }
        if (inUnorderedList) {
          processedLines.push('</ul>');
          inUnorderedList = false;
        }
        // Only add non-empty lines that aren't just colons
        if (line && line !== ':') {
          processedLines.push(line);
        }
      }
    }
    
    if (inOrderedList) {
      processedLines.push('</ol>');
    }
    if (inUnorderedList) {
      processedLines.push('</ul>');
    }
    
    html = processedLines.join('\n');
    
    // Bold: **text** or __text__
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
    
    // Italic: *text* or _text_ (but not in <li> tags already)
    html = html.replace(/(?<!<li>.*)\*(.+?)\*/g, '<em>$1</em>');
    html = html.replace(/(?<!<li>.*)_(.+?)_/g, '<em>$1</em>');
    
    // Code: `code`
    html = html.replace(/`(.+?)`/g, '<code>$1</code>');
    
    // Line breaks (but not inside lists)
    html = html.replace(/\n(?![<\/]?(ul|li|ol))/g, '<br/>');
    
    return html;
  };

  return (
    <div className={`message ${message.role} ${isError ? 'error' : ''}`}>
      <div className="message-avatar">
        {isUser ? (
          <div className="user-avatar">AU</div>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
          </svg>
        )}
      </div>
      <div className="message-content">
        <p 
          className="message-text"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }}
        />
        
        {hasSources && topSources.length > 0 && (
          <div className="sources-tags">
            {topSources.map((source, index) => {
              const relevanceColor = getRelevanceColor(source.similarity || 0);
              return (
                <button
                  key={index}
                  className="source-tag"
                  onClick={() => setShowSources(showSources === index ? null : index)}
                  title={`${formatDocName(source.doc_id)} - ${source.section}`}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                  </svg>
                  <span>{index + 1}</span>
                </button>
              );
            })}
          </div>
        )}

        {showSources !== false && showSources !== null && topSources[showSources] && (
          <div className="source-detail">
            {(() => {
              const source = topSources[showSources];
              const relevanceColor = getRelevanceColor(source.similarity || 0);
              return (
                <div className="source-detail-content" style={{ borderLeftColor: relevanceColor }}>
                  <div className="source-detail-header">
                    <span className="source-detail-title">
                      <strong>{formatDocName(source.doc_id)}</strong>
                    </span>
                    <button 
                      className="source-detail-close"
                      onClick={() => setShowSources(null)}
                    >
                      ×
                    </button>
                  </div>
                  <p className="source-detail-section">{source.section}</p>
                  <div className="source-detail-footer">
                    <span className="source-detail-relevance" style={{ color: relevanceColor }}>
                      {getRelevanceLabel(source.similarity)}
                    </span>
                    <span className="source-detail-match" style={{ color: relevanceColor }}>
                      {(source.similarity * 100).toFixed(0)}% match
                    </span>
                  </div>
                </div>
              );
            })()}
          </div>
        )}

        {message.metadata?.confidence && (
          <div className="message-meta">
            <span className="confidence-badge">
              Confidence: {message.metadata.confidence}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default Message;
