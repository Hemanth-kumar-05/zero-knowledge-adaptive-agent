import { useState, useMemo, useRef, useEffect } from 'react';
import './IndividualChunkEditor.css';
import { FaEdit, FaCheckCircle, FaInfoCircle, FaChevronRight, FaChevronLeft } from 'react-icons/fa';

/**
 * Improved diff algorithm using word-level granularity
 * This provides better highlighting for inline edits
 */
const computeDiff = (original, edited) => {
    if (original === edited) {
        return [{ type: 'unchanged', text: edited }];
    }
    
    // Split into words and whitespace tokens
    const tokenize = (text) => {
        const tokens = [];
        const regex = /(\s+|[^\s]+)/g;
        let match;
        while ((match = regex.exec(text)) !== null) {
            tokens.push(match[0]);
        }
        return tokens;
    };
    
    const origTokens = tokenize(original);
    const editTokens = tokenize(edited);
    
    // Dynamic programming LCS (Longest Common Subsequence)
    const m = origTokens.length;
    const n = editTokens.length;
    const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));
    
    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (origTokens[i - 1] === editTokens[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }
    
    // Backtrack to find diff
    const result = [];
    let i = m, j = n;
    let deletedBuffer = [];
    let addedBuffer = [];
    
    const flushBuffers = () => {
        if (deletedBuffer.length > 0) {
            result.unshift({ type: 'deleted', text: deletedBuffer.join('') });
            deletedBuffer = [];
        }
        if (addedBuffer.length > 0) {
            result.unshift({ type: 'added', text: addedBuffer.join('') });
            addedBuffer = [];
        }
    };
    
    while (i > 0 || j > 0) {
        if (i > 0 && j > 0 && origTokens[i - 1] === editTokens[j - 1]) {
            flushBuffers();
            result.unshift({ type: 'unchanged', text: origTokens[i - 1] });
            i--;
            j--;
        } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
            addedBuffer.unshift(editTokens[j - 1]);
            j--;
        } else if (i > 0) {
            deletedBuffer.unshift(origTokens[i - 1]);
            i--;
        }
    }
    
    flushBuffers();
    
    // Merge consecutive same-type segments
    const merged = [];
    for (const segment of result) {
        if (merged.length > 0 && merged[merged.length - 1].type === segment.type) {
            merged[merged.length - 1].text += segment.text;
        } else {
            merged.push(segment);
        }
    }
    
    return merged.length > 0 ? merged : [{ type: 'unchanged', text: edited }];
};

/**
 * IndividualChunkEditor - Master-Detail layout for editing chunks
 * 
 * Features:
 * - Master panel: List of chunks with progress
 * - Detail panel: Full editor for selected chunk
 * - Keyword highlighting from user claim
 * - Navigation buttons for prev/next chunk
 */
const IndividualChunkEditor = ({ 
    selectedChunks = [],  // Array of chunk objects with {id, text, doc_id, section}
    userClaim = '',       // User's policy claim for keyword extraction
    onChange,             // Callback when any chunk is edited: (chunkId, newText) => void
    onChangeSelection     // Optional callback to go back to chunk selection
}) => {
    const [editedChunks, setEditedChunks] = useState({});
    const [activeChunkId, setActiveChunkId] = useState(
        selectedChunks.length > 0 ? selectedChunks[0].id : null
    );
    const textareaRef = useRef(null);
    const backdropRef = useRef(null);

    // Sync scroll between textarea and backdrop
    const handleScroll = (e) => {
        if (backdropRef.current && textareaRef.current) {
            backdropRef.current.scrollTop = e.target.scrollTop;
            backdropRef.current.scrollLeft = e.target.scrollLeft;
        }
    };

    // Extract keywords from user claim (improved extraction)
    const keywords = useMemo(() => {
        if (!userClaim) return [];
        
        const stopWords = ['the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by', 'from', 'says', 'now', 'not'];
        
        const extractedKeywords = [];
        
        // 1. Extract percentages (e.g., "40%", "50%")
        const percentages = userClaim.match(/\d+(\.\d+)?%/g);
        if (percentages) {
            extractedKeywords.push(...percentages);
        }
        
        // 2. Extract dates (e.g., "March 5, 2026", "2026/03/05")
        const dates = userClaim.match(/\b\d{4}\b|\b\d{1,2}\/\d{1,2}\/\d{2,4}\b/g);
        if (dates) {
            extractedKeywords.push(...dates);
        }
        
        // 3. Extract month names
        const months = userClaim.match(/\b(January|February|March|April|May|June|July|August|September|October|November|December)\b/gi);
        if (months) {
            extractedKeywords.push(...months);
        }
        
        // 4. Extract all-caps abbreviations (e.g., "CA", "GPA", "CGPA")
        const abbreviations = userClaim.match(/\b[A-Z]{2,}\b/g);
        if (abbreviations) {
            extractedKeywords.push(...abbreviations);
        }
        
        // 5. Extract standalone numbers that might be significant
        const numbers = userClaim.match(/\b\d+\b/g);
        if (numbers) {
            extractedKeywords.push(...numbers);
        }
        
        // 6. Extract important words (longer than 3 chars, not stop words)
        const words = userClaim.toLowerCase()
            .replace(/[^\w\s]/g, ' ')
            .split(/\s+/)
            .filter(word => word.length > 3 && !stopWords.includes(word));
        extractedKeywords.push(...words);
        
        // Remove duplicates (case-insensitive) and return
        const unique = [...new Set(extractedKeywords.map(k => k.toLowerCase()))];
        return unique;
    }, [userClaim]);

    const handleChunkEdit = (chunkId, newText) => {
        setEditedChunks(prev => ({
            ...prev,
            [chunkId]: newText
        }));
        onChange(chunkId, newText);
    };

    const getChunkText = (chunk) => {
        return editedChunks[chunk.id] ?? chunk.text;
    };

    const isChunkEdited = (chunkId) => {
        return editedChunks.hasOwnProperty(chunkId);
    };

    const activeChunk = selectedChunks.find(c => c.id === activeChunkId);
    const activeChunkIndex = selectedChunks.findIndex(c => c.id === activeChunkId);

    const goToNext = () => {
        if (activeChunkIndex < selectedChunks.length - 1) {
            setActiveChunkId(selectedChunks[activeChunkIndex + 1].id);
        }
    };

    const goToPrevious = () => {
        if (activeChunkIndex > 0) {
            setActiveChunkId(selectedChunks[activeChunkIndex - 1].id);
        }
    };

    // Highlight keywords in text (improved to handle percentages, abbreviations, etc.)
    const highlightKeywords = (text) => {
        if (!keywords.length || !text) return text;
        
        // Sort keywords by length (longest first) to match longer patterns first
        const sortedKeywords = [...keywords].sort((a, b) => b.length - a.length);
        
        // Escape special regex characters in keywords
        const escapeRegex = (str) => str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        
        // Build regex pattern with proper word boundaries
        // Use lookahead/lookbehind for better matching
        const pattern = sortedKeywords.map(kw => {
            const escaped = escapeRegex(kw);
            // For percentages and special patterns, don't require word boundaries
            if (/\d+%|\d+/.test(kw)) {
                return `(?<=^|\\s|[^\\w])(${escaped})(?=$|\\s|[^\\w])`;
            }
            // For regular words, use word boundaries
            return `\\b(${escaped})\\b`;
        }).join('|');
        
        const regex = new RegExp(pattern, 'gi');
        
        // Split and highlight
        const parts = [];
        let lastIndex = 0;
        let match;
        
        while ((match = regex.exec(text)) !== null) {
            // Add text before match
            if (match.index > lastIndex) {
                parts.push(text.substring(lastIndex, match.index));
            }
            // Add highlighted match
            parts.push(
                <mark key={`highlight-${match.index}`} className="keyword-highlight">
                    {match[0]}
                </mark>
            );
            lastIndex = regex.lastIndex;
        }
        
        // Add remaining text
        if (lastIndex < text.length) {
            parts.push(text.substring(lastIndex));
        }
        
        return parts.length > 0 ? parts : text;
    };

    // Render edited text with diff highlighting
    // IMPORTANT: Don't show deleted text - it doesn't exist in the textarea
    // Only highlight additions in green, show unchanged text normally
    const renderEditedTextWithDiff = (originalText, editedText) => {
        if (originalText === editedText) {
            // No changes, just return the text
            return editedText;
        }
        
        const diff = computeDiff(originalText, editedText);
        
        return diff.map((part, idx) => {
            if (part.type === 'added') {
                // Show added text with green highlight
                return (
                    <mark key={`diff-${idx}`} className="text-added">
                        {part.text}
                    </mark>
                );
            } else if (part.type === 'deleted') {
                // Don't render deleted text - it doesn't exist in the textarea
                // Rendering it would cause cursor position misalignment
                return null;
            } else {
                // Show unchanged text normally
                return <span key={`diff-${idx}`}>{part.text}</span>;
            }
        });
    };

    if (!selectedChunks.length) {
        return (
            <div className="individual-chunk-editor">
                <div className="editor-empty">
                    <FaInfoCircle />
                    <p>No chunks selected for editing</p>
                </div>
            </div>
        );
    }

    if (!activeChunk) {
        setActiveChunkId(selectedChunks[0]?.id);
        return null;
    }

    const currentText = getChunkText(activeChunk);
    const isEdited = isChunkEdited(activeChunk.id);

    return (
        <div className="individual-chunk-editor master-detail">
            {/* Header with stats */}
            <div className="editor-header">
                <div className="editor-header-left">
                    <h3>Edit Selected Chunks</h3>
                    {onChangeSelection && (
                        <button className="btn-change-selection" onClick={onChangeSelection} title="Go back to chunk selection">
                            ← Change Selection
                        </button>
                    )}
                </div>
                <div className="editor-stats">
                    <span className="stat-item">
                        <strong>{selectedChunks.length}</strong> chunks
                    </span>
                    <span className="stat-separator">•</span>
                    <span className="stat-item edited-stat">
                        <FaCheckCircle /> <strong>{Object.keys(editedChunks).length}</strong> edited
                    </span>
                </div>
            </div>

            {/* Master-Detail Layout */}
            <div className="master-detail-container">
                {/* LEFT: Master Panel - Chunk List */}
                <div className="master-panel">
                    <div className="master-header">
                        <span>All Chunks</span>
                        <span className="progress-badge">
                            {Object.keys(editedChunks).length}/{selectedChunks.length}
                        </span>
                    </div>
                    
                    <div className="chunk-list">
                        {selectedChunks.map((chunk, idx) => {
                            const isActive = chunk.id === activeChunkId;
                            const isEdited = isChunkEdited(chunk.id);
                            
                            return (
                                <div
                                    key={chunk.id}
                                    className={`chunk-list-item ${isActive ? 'active' : ''} ${isEdited ? 'edited' : ''}`}
                                    onClick={() => setActiveChunkId(chunk.id)}
                                >
                                    <div className="chunk-list-header">
                                        <span className="chunk-number">#{idx + 1}</span>
                                        {isEdited && <FaCheckCircle className="edited-icon" />}
                                    </div>
                                    <div className="chunk-list-meta">
                                        <div className="chunk-doc">{chunk.doc_id}</div>
                                        <div className="chunk-section">{chunk.section}</div>
                                    </div>
                                    {/* <div className="chunk-list-preview">
                                        {chunk.text.substring(0, 80)}...
                                    </div> */}
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* RIGHT: Detail Panel - Editor */}
                <div className="detail-panel">
                    {/* Navigation */}
                    <div className="detail-header">
                        <div className="chunk-title-section">
                            <h4>Chunk {activeChunkIndex + 1} of {selectedChunks.length}</h4>
                            <span className="chunk-meta-inline">
                                {activeChunk.doc_id} • {activeChunk.section}
                            </span>
                        </div>
                        
                        <div className="navigation-buttons">
                            <button
                                className="nav-btn"
                                onClick={goToPrevious}
                                disabled={activeChunkIndex === 0}
                                title="Previous chunk"
                            >
                                <FaChevronLeft /> Previous
                            </button>
                            <button
                                className="nav-btn"
                                onClick={goToNext}
                                disabled={activeChunkIndex === selectedChunks.length - 1}
                                title="Next chunk"
                            >
                                Next <FaChevronRight />
                            </button>
                        </div>
                    </div>

                    {/* Hint */}
                    <div className="editor-hint">
                        <FaInfoCircle className="hint-icon" />
                        <span>Keywords from the claim are <mark className="keyword-highlight">highlighted in yellow</mark>. Your additions/changes will appear in <mark className="text-added">green</mark> in real-time.</span>
                    </div>

                    {/* Split View: Original | Edited */}
                    <div className="split-view-container">
                        {/* LEFT: Original Text */}
                        <div className="split-pane original-pane">
                            <div className="pane-header">
                                <label className="section-label">Original Text</label>
                            </div>
                            <div className="pane-content">
                                <div className="original-text-display">
                                    {highlightKeywords(activeChunk.text)}
                                </div>
                            </div>
                        </div>

                        {/* RIGHT: Editor */}
                        <div className="split-pane editor-pane">
                            <div className="pane-header">
                                <label className="section-label">
                                    <FaEdit /> Edit Text {isEdited && <span className="modified-badge">(Modified)</span>}
                                </label>
                            </div>
                            <div className="pane-content">
                                <div className="editor-wrapper">
                                    {/* Highlighted backdrop */}
                                    <div 
                                        ref={backdropRef}
                                        className="editor-backdrop" 
                                        aria-hidden="true"
                                    >
                                        {renderEditedTextWithDiff(activeChunk.text, currentText)}
                                    </div>
                                    {/* Actual editable textarea */}
                                    <textarea
                                        ref={textareaRef}
                                        id="chunk-editor"
                                        className="chunk-textarea"
                                        value={currentText}
                                        onChange={(e) => handleChunkEdit(activeChunk.id, e.target.value)}
                                        onScroll={handleScroll}
                                        placeholder="Edit the policy text for this chunk..."
                                        spellCheck="false"
                                    />
                                </div>
                            </div>
                            <div className="pane-footer">
                                <span className="char-count">{currentText.length} characters</span>
                            </div>
                        </div>
                    </div>

                    {/* Footer Info */}
                    <div className="detail-footer">
                        <FaInfoCircle className="footer-icon" />
                        <span>This edited text will replace the original chunk. The old chunk will be deprecated.</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default IndividualChunkEditor;
