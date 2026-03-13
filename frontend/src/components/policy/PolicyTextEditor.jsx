import { useState } from 'react';
import './PolicyTextEditor.css';
import { FaLightbulb, FaInfoCircle, FaEdit, FaEye } from 'react-icons/fa';

/**
 * PolicyTextEditor - Edit new policy text with AI suggestions
 * 
 * Features:
 * - Text editor for new policy
 * - Character count
 * - Preview of how text will be chunked
 * - AI suggestion (future enhancement)
 */
const PolicyTextEditor = ({ 
    value = '', 
    onChange,
    policyArea = '',
    minLength = 20,
    placeholder = "Enter the complete updated policy text..."
}) => {
    const [showPreview, setShowPreview] = useState(false);

    const chunkSize = 800;
    const chunkOverlap = 100;

    // Preview how text will be chunked
    const generateChunkPreview = () => {
        const chunks = [];
        let position = 0;
        const textLength = value.length;

        while (position < textLength) {
            const chunkText = value.slice(position, position + chunkSize).trim();
            if (chunkText) {
                chunks.push({
                    start: position,
                    end: Math.min(position + chunkSize, textLength),
                    text: chunkText
                });
            }
            position += (chunkSize - chunkOverlap);
        }

        return chunks;
    };

    const chunks = generateChunkPreview();
    const isValid = value.trim().length >= minLength;
    const characterCount = value.length;

    return (
        <div className="policy-text-editor">
            <div className="editor-header">
                <label htmlFor="policy-text-input" className="editor-label">
                    New Policy Text *
                </label>
                <div className="editor-actions">
                    <span 
                        className={`char-count ${isValid ? 'valid' : 'invalid'}`}
                    >
                        {characterCount} characters {!isValid && `(min ${minLength})`}
                    </span>
                    <button
                        type="button"
                        className="btn-preview"
                        onClick={() => setShowPreview(!showPreview)}
                        aria-label={showPreview ? 'Edit policy text' : 'Preview chunks'}
                    >
                        {/* <i className="icon" aria-hidden="true">{showPreview ? '✎' : '◉'}</i> */}
                        {showPreview ? <FaEdit /> : <FaEye />}
                        {showPreview ? 'Edit' : 'Preview Chunks'}
                    </button>
                </div>
            </div>

            {policyArea && (
                <div className="policy-context">
                    <strong>Policy Area:</strong> {policyArea}
                </div>
            )}

            {!showPreview ? (
                <>
                    <textarea
                        id="policy-text-input"
                        className="policy-textarea"
                        value={value}
                        onChange={(e) => onChange(e.target.value)}
                        placeholder={placeholder}
                        rows="10"
                        required
                    />
                    <div className="editor-hints">
                        <div className="hint-item">
                            {/* <i className="hint-icon" aria-label="tip">●</i> */}
                            <FaLightbulb className="hint-icon" aria-label="tip" />
                            <span>This text will be chunked into ~{chunks.length} piece{chunks.length !== 1 ? 's' : ''} of {chunkSize} characters for embedding</span>
                        </div>
                        <div className="hint-item">
                            {/* <i className="hint-icon" aria-label="information">ⓘ</i> */}
                            <FaInfoCircle className="hint-icon" aria-label="information" />
                            <span>Write complete, self-contained policy text including context and details</span>
                        </div>
                    </div>
                </>
            ) : (
                <div className="chunk-preview-container">
                    <div className="preview-header">
                        <h4>Chunk Preview</h4>
                        <p className="preview-description">
                            Your policy text will be split into {chunks.length} chunk{chunks.length !== 1 ? 's' : ''} with {chunkOverlap} character overlap for better semantic retrieval.
                        </p>
                    </div>
                    
                    <div className="preview-chunks">
                        {chunks.map((chunk, idx) => (
                            <div key={idx} className="preview-chunk">
                                <div className="preview-chunk-header">
                                    <span className="chunk-number">Chunk {idx + 1}</span>
                                    <span className="chunk-range">
                                        Characters {chunk.start}-{chunk.end} ({chunk.text.length} chars)
                                    </span>
                                </div>
                                <div className="preview-chunk-text">
                                    {chunk.text}
                                </div>
                            </div>
                        ))}
                    </div>

                    {chunks.length === 0 && (
                        <div className="preview-empty">
                            <p>No preview available. Enter policy text to see how it will be chunked.</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default PolicyTextEditor;
