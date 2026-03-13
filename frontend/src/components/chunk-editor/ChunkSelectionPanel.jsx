import { useState } from 'react';
import './ChunkSelectionPanel.css';

/**
 * ChunkSelectionPanel - Display and select chunks for deprecation
 * 
 * Shows:
 * - High confidence chunks (green) - pre-selected
 * - Possibly related chunks (yellow) - user can select
 * - Grouped by document for easy navigation
 */
const ChunkSelectionPanel = ({ 
    highConfidenceChunks = [], 
    possiblyRelatedChunks = [],
    selectedChunkIds = [],
    onSelectionChange,
    loading = false
}) => {
    const [expandedDocs, setExpandedDocs] = useState({});
    const [showPossiblyRelated, setShowPossiblyRelated] = useState(false);

    // Group chunks by document
    const groupByDocument = (chunks) => {
        const grouped = {};
        chunks.forEach(chunk => {
            const docId = chunk.doc_id || 'unknown';
            if (!grouped[docId]) {
                grouped[docId] = [];
            }
            grouped[docId].push(chunk);
        });
        return grouped;
    };

    const highConfGrouped = groupByDocument(highConfidenceChunks);
    const possiblyRelatedGrouped = groupByDocument(possiblyRelatedChunks);

    const toggleExpanded = (docId) => {
        setExpandedDocs(prev => ({
            ...prev,
            [docId]: !prev[docId]
        }));
    };

    const handleChunkToggle = (chunkId) => {
        const newSelection = selectedChunkIds.includes(chunkId)
            ? selectedChunkIds.filter(id => id !== chunkId)
            : [...selectedChunkIds, chunkId];
        onSelectionChange(newSelection);
    };

    const handleSelectAll = (chunks) => {
        const chunkIds = chunks.map(c => c.id);
        const allSelected = chunkIds.every(id => selectedChunkIds.includes(id));
        
        if (allSelected) {
            // Deselect all
            const newSelection = selectedChunkIds.filter(id => !chunkIds.includes(id));
            onSelectionChange(newSelection);
        } else {
            // Select all
            const newSelection = [...new Set([...selectedChunkIds, ...chunkIds])];
            onSelectionChange(newSelection);
        }
    };

    const renderChunkGroup = (docId, chunks, confidenceLevel) => {
        const isExpanded = expandedDocs[docId] !== false; // Default expanded
        const allSelected = chunks.every(c => selectedChunkIds.includes(c.id));
        const someSelected = chunks.some(c => selectedChunkIds.includes(c.id));
        
        return (
            <div key={docId} className={`chunk-doc-group ${confidenceLevel}`}>
                <div className="doc-header" onClick={() => toggleExpanded(docId)}>
                    <div className="doc-header-left">
                        <span className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>▶</span>
                        <span className="doc-name">{docId}</span>
                        <span className="chunk-count">{chunks.length} chunk{chunks.length !== 1 ? 's' : ''}</span>
                    </div>
                    <div className="doc-header-right">
                        <input
                            type="checkbox"
                            checked={allSelected}
                            ref={input => {
                                if (input) input.indeterminate = someSelected && !allSelected;
                            }}
                            onChange={(e) => {
                                e.stopPropagation();
                                handleSelectAll(chunks);
                            }}
                            onClick={(e) => e.stopPropagation()}
                        />
                    </div>
                </div>
                
                {isExpanded && (
                    <div className="chunk-list">
                        {chunks.map((chunk, idx) => (
                            <div 
                                key={chunk.id} 
                                className={`chunk-item ${selectedChunkIds.includes(chunk.id) ? 'selected' : ''}`}
                            >
                                <div className="chunk-header">
                                    <div className="chunk-header-left">
                                        <input
                                            type="checkbox"
                                            checked={selectedChunkIds.includes(chunk.id)}
                                            onChange={() => handleChunkToggle(chunk.id)}
                                            id={`chunk-${chunk.id}`}
                                        />
                                        <label htmlFor={`chunk-${chunk.id}`} className="chunk-meta">
                                            <span className="chunk-id">Chunk {idx + 1}</span>
                                            {chunk.section && (
                                                <span className="chunk-section">{chunk.section}</span>
                                            )}
                                            {chunk.similarity != null && (
                                                <span className="chunk-similarity">
                                                    {(chunk.similarity * 100).toFixed(0)}% match
                                                </span>
                                            )}
                                        </label>
                                    </div>
                                </div>
                                <div className="chunk-text">
                                    {chunk.text}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    if (loading) {
        return (
            <div className="chunk-selection-panel loading">
                <div className="loading-spinner"></div>
                <p>Finding affected chunks...</p>
            </div>
        );
    }

    const totalSelected = selectedChunkIds.length;
    const totalAvailable = highConfidenceChunks.length + possiblyRelatedChunks.length;

    return (
        <div className="chunk-selection-panel">
            <div className="panel-header">
                <h3><i className="icon-box"></i> Select Chunks to Deprecate</h3>
                <div className="selection-summary">
                    <span className="selected-count">{totalSelected} selected</span>
                    <span className="total-count">of {totalAvailable} total</span>
                </div>
            </div>

            <div className="panel-hint">
                <span className="hint-icon"><i className="icon-info"></i></span>
                <span>High confidence chunks (green) are pre-selected. Review and adjust your selection below.</span>
            </div>

            {/* High Confidence Chunks */}
            {highConfidenceChunks.length > 0 && (
                <div className="confidence-section high-confidence-section">
                    <div className="section-header">
                        <span className="confidence-badge high">High Confidence</span>
                        <span className="section-count">{highConfidenceChunks.length} chunks</span>
                    </div>
                    <p className="section-description">
                        These chunks definitely contain the policy being updated. They are pre-selected for deprecation.
                    </p>
                    {Object.entries(highConfGrouped).map(([docId, chunks]) => 
                        renderChunkGroup(docId, chunks, 'high-confidence')
                    )}
                </div>
            )}

            {/* Possibly Related Chunks */}
            {possiblyRelatedChunks.length > 0 && (
                <div className="confidence-section possibly-related-section">
                    <div 
                        className="section-header clickable" 
                        onClick={() => setShowPossiblyRelated(!showPossiblyRelated)}
                    >
                        <div className="section-header-left">
                            <span className={`expand-icon ${showPossiblyRelated ? 'expanded' : ''}`}>▶</span>
                            <span className="confidence-badge possibly">Possibly Related</span>
                            <span className="section-count">{possiblyRelatedChunks.length} chunks</span>
                        </div>
                    </div>
                    {showPossiblyRelated && (
                        <>
                            <p className="section-description">
                                These chunks are semantically related but may not directly contain the policy value. Review carefully before selecting.
                            </p>
                            {Object.entries(possiblyRelatedGrouped).map(([docId, chunks]) => 
                                renderChunkGroup(docId, chunks, 'possibly-related')
                            )}
                        </>
                    )}
                </div>
            )}

            {totalAvailable === 0 && (
                <div className="no-chunks-message">
                    <p>No chunks found. This might indicate an error in semantic search.</p>
                </div>
            )}
        </div>
    );
};

export default ChunkSelectionPanel;
