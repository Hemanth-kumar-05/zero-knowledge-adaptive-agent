import React, { useState } from 'react';

/**
 * Tokenizes a pretty-printed JSON string and wraps tokens in
 * <span> tags with CSS classes for VS Code-style syntax highlighting.
 * Input must already be HTML-escaped (&amp; &lt; &gt;).
 */
export const syntaxHighlightJson = (code) => {
  // Escape HTML first so any <, > in string values won't break markup
  const escaped = code
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Classic JSON highlighter regex
  return escaped.replace(
    /("(?:\\u[a-fA-F0-9]{4}|\\[^u]|[^\\"])*"(?:\s*:)?|\b(?:true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    (match) => {
      if (/^"/.test(match)) {
        const cls = /:$/.test(match) ? 'jsh-key' : 'jsh-string';
        return `<span class="${cls}">${match}</span>`;
      }
      if (/^true$|^false$/.test(match)) return `<span class="jsh-bool">${match}</span>`;
      if (match === 'null') return `<span class="jsh-null">${match}</span>`;
      return `<span class="jsh-number">${match}</span>`;
    }
  );
};

/**
 * Pretty-print + highlight a JSON string.
 * Returns { highlighted: string, pretty: string }.
 */
export const prepareJson = (raw) => {
  let pretty = raw.trim();
  try {
    pretty = JSON.stringify(JSON.parse(pretty), null, 2);
  } catch {
    // use raw if it's not valid JSON
  }
  return { pretty, highlighted: syntaxHighlightJson(pretty) };
};

/* ------------------------------------------------------------------ */

const CopyIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
  </svg>
);

const CheckIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <polyline points="20 6 9 17 4 12"></polyline>
  </svg>
);

const CodeBracketsIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="16 18 22 12 16 6"></polyline>
    <polyline points="8 6 2 12 8 18"></polyline>
  </svg>
);

const SaveIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
    <polyline points="17 21 17 13 7 13 7 21"></polyline>
    <polyline points="7 3 7 8 15 8"></polyline>
  </svg>
);

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

/* ------------------------------------------------------------------ */

const JsonCodeViewer = ({ code, language = 'json', fileBaseName = 'message_code' }) => {
  const [copied, setCopied] = useState(false);
  const [saved, setSaved] = useState(false);
  const { pretty, highlighted } = prepareJson(code);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(pretty);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard not available — no-op
    }
  };

  const handleSave = () => {
    try {
      const extension = getExtensionForLanguage(language);
      const safeBase = (fileBaseName || 'message_code').replace(/[^a-zA-Z0-9_-]+/g, '_');
      const filename = `${safeBase}.${extension}`;
      const blob = new Blob([pretty], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // no-op when save is blocked
    }
  };

  return (
    <div className="json-viewer">
      <div className="json-viewer-header">
        <div className="json-viewer-lang-badge">
          <CodeBracketsIcon />
          <span>JSON</span>
        </div>
        <div className="json-viewer-actions">
          <button className="json-viewer-copy-btn" onClick={handleCopy}>
            {copied ? <><CheckIcon /> Copied!</> : <><CopyIcon /> Copy</>}
          </button>
          <button className="json-viewer-copy-btn" onClick={handleSave}>
            {saved ? <><CheckIcon /> Saved!</> : <><SaveIcon /> Save</>}
          </button>
        </div>
      </div>
      <div className="json-viewer-body">
        <pre
          className="json-viewer-pre"
          dangerouslySetInnerHTML={{ __html: highlighted }}
        />
      </div>
    </div>
  );
};

export default JsonCodeViewer;
