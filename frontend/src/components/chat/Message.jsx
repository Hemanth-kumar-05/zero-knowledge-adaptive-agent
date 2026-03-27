import React, { useEffect, useRef, useState } from 'react';
import './Message.css';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import RiskAlertDisplay from './RiskAlertDisplay';
import JsonCodeViewer, { prepareJson } from './JsonCodeViewer';
import PlotlyChart from './PlotlyChart';
import { runPythonOnDataset } from '../../utils/pyodideRunner';
import api from '../../api/client';

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

  const rawHtml = marked
    .parse(cleaned)
    .replace(/<table>/g, '<div class="markdown-table-scroll"><table>')
    .replace(/<\/table>/g, '</table></div>');
  // Allow <button> so fenced-block copy buttons survive DOMPurify
  return DOMPurify.sanitize(rawHtml, {
    ADD_TAGS: ['button'],
    ALLOW_DATA_ATTR: true,
  });
};

const looksLikeMarkdownTable = (text) => {
  if (!text) return false;
  return /\|.+\|/.test(text) && /\|\s*---/.test(text);
};

const maybeFormatExecutionOutput = (text) => {
  if (!text) return '';
  if (looksLikeMarkdownTable(text)) return text;

  const lines = text
    .split('\n')
    .map((line) => line.replace(/\t/g, '    ').trimEnd())
    .filter((line) => line.trim());

  if (lines.length < 2) return text;

  const headerIndex = lines.findIndex((line) => /\s{2,}/.test(line));
  if (headerIndex === -1 || headerIndex === lines.length - 1) return text;

  const titleLines = lines.slice(0, headerIndex);
  const tableLines = lines.slice(headerIndex);
  const parsedRows = tableLines.map((line) => _splitTableLine(line)).filter((row) => row.length > 1);

  if (parsedRows.length < 2) return text;

  const columnCount = parsedRows[0].length;
  if (columnCount < 2) return text;
  if (!parsedRows.every((row) => row.length === columnCount)) return text;

  const header = `| ${parsedRows[0].join(' | ')} |`;
  const separator = `| ${Array(columnCount).fill('---').join(' | ')} |`;
  const body = parsedRows.slice(1).map((row) => `| ${row.join(' | ')} |`);

  return [...titleLines, header, separator, ...body].join('\n');
};

const _splitTableLine = (line) => {
  const strongSplit = line.split(/\s{2,}/).map((cell) => cell.trim()).filter(Boolean);
  if (strongSplit.length > 1) return strongSplit;

  const looseSplit = line.trim().split(/\s+/).filter(Boolean);
  if (looseSplit.length <= 2) return looseSplit;

  const first = looseSplit[0];
  const last = looseSplit[looseSplit.length - 1];
  const middle = looseSplit.slice(1, -1);

  if (/^[A-Za-z0-9_-]+$/.test(first) && /^-?\d+(\.\d+)?$/.test(last)) {
    return [first, ...middle.slice(0, 1), ...middle.slice(1), last];
  }

  return looseSplit;
};

const splitDelimitedLine = (line, delimiter) => {
  const cells = [];
  let current = '';
  let inQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];

    if (char === '"') {
      if (inQuotes && next === '"') {
        current += '"';
        index += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === delimiter && !inQuotes) {
      cells.push(current.trim());
      current = '';
      continue;
    }

    current += char;
  }

  cells.push(current.trim());
  return cells;
};

const parseDelimitedPreview = (text, fileName = '', fileType = '') => {
  if (!text) return null;

  const trimmed = text.trim();
  const nameLower = (fileName || '').toLowerCase();
  const isTsv = nameLower.endsWith('.tsv') || fileType === 'text/tab-separated-values';
  const delimiter = isTsv ? '\t' : ',';
  const lines = trimmed
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length < 2) return null;
  if (!isTsv && !nameLower.endsWith('.csv') && !lines[0].includes(',')) return null;
  if (isTsv && !lines[0].includes('\t')) return null;

  const rows = lines.slice(0, 21).map((line) => splitDelimitedLine(line, delimiter));
  const header = rows[0];
  if (!header || header.length < 2) return null;

  const columnCount = header.length;
  const normalizedRows = rows
    .slice(1)
    .map((row) => {
      if (row.length === columnCount) return row;
      if (row.length < columnCount) return [...row, ...Array(columnCount - row.length).fill('')];
      return row.slice(0, columnCount);
    });

  return {
    header,
    rows: normalizedRows,
    hasMoreRows: lines.length > 21,
  };
};

const CsvPreviewTable = ({ preview, compact = false }) => {
  if (!preview) return null;

  return (
    <div className={`csv-preview-shell ${compact ? 'compact' : ''}`}>
      <div className="csv-preview-scroll">
        <table className="csv-preview-table">
          <thead>
            <tr>
              {preview.header.map((cell, index) => (
                <th key={`${cell}-${index}`}>{cell || `Column ${index + 1}`}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {preview.rows.map((row, rowIndex) => (
              <tr key={`row-${rowIndex}`}>
                {preview.header.map((_, cellIndex) => (
                  <td key={`cell-${rowIndex}-${cellIndex}`}>{row[cellIndex] || ''}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {preview.hasMoreRows && (
        <div className="csv-preview-note">Preview truncated. Open the file or run analysis to work with the full dataset.</div>
      )}
    </div>
  );
};

const extractFirstPythonBlock = (text) => {
  if (!text) return '';
  const match = text.match(/```(?:python|py)\s*([\s\S]*?)```/i);
  return match ? match[1].trim() : '';
};

const stripPythonBlocks = (text) => {
  if (!text) return '';
  return text
    .replace(/```(?:python|py)\s*[\s\S]*?```/gi, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
};

const autoFixPythonCode = (code, errorText = '', { allowPlots = true } = {}) => {
  let fixed = code || '';
  const numericMetricHelper = [
    'def _autorun_metric(row):',
    '    values = []',
    '    for key, value in row.items():',
    '        if key in {"Student_ID", "Student_Name", "Name", "ID"}:',
    '            continue',
    '        if isinstance(value, (int, float)):',
    '            values.append(float(value))',
    '            continue',
    '        try:',
    '            values.append(float(value))',
    '        except (TypeError, ValueError):',
    '            pass',
    '    return sum(values) / len(values) if values else 0',
    '',
  ].join('\n');

  if (/pd\.DataFrame\s*\(/i.test(fixed)) {
    fixed = fixed.replace(/(?:rows|df)\s*=\s*pd\.DataFrame\s*\([\s\S]*?\)\s*/im, '');
  }

  fixed = fixed.replace(/^\s*(import|from)\s+matplotlib[^\n]*$/gim, '');
  fixed = fixed.replace(/^\s*(import|from)\s+seaborn[^\n]*$/gim, '');
  fixed = fixed.replace(/^\s*plt\.show\(\)\s*$/gim, '');
  fixed = fixed.replace(/^\s*sns\.[^\n]*$/gim, '');

  if (/Do not import matplotlib or seaborn/i.test(errorText)) {
    fixed = fixed.replace(/^\s*(import|from)\s+(matplotlib|seaborn)[^\n]*$/gim, '');
  }

  if (/Do not overwrite runtime dataset variables/i.test(errorText)) {
    fixed = fixed.replace(/^\s*(df|rows|file_name|file_text|df_columns|df_shape|df_head|df_numeric_summary)\s*=.*$/gim, '');
  }

  if (/Invalid element\(s\) received for the 'data' property/i.test(errorText) && /Invalid elements include: \[Figure\(/i.test(errorText)) {
    fixed += '\n\n# Plotly fix: build one figure and add traces, or use make_subplots with add_trace; do not pass Figure objects inside data=[...].\n';
  }

  if (/TypeError: '<' not supported between instances of 'str' and 'int'/i.test(errorText)) {
    fixed = fixed.replace(/row\[(.*?)\]\s*<\s*35/g, 'float(row.get($1, 0) or 0) < 35');
    fixed = fixed.replace(/row\[(.*?)\]\s*>\s*35/g, 'float(row.get($1, 0) or 0) > 35');
  }

  if (/KeyError:\s*'metric_value'/i.test(errorText) || /["']metric_value["']/.test(fixed)) {
    if (!fixed.includes('def _autorun_metric(row):')) {
      fixed = `${numericMetricHelper}${fixed}`;
    }

    fixed = fixed.replace(/\b([A-Za-z_][A-Za-z0-9_]*)\[['"]metric_value['"]\]/g, '_autorun_metric($1)');
    fixed = fixed.replace(/\b([A-Za-z_][A-Za-z0-9_]*)\.get\(\s*['"]metric_value['"]\s*,\s*([^)]+)\)/g, '_autorun_metric($1)');
    fixed = fixed.replace(/Metric Value:\s*\{[^}]*metric_value[^}]*\}/gi, 'Average Score: {_autorun_metric(row):.2f}');
    fixed = fixed.replace(/Metric Value:/g, 'Average Score:');
  }

  if (!/result_markdown\s*=/.test(fixed) && /print\s*\(/.test(fixed)) {
    fixed += '\n\nresult_markdown = stdout_output if "stdout_output" in globals() else ""\n';
  }

  if (!allowPlots) {
    fixed = fixed.replace(/^\s*(import|from)\s+plotly[^\n]*$/gim, '');
    fixed = fixed.replace(/^\s*plotly_figure\s*=.*$/gim, '');
    fixed = fixed.replace(/^\s*fig\.show\(\)\s*$/gim, '');
  }

  if (allowPlots && !/plotly_figure\s*=/.test(fixed) && /chart|plot|bar|line|scatter|histogram|visual/i.test(fixed)) {
    fixed += '\n\nplotly_figure = fig if "fig" in globals() else plotly_figure\n';
  }

  return fixed.trim();
};

const sanitizeExecutionPayload = (payload, { allowPlots = true } = {}) => {
  if (!payload || typeof payload !== 'object') {
    return payload;
  }

  if (allowPlots) {
    return payload;
  }

  return {
    ...payload,
    chart: null,
    charts: [],
    plotly_figure: null,
    plotly_figures: [],
    output: payload.output || 'Visualization output is disabled for this extension. Use Data Visualization Studio for charts.',
  };
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

const buildExecutionSignature = (messageId, datasetName, pythonCode) =>
  `${messageId}::${datasetName}::${pythonCode}`;

/* ---------------- COMPONENT ---------------- */

function Message({ message, user, executionDataset, queryText = '', extensionName = '' }) {
  const isUser = message.role === 'user';
  const [showSources, setShowSources] = useState(null);
  const [imageError, setImageError] = useState(false);
  const [showFilePreviewModal, setShowFilePreviewModal] = useState(false);
  const [executionState, setExecutionState] = useState({
    running: false,
    result: '',
    chart: null,
    charts: [],
    error: '',
    attempts: 0,
    statusSteps: [],
    executedCode: '',
  });
  const autoRunSignatureRef = useRef(null);
  const aiRepairAttemptedRef = useRef(new Set());
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
  const attachmentCsvPreview = parseDelimitedPreview(attachment?.preview_text, attachment?.name, attachment?.type);
  const isCsvLikeAttachment = Boolean(attachmentCsvPreview);
  const pythonCode = extractFirstPythonBlock(message.content);
  const hasComputedAnalysis = Boolean(executionDataset && pythonCode);
  const displayedCode = executionState.executedCode || pythonCode;
  const displayContent = hasComputedAnalysis
    ? stripPythonBlocks(message.content)
    : message.content;
  const shouldHideNarrative = hasComputedAnalysis;

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

  const executionDatasetText = executionDataset?.text || '';
  const executionDatasetName = executionDataset?.name || '';
  const allowPlotlyOutputs = /visualization/i.test(extensionName);
  const executionSignature = pythonCode
    ? buildExecutionSignature(message.id, executionDatasetName, pythonCode)
    : '';
  const persistedExecutionCache = message.metadata?.execution_cache || null;

  useEffect(() => {
    if (message.role !== 'assistant') {
      console.log('[AutoRun] Skipped: message is not assistant', { messageId: message.id });
      return;
    }
    if (!pythonCode) {
      console.log('[AutoRun] Skipped: no python block found', { messageId: message.id });
      return;
    }

    const signature = executionSignature;
    const storageKey = `autorun:${signature}`;
    if (
      persistedExecutionCache &&
      (
        !persistedExecutionCache.signature ||
        persistedExecutionCache.signature === signature
      )
    ) {
      console.log('[AutoRun] Using persisted backend execution cache', {
        messageId: message.id,
        signature: persistedExecutionCache.signature || signature,
      });
      const sanitizedPersistedCache = sanitizeExecutionPayload(persistedExecutionCache, {
        allowPlots: allowPlotlyOutputs,
      });
      setExecutionState({
        running: false,
        result: sanitizedPersistedCache.result || '',
        chart: sanitizedPersistedCache.chart || sanitizedPersistedCache.plotly_figure || null,
        charts: sanitizedPersistedCache.charts || sanitizedPersistedCache.plotly_figures || [],
        error: sanitizedPersistedCache.error || '',
        attempts: sanitizedPersistedCache.attempts || 1,
        statusSteps: [],
        executedCode: sanitizedPersistedCache.executedCode || pythonCode,
      });
      autoRunSignatureRef.current = signature;
      window.sessionStorage.setItem(storageKey, JSON.stringify(sanitizedPersistedCache));
      return;
    }

    if (!executionDatasetText) {
      console.log('[AutoRun] Skipped: no execution dataset available', { messageId: message.id });
      return;
    }

    const cached = window.sessionStorage.getItem(storageKey);
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        const sanitizedCached = sanitizeExecutionPayload(parsed, {
          allowPlots: allowPlotlyOutputs,
        });
        console.log('[AutoRun] Using sessionStorage execution cache', {
          messageId: message.id,
          signature,
        });
        setExecutionState({
          running: false,
          result: sanitizedCached.result || '',
          chart: sanitizedCached.chart || sanitizedCached.plotly_figure || null,
          charts: sanitizedCached.charts || sanitizedCached.plotly_figures || [],
          error: sanitizedCached.error || '',
          attempts: sanitizedCached.attempts || 1,
          statusSteps: [],
          executedCode: sanitizedCached.executedCode || pythonCode,
        });
        autoRunSignatureRef.current = signature;
        return;
      } catch {
        window.sessionStorage.removeItem(storageKey);
      }
    }

    if (autoRunSignatureRef.current === signature) {
      console.log('[AutoRun] Skipped: signature already running or handled', {
        messageId: message.id,
        signature,
      });
      return;
    }
    autoRunSignatureRef.current = signature;

    let cancelled = false;

    const executeWithAutoFix = async () => {
      let codeToRun = autoFixPythonCode(pythonCode, '', {
        allowPlots: allowPlotlyOutputs,
      });
      let lastError = '';

      for (let attempt = 1; attempt <= 3; attempt += 1) {
        if (cancelled) return;

        console.log('[AutoRun] Starting attempt', {
          messageId: message.id,
          attempt,
          datasetName: executionDatasetName,
          codePreview: codeToRun.slice(0, 180),
        });

        setExecutionState({
          running: true,
          result: '',
          chart: null,
          charts: [],
          error: '',
          attempts: attempt,
          statusSteps: [{ step: `Starting attempt ${attempt}`, detail: null }],
          executedCode: codeToRun,
        });

        try {
          const output = await runPythonOnDataset({
            code: codeToRun,
            datasetText: executionDatasetText,
            fileName: executionDatasetName,
            onStatus: (status) => {
              if (cancelled) return;
              setExecutionState((prev) => ({
                ...prev,
                running: true,
                attempts: attempt,
                statusSteps: [...prev.statusSteps, status],
              }));
            },
          });
          const normalizedOutput = typeof output === 'string'
            ? { output, plotly_figure: null }
            : output;
          const sanitizedOutput = sanitizeExecutionPayload(normalizedOutput, {
            allowPlots: allowPlotlyOutputs,
          });

          if (cancelled) return;
          console.log('[AutoRun] Execution succeeded', {
            messageId: message.id,
            attempt,
            outputPreview: String(sanitizedOutput?.output || '').slice(0, 180),
          });
          setExecutionState({
            running: false,
            result: sanitizedOutput?.output || '',
            chart: sanitizedOutput?.plotly_figure || null,
            charts: sanitizedOutput?.plotly_figures || [],
            error: '',
            attempts: attempt,
            statusSteps: [],
            executedCode: codeToRun,
          });
          window.sessionStorage.setItem(
            storageKey,
            JSON.stringify({
              signature,
              result: sanitizedOutput?.output || '',
              chart: sanitizedOutput?.plotly_figure || null,
              charts: sanitizedOutput?.plotly_figures || [],
              error: '',
              attempts: attempt,
              executedCode: codeToRun,
            })
          );
          try {
            await api.updateMessageExecutionCache(message.id, {
              signature,
              result: sanitizedOutput?.output || '',
              chart: sanitizedOutput?.plotly_figure || null,
              charts: sanitizedOutput?.plotly_figures || [],
              error: '',
              attempts: attempt,
              executedCode: codeToRun,
            });
          } catch (persistErr) {
            console.warn('[AutoRun] Failed to persist execution cache', {
              messageId: message.id,
              error: persistErr?.message || 'Persist failed.',
            });
          }
          return;
        } catch (err) {
          lastError = err?.message || 'Execution failed.';
          console.warn('[AutoRun] Execution failed, applying fix', {
            messageId: message.id,
            attempt,
            error: lastError,
          });

          let repairedCode = autoFixPythonCode(codeToRun, lastError, {
            allowPlots: allowPlotlyOutputs,
          });
          const aiRepairKey = `${signature}::${attempt}`;

          if (!cancelled && queryText && !aiRepairAttemptedRef.current.has(aiRepairKey)) {
            aiRepairAttemptedRef.current.add(aiRepairKey);
            try {
              console.log('[AutoRun] Requesting AI code repair', {
                messageId: message.id,
                attempt,
                datasetName: executionDatasetName,
              });
              const repairResponse = await api.repairCodeExecution({
                question: queryText,
                code: repairedCode || codeToRun,
                error: lastError,
                traceback: lastError,
                dataset_preview: executionDatasetText.slice(0, 6000),
                file_name: executionDatasetName,
                extension_name: extensionName,
              });

              if (repairResponse?.fixed_code?.trim()) {
                repairedCode = repairResponse.fixed_code.trim();
                console.log('[AutoRun] AI repair received', {
                  messageId: message.id,
                  attempt,
                  codePreview: repairedCode.slice(0, 180),
                });
              }
            } catch (repairErr) {
              console.warn('[AutoRun] AI repair request failed', {
                messageId: message.id,
                attempt,
                error: repairErr?.message || 'Code repair request failed.',
              });
            }
          }

          codeToRun = repairedCode;
        }
      }

      if (!cancelled) {
        console.error('[AutoRun] Execution failed after all attempts', {
          messageId: message.id,
          error: lastError,
        });
        setExecutionState({
          running: false,
          result: '',
          chart: null,
          charts: [],
          error: lastError || 'Automatic execution failed after multiple attempts.',
          attempts: 3,
          statusSteps: [],
          executedCode: codeToRun,
        });
        window.sessionStorage.setItem(
          storageKey,
          JSON.stringify({
            signature,
            result: '',
            chart: null,
            charts: [],
            error: lastError || 'Automatic execution failed after multiple attempts.',
            attempts: 3,
            executedCode: codeToRun,
          })
        );
        try {
          await api.updateMessageExecutionCache(message.id, {
            signature,
            result: '',
            chart: null,
            charts: [],
            error: lastError || 'Automatic execution failed after multiple attempts.',
            attempts: 3,
            executedCode: codeToRun,
          });
        } catch (persistErr) {
          console.warn('[AutoRun] Failed to persist execution cache', {
            messageId: message.id,
            error: persistErr?.message || 'Persist failed.',
          });
        }
      }
    };

    executeWithAutoFix();

    return () => {
      cancelled = true;
      if (autoRunSignatureRef.current === signature) {
        autoRunSignatureRef.current = null;
      }
    };
  }, [message.id, message.role, message.content, executionDatasetText, executionDatasetName, executionSignature, persistedExecutionCache]);

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
        {attachment && (
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

            {isCsvLikeAttachment && (
              <div className="message-file-inline-preview csv" onClick={() => setShowFilePreviewModal(true)}>
                <CsvPreviewTable preview={attachmentCsvPreview} compact />
              </div>
            )}
          </div>
        )}

        {/* Code-viewer for raw JSON and for fenced markdown code blocks */}
        {isRawJson(message.content) ? (
          <JsonCodeViewer code={message.content} language="json" fileBaseName="co_po_mapping" />
        ) : (
          <>
            {!shouldHideNarrative && displayContent ? (
              <div
                className="message-text"
                onClick={handleDelegatedCodeActions}
                dangerouslySetInnerHTML={{
                  __html: renderMarkdown(displayContent)
                }}
              />
            ) : null}

            {!isUser && hasComputedAnalysis && displayedCode && (
              <details className="generated-code-details" onClick={handleDelegatedCodeActions}>
                <summary>Show generated analysis code</summary>
                <div
                  className="generated-code-content"
                  dangerouslySetInnerHTML={{
                    __html: renderMarkdown(`\`\`\`python\n${displayedCode}\n\`\`\``)
                  }}
                />
              </details>
            )}
          </>
        )}

        {executionState.running && (
          <div className="execution-panel execution-panel-running">
            <div className="execution-status-current">
              {executionState.statusSteps[executionState.statusSteps.length - 1]?.step || 'Running Python on uploaded dataset automatically...'}
            </div>
            {executionState.statusSteps.length > 0 && (
              <div className="execution-status-log">
                {executionState.statusSteps.map((status, index) => (
                  <div key={`${status.timestamp || status.step}-${index}`} className="execution-status-line">
                    <span className="execution-status-bullet">•</span>
                    <span className="execution-status-text">{status.step}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {executionState.error && (
          <div className="execution-panel execution-panel-error">
            <strong>Execution Error</strong>
            <pre>{executionState.error}</pre>
          </div>
        )}

        {(executionState.chart || executionState.charts.length || executionState.result) && !executionState.running && !executionState.error && (
          <div className="execution-result-wrapper">
            <div className="execution-result-badge">Computed from uploaded dataset</div>
            {executionState.charts.length > 0 ? (
              <div className="execution-charts-stack">
                {executionState.charts.map((figure, index) => (
                  <div key={index} className="execution-chart-wrapper">
                    <PlotlyChart figure={figure} />
                  </div>
                ))}
              </div>
            ) : executionState.chart ? (
              <div className="execution-chart-wrapper">
                <PlotlyChart figure={executionState.chart} />
              </div>
            ) : null}
            {!executionState.chart && executionState.charts.length === 0 && executionState.result ? (
              <div
                className="message-text execution-result-text"
                dangerouslySetInnerHTML={{ __html: renderMarkdown(maybeFormatExecutionOutput(executionState.result)) }}
              />
            ) : null}
          </div>
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

                {attachmentKind === 'text' && attachment?.preview_text && isCsvLikeAttachment && (
                  <CsvPreviewTable preview={attachmentCsvPreview} />
                )}

                {attachmentKind === 'text' && attachment?.preview_text && !isCsvLikeAttachment && (
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
