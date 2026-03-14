import React, { useState } from 'react';
import './Message.css';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import RiskAlertDisplay from './RiskAlertDisplay';
import JsonCodeViewer, { prepareJson } from './JsonCodeViewer';

/* ---------------- MARKDOWN CONFIG ---------------- */

marked.setOptions({
  gfm: true,
  breaks: true,
  headerIds: false,
  mangle: false
});

const escapeCodeHtml = (code) => code
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;');

// Override the code block renderer: all fenced blocks use a code-editor style view.
marked.use({
  renderer: {
    code({ text, lang }) {
      const normalizedLang = (lang || 'text').toLowerCase();
      const languageLabel = normalizedLang.toUpperCase();

      if (normalizedLang === 'json') {
        const { highlighted } = prepareJson(text);
        return (
          `<div class="json-viewer json-viewer-fenced" data-lang="${normalizedLang}">` +
          `<div class="json-viewer-header">` +
          `<div class="json-viewer-lang-badge">${languageLabel}</div>` +
          `<div class="json-viewer-actions">` +
          `<button type="button" class="json-viewer-copy-btn json-copy-delegated">Copy</button>` +
          `<button type="button" class="json-viewer-copy-btn json-save-delegated">Save</button>` +
          `</div></div>` +
          `<div class="json-viewer-body"><pre class="json-viewer-pre">${highlighted}</pre></div>` +
          `</div>`
        );
      }

      const highlighted = escapeCodeHtml(text);
      return (
        `<div class="json-viewer json-viewer-fenced" data-lang="${normalizedLang}">` +
        `<div class="json-viewer-header">` +
        `<div class="json-viewer-lang-badge">${languageLabel}</div>` +
        `<div class="json-viewer-actions">` +
        `<button type="button" class="json-viewer-copy-btn json-copy-delegated">Copy</button>` +
        `<button type="button" class="json-viewer-copy-btn json-save-delegated">Save</button>` +
        `</div></div>` +
        `<div class="json-viewer-body"><pre class="json-viewer-pre code-plain">${highlighted}</pre></div>` +
        `</div>`
      );
    }
  }
});

/**
 * Returns true when the entire message content is valid JSON (object or array).
 */
const isRawJson = (text) => {
  if (!text) return false;
  const t = text.trim();
  if (!t.startsWith('{') && !t.startsWith('[')) return false;
  try { JSON.parse(t); return true; } catch { return false; }
};

const renderMarkdown = (text) => {
  if (!text) return '';

  // Remove source citations but KEEP formatting
  const cleaned = text
    .replace(/\(Source:[^)]*\)/gi, '')
    .replace(/\(Source:[^)]*$/gi, '')
    .replace(/Source:[^.]*\./gi, '')
    .trim();

  const rawHtml = marked.parse(cleaned);
  // Allow <button> so fenced-block copy buttons survive DOMPurify
  return DOMPurify.sanitize(rawHtml, {
    ADD_TAGS: ['button'],
    ALLOW_DATA_ATTR: true,
  });
};

const getExtensionForLanguage = (language = 'text') => {
  const lang = (language || 'text').toLowerCase();
  const extMap = {
    json: 'json',
    javascript: 'js',
    js: 'js',
    jsx: 'jsx',
    typescript: 'ts',
    ts: 'ts',
    tsx: 'tsx',
    python: 'py',
    py: 'py',
    java: 'java',
    c: 'c',
    cpp: 'cpp',
    csharp: 'cs',
    cs: 'cs',
    go: 'go',
    rust: 'rs',
    ruby: 'rb',
    php: 'php',
    kotlin: 'kt',
    swift: 'swift',
    sql: 'sql',
    xml: 'xml',
    html: 'html',
    css: 'css',
    scss: 'scss',
    markdown: 'md',
    md: 'md',
    yaml: 'yml',
    yml: 'yml',
    bash: 'sh',
    shell: 'sh',
    sh: 'sh',
    text: 'txt'
  };
  return extMap[lang] || 'txt';
};

/* ---------------- COMPONENT ---------------- */

function Message({ message, user }) {
  const isUser = message.role === 'user';
  const [showSources, setShowSources] = useState(null);
  const [imageError, setImageError] = useState(false);
  const [showFilePreviewModal, setShowFilePreviewModal] = useState(false);
  const hasSources =
    message.metadata?.sources && message.metadata.sources.length > 0;
  const isError = message.metadata?.isError;

  const formatFileSize = (bytes) => {
    if (!bytes) return '';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFileChipIcon = (fileType, fileName) => {
    if (fileType?.startsWith('image/')) {
      return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <circle cx="8.5" cy="8.5" r="1.5"></circle>
          <polyline points="21 15 16 10 5 21"></polyline>
        </svg>
      );
    }
    if (fileType === 'application/pdf' || fileName?.endsWith('.pdf')) {
      return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="9" y1="13" x2="15" y2="13"></line>
          <line x1="9" y1="17" x2="15" y2="17"></line>
        </svg>
      );
    }
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
        <polyline points="13 2 13 9 20 9"></polyline>
      </svg>
    );
  };

  const getInitials = (name) => {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const formatDocName = (docId) => {
    if (!docId) return 'Unknown Document';
    return docId
      .replace('ncie_', '')
      .replace(/_/g, ' ')
      .split(' ')
      .map(
        (word) => word.charAt(0).toUpperCase() + word.slice(1)
      )
      .join(' ');
  };

  const getRelevanceColor = (similarity) => {
    if (similarity >= 0.8) return '#10a37f';
    if (similarity >= 0.6) return '#fbbf24';
    return '#94a3b8';
  };

  const getRelevanceLabel = (similarity) => {
    if (similarity >= 0.8) return 'Highly Relevant';
    if (similarity >= 0.6) return 'Relevant';
    return 'Related';
  };

  const topSources = message.metadata?.sources?.slice(0, 3) || [];
  const hasExtractedPreferences = message.extracted_preferences && message.extracted_preferences.length > 0;
  const hasRiskAlerts = message.metadata?.risk_alerts && message.metadata.risk_alerts.length > 0;
  const attachment = message.file || message.metadata?.file || null;
  const attachmentKind = attachment?.preview_kind || (attachment?.type?.startsWith('image/') ? 'image' : 'other');
  const attachmentPreviewUrl = attachment?.preview_url || attachment?.url || null;
  const canPreviewAttachment = Boolean(attachmentPreviewUrl || attachment?.preview_text);

  const handleDelegatedCodeActions = async (e) => {
    const copyBtn = e.target.closest('.json-copy-delegated');
    const saveBtn = e.target.closest('.json-save-delegated');
    if (!copyBtn && !saveBtn) return;

    const actionBtn = copyBtn || saveBtn;
    const viewer = actionBtn.closest('.json-viewer');
    const pre = viewer?.querySelector('.json-viewer-pre');
    if (!pre) return;

    try {
      if (copyBtn) {
        await navigator.clipboard.writeText(pre.innerText || '');
        const previousLabel = copyBtn.textContent;
        copyBtn.textContent = 'Copied!';
        setTimeout(() => {
          copyBtn.textContent = previousLabel || 'Copy';
        }, 1800);
        return;
      }

      const lang = viewer?.dataset?.lang || 'text';
      const extension = getExtensionForLanguage(lang);
      const filename = `code_snippet.${extension}`;
      const blob = new Blob([pre.innerText || ''], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      const previousLabel = saveBtn.textContent;
      saveBtn.textContent = 'Saved!';
      setTimeout(() => {
        saveBtn.textContent = previousLabel || 'Save';
      }, 1800);
    } catch {
      // Ignore clipboard failures in unsupported browsers
    }
  };

  return (
    <div className={`message ${message.role} ${isError ? 'error' : ''}`}>
      <div className="message-avatar">
        {isUser ? (
          <div
            className={`user-avatar ${
              user?.profile_picture && !imageError ? 'has-image' : ''
            }`}
          >
            {user?.profile_picture && !imageError ? (
              <img 
                src={user.profile_picture} 
                alt="User Avatar"
                onError={() => setImageError(true)}
              />
            ) : (
              <span className="avatar-initials">
                {getInitials(user?.name)}
              </span>
            )}
          </div>
        ) : (
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" />
          </svg>
        )}
      </div>

      <div className="message-content">
        {/* Risk Alert Indicator - Top Right */}
        {!isUser && hasRiskAlerts && (
          <div className="message-risk-indicator">
            <RiskAlertDisplay riskAlerts={message.metadata.risk_alerts} />
          </div>
        )}

        {/* File attachment preview persists after the assistant responds */}
        {isUser && attachment && (
          <div className="message-file-block">
            <div
              className={`message-file-chip ${canPreviewAttachment ? 'clickable' : ''}`}
              onClick={() => {
                if (canPreviewAttachment) {
                  setShowFilePreviewModal(true);
                }
              }}
            >
              {attachmentKind === 'image' && attachmentPreviewUrl ? (
                <img
                  className="message-file-chip-thumb"
                  src={attachmentPreviewUrl}
                  alt={attachment.name || 'attachment'}
                />
              ) : (
                <div className="message-file-chip-icon">
                  {getFileChipIcon(attachment.type, attachment.name)}
                </div>
              )}
              <div className="message-file-chip-info">
                <span className="message-file-chip-name">{attachment.name}</span>
                {attachment.size && (
                  <span className="message-file-chip-size">{formatFileSize(attachment.size)}</span>
                )}
              </div>
              {canPreviewAttachment && <span className="message-file-chip-action">Preview</span>}
            </div>

            {attachmentKind === 'image' && attachmentPreviewUrl && (
              <div className="message-file-inline-preview" onClick={() => setShowFilePreviewModal(true)}>
                <img src={attachmentPreviewUrl} alt={attachment.name || 'attachment preview'} />
              </div>
            )}
          </div>
        )}

        {/* Code-viewer for raw JSON and for fenced markdown code blocks */}
        {isRawJson(message.content) ? (
          <JsonCodeViewer code={message.content} language="json" fileBaseName="co_po_mapping" />
        ) : (
          <div
            className="message-text"
            onClick={handleDelegatedCodeActions}
            dangerouslySetInnerHTML={{
              __html: renderMarkdown(message.content)
            }}
          />
        )}

        {hasSources && topSources.length > 0 && (
          <div className="sources-tags">
            {topSources.map((source, index) => {
              const relevanceColor = getRelevanceColor(
                source.similarity || 0
              );
              return (
                <button
                  key={index}
                  className="source-tag"
                  onClick={() =>
                    setShowSources(
                      showSources === index ? null : index
                    )
                  }
                  title={`${formatDocName(source.doc_id)} - ${
                    source.section
                  }`}
                >
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  <span>{index + 1}</span>
                </button>
              );
            })}
          </div>
        )}

        {showSources !== null && topSources[showSources] && (
          <div className="source-detail">
            {(() => {
              const source = topSources[showSources];
              const relevanceColor = getRelevanceColor(
                source.similarity || 0
              );
              return (
                <div
                  className="source-detail-content"
                  style={{ borderLeftColor: relevanceColor }}
                >
                  <div className="source-detail-header">
                    <span className="source-detail-title">
                      <strong>
                        {formatDocName(source.doc_id)}
                      </strong>
                    </span>
                    <button
                      className="source-detail-close"
                      onClick={() => setShowSources(null)}
                    >
                      ×
                    </button>
                  </div>

                  <p className="source-detail-section">
                    {source.section}
                  </p>

                  <div className="source-detail-footer">
                    <span
                      className="source-detail-relevance"
                      style={{ color: relevanceColor }}
                    >
                      {getRelevanceLabel(source.similarity)}
                    </span>
                    <span
                      className="source-detail-match"
                      style={{ color: relevanceColor }}
                    >
                      {(source.similarity * 100).toFixed(0)}%
                      match
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

        {hasExtractedPreferences && isUser && (
          <div className="preference-indicator">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
            </svg>
            <span>Preference learned from this message</span>
          </div>
        )}

        {showFilePreviewModal && attachment && (
          <div className="file-previewer-overlay" onClick={() => setShowFilePreviewModal(false)}>
            <div className="file-previewer-content" onClick={(e) => e.stopPropagation()}>
              <div className="file-previewer-header">
                <h3>{attachment.name || 'Attachment Preview'}</h3>
                <button type="button" onClick={() => setShowFilePreviewModal(false)} className="file-previewer-close">
                  ×
                </button>
              </div>
              <div className="file-previewer-body">
                {attachmentKind === 'image' && attachmentPreviewUrl && (
                  <div className="file-previewer-image-wrap">
                    <img src={attachmentPreviewUrl} alt={attachment.name || 'attachment'} />
                  </div>
                )}

                {attachmentKind === 'pdf' && attachmentPreviewUrl && (
                  <iframe
                    title={attachment.name || 'PDF preview'}
                    src={attachmentPreviewUrl}
                    className="file-previewer-frame"
                  />
                )}

                {attachmentKind === 'text' && attachment?.preview_text && (
                  <pre className="file-previewer-text">{attachment.preview_text}</pre>
                )}

                {attachmentKind === 'text' && !attachment?.preview_text && attachmentPreviewUrl && (
                  <iframe
                    title={attachment.name || 'Text preview'}
                    src={attachmentPreviewUrl}
                    className="file-previewer-frame"
                  />
                )}

                {!['image', 'pdf', 'text'].includes(attachmentKind) && attachmentPreviewUrl && (
                  <div className="file-previewer-download">
                    <p>Preview is unavailable for this file type.</p>
                    <a href={attachmentPreviewUrl} target="_blank" rel="noreferrer">Open file</a>
                  </div>
                )}

                {attachment?.preview_text_truncated && (
                  <div className="file-previewer-note">
                    Preview truncated for performance.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Message;
