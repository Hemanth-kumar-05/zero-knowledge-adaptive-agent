import React, { useEffect, useMemo, useState } from 'react';
import './ValidationDashboard.css';

const metricDefinitions = {
  personalization_accuracy: {
    label: 'Personalization Accuracy',
    formula: 'correct personalized responses / personalization test cases',
    note: 'Did the response obey stored user preferences or remembered context when expected?',
    kind: 'rate',
  },
  zero_knowledge_compliance: {
    label: 'Zero-Knowledge Compliance',
    formula: 'neutral responses without prior learning / zero-knowledge cases',
    note: 'Did a fresh user stay free from invented personalization?',
    kind: 'rate',
  },
  user_memory_relevance_score: {
    label: 'User Memory Relevance',
    formula: 'sum memory relevance scores / memory-enabled cases',
    note: '0 = irrelevant, 1 = partially relevant, 2 = clearly useful.',
    kind: 'score2',
  },
  grounded_response_fidelity: {
    label: 'Grounded Response Fidelity',
    formula: 'fully grounded responses / grounded-answer cases',
    note: 'Did the generated answer remain faithful to retrieved source chunks?',
    kind: 'rate',
  },
  contradiction_resolution_rate: {
    label: 'Contradiction Resolution',
    formula: 'correctly handled contradiction cases / contradiction cases',
    note: 'Did policy conflicts and update claims route safely?',
    kind: 'rate',
  },
  knowledge_evolution_stability: {
    label: 'Knowledge Evolution Stability',
    formula: 'stable knowledge-evolution runs / knowledge-evolution cases',
    note: 'Did claim detection, proof flow, ticketing, chunk status, and audit behavior remain stable?',
    kind: 'rate',
  },
  end_to_end_task_success_rate: {
    label: 'End-to-End Task Success',
    formula: 'successful validated scenarios / total benchmark scenarios',
    note: 'Overall scenario success after retrieval, generation, personalization, memory, refusal, and workflow checks.',
    kind: 'rate',
  },
  hallucination_rate: {
    label: 'Hallucination Rate',
    formula: 'hallucinated completed responses / completed turns',
    note: 'Lower is better. GPT flags claims unsupported by RAG evidence.',
    kind: 'inverseRate',
  },
  context_sufficiency_rate: {
    label: 'Context Sufficiency',
    formula: 'turns with sufficient retrieved context / completed turns',
    note: 'Did retrieval provide enough evidence for the expected answer?',
    kind: 'rate',
  },
  retry_recovery_rate: {
    label: 'Retry Recovery',
    formula: 'completed retried turns / turns requiring retry',
    note: 'How often a retry recovered from a provider or application retry condition.',
    kind: 'rate',
  },
  refusal_correctness_rate: {
    label: 'Refusal Correctness',
    formula: 'correct refusals / refusal-required cases',
    note: 'Did the assistant refuse out-of-scope requests instead of inventing?',
    kind: 'rate',
  },
  policy_claim_false_alarm_rate: {
    label: 'Policy Claim False Alarm',
    formula: 'false policy-claim triggers / non-claim cases',
    note: 'Lower is better. Normal questions should not trigger policy-update workflows.',
    kind: 'inverseRate',
  },
};

const scoreFields = [
  ['groundedness_score', 'Groundedness'],
  ['answer_relevance_score', 'Answer relevance'],
  ['completeness_score', 'Completeness'],
  ['context_sufficiency_score', 'Context sufficiency'],
];

const workflowSteps = [
  'Benchmark prompt is sent to the real backend',
  'RAG retrieves active ChromaDB source chunks',
  'Groq generates the student-facing answer',
  'The harness records sources, response, latency, memory, preferences, and workflow metadata',
  'GPT-4.1 mini receives the trace and returns strict JSON scores',
  'Rule checks and GPT scores are aggregated into report percentages',
];

function clamp(value, min = 0, max = 100) {
  return Math.max(min, Math.min(max, value));
}

function toPercent(metricKey, value) {
  if (value == null) return null;
  const definition = metricDefinitions[metricKey];
  if (definition?.kind === 'score2') return (value / 2) * 100;
  return value <= 1 ? value * 100 : value;
}

function formatMetric(metricKey, value) {
  if (value == null) return 'n/a';
  const definition = metricDefinitions[metricKey];
  if (definition?.kind === 'score2') return `${Number(value).toFixed(2)} / 2`;
  const percent = toPercent(metricKey, value);
  return `${Number(percent).toFixed(percent % 1 === 0 ? 0 : 2)}%`;
}

function average(values) {
  const usable = values.filter((value) => typeof value === 'number' && !Number.isNaN(value));
  if (!usable.length) return null;
  return usable.reduce((sum, value) => sum + value, 0) / usable.length;
}

function groupBy(items, getKey) {
  return items.reduce((acc, item) => {
    const key = getKey(item);
    acc[key] = acc[key] || [];
    acc[key].push(item);
    return acc;
  }, {});
}

function getAnswer(record) {
  return record?.execution?.response?.answer || '(no answer captured)';
}

function getSources(record) {
  return record?.execution?.response?.sources || [];
}

function verdictOf(record) {
  return record?.judge?.verdict || 'unknown';
}

function isCompleted(record) {
  return record?.execution?.final_status === 'completed';
}

function loadJson(path) {
  return fetch(path).then((response) => {
    if (!response.ok) {
      throw new Error(`Unable to load ${path}`);
    }
    return response.json();
  });
}

function ToggleButton({ onClick }) {
  return (
    <button className="validation-sidebar-toggle" onClick={onClick} title="Toggle sidebar">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="3" y1="12" x2="21" y2="12"></line>
        <line x1="3" y1="6" x2="21" y2="6"></line>
        <line x1="3" y1="18" x2="21" y2="18"></line>
      </svg>
    </button>
  );
}

function Donut({ percent, inverse = false, label }) {
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const value = clamp(percent || 0);
  const offset = circumference - (value / 100) * circumference;
  const color = inverse
    ? value <= 5 ? '#10a37f' : value <= 20 ? '#f59e0b' : '#ef4444'
    : value >= 85 ? '#10a37f' : value >= 65 ? '#f59e0b' : '#ef4444';

  return (
    <svg className="validation-donut" viewBox="0 0 96 96" aria-label={label}>
      <circle className="validation-donut-track" cx="48" cy="48" r={radius} />
      <circle
        className="validation-donut-value"
        cx="48"
        cy="48"
        r={radius}
        stroke={color}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
      />
      <text x="48" y="51" textAnchor="middle" className="validation-donut-text">
        {Math.round(value)}
      </text>
    </svg>
  );
}

function HelpTip({ text }) {
  return (
    <span className="help-tip" tabIndex="0" aria-label={text}>
      ?
      <span>{text}</span>
    </span>
  );
}

function MiniLegend() {
  return (
    <div className="visual-legend" aria-label="Dashboard legend">
      <span><i className="legend-dot good"></i>Strong</span>
      <span><i className="legend-dot warn"></i>Watch</span>
      <span><i className="legend-dot bad"></i>Fail</span>
      <span><i className="legend-line"></i>Trend</span>
    </div>
  );
}

function MetricThermometer({ value, inverse }) {
  const percent = clamp(value || 0);
  const marker = inverse ? 100 - percent : percent;
  return (
    <div className={`metric-thermometer ${inverse ? 'inverse' : ''}`} title={inverse ? 'Lower value is better' : 'Higher value is better'}>
      <span style={{ '--metric-fill': `${clamp(marker, 0, 100)}%` }}></span>
    </div>
  );
}

function VisualPipeline() {
  return (
    <div className="visual-pipeline" aria-label="Validation workflow animation">
      {[
        ['Query', 'User prompt'],
        ['RAG', 'Sources'],
        ['Groq', 'Answer'],
        ['Trace', 'Metadata'],
        ['GPT', 'Judge'],
        ['Score', 'Metrics'],
      ].map(([label, sub], index) => (
        <div className="flow-node" key={label} style={{ animationDelay: `${index * 120}ms` }}>
          <strong>{label}</strong>
          <span>{sub}</span>
        </div>
      ))}
    </div>
  );
}

function BarRow({ label, value, max, color = '#10a37f', suffix = '' }) {
  const width = max > 0 ? clamp((value / max) * 100) : 0;
  return (
    <div className="bar-row">
      <div className="bar-row-label">
        <span>{label}</span>
        <strong>{typeof value === 'number' ? `${Number(value).toFixed(value % 1 === 0 ? 0 : 1)}${suffix}` : value}</strong>
      </div>
      <div className="bar-track">
        <div style={{ width: `${width}%`, backgroundColor: color }}></div>
      </div>
    </div>
  );
}

function Sparkline({ points }) {
  const width = 1100;
  const height = 340;
  const margin = { left: 70, right: 40, top: 20, bottom: 50 };
  const chartWidth = width - margin.left - margin.right;
  const chartHeight = height - margin.top - margin.bottom;
  
  const max = Math.max(...points.map((point) => point.value), 1);
  const step = points.length > 1 ? chartWidth / (points.length - 1) : chartWidth;
  
  const polyline = points
    .map((point, index) => {
      const x = margin.left + index * step;
      const y = margin.top + chartHeight - (point.value / max) * chartHeight;
      return `${x},${y}`;
    })
    .join(' ');

  // Generate Y-axis gridlines and labels
  const ySteps = 4;
  const yGridlines = Array.from({ length: ySteps + 1 }, (_, i) => {
    const ratio = i / ySteps;
    const value = max * (1 - ratio);
    const y = margin.top + ratio * chartHeight;
    return { y, value };
  });

  const [hoveredIndex, setHoveredIndex] = React.useState(null);
  const hoveredPoint = hoveredIndex !== null ? points[hoveredIndex] : null;
  
  const getPointCoords = (index) => ({
    x: margin.left + index * step,
    y: margin.top + chartHeight - (points[index].value / max) * chartHeight,
  });

  return (
    <div className="sparkline-container">
      <svg className="latency-chart" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        {/* Y-axis gridlines */}
        {yGridlines.map((grid, i) => (
          <line key={`grid-${i}`} x1={margin.left} y1={grid.y} x2={width - margin.right} y2={grid.y} 
                className="gridline" stroke="#2f2f2f" strokeWidth="1" strokeDasharray="2,4" />
        ))}
        
        {/* Y-axis labels */}
        {yGridlines.map((grid, i) => (
          <text key={`label-${i}`} x={margin.left - 10} y={grid.y + 4} textAnchor="end" 
                className="axis-label" fontSize="11" fill="#888">
            {grid.value.toFixed(1)}s
          </text>
        ))}

        {/* Y-axis line */}
        <line x1={margin.left} y1={margin.top} x2={margin.left} y2={margin.top + chartHeight} 
              stroke="#444" strokeWidth="1" />
        
        {/* X-axis line */}
        <line x1={margin.left} y1={margin.top + chartHeight} x2={width - margin.right} y2={margin.top + chartHeight} 
              stroke="#444" strokeWidth="1" />

        {/* Main polyline */}
        <polyline className="latency-line" points={polyline} fill="none" stroke="#10a37f" strokeWidth="3" strokeLinejoin="round" />
        
        {/* Data points - all of them, not filtered */}
        {points.map((point, index) => {
          const coords = getPointCoords(index);
          return (
            <circle
              key={`${point.id}-${index}`}
              cx={coords.x}
              cy={coords.y}
              r="4"
              fill={point.failed ? '#ef4444' : '#7bf0cb'}
              className="data-point"
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
              style={{ cursor: 'pointer', transition: 'r 0.1s' }}
            />
          );
        })}

        {/* Tooltip for hovered point */}
        {hoveredPoint && hoveredIndex !== null && (
          <g>
            <circle {...getPointCoords(hoveredIndex)} r="6" fill="none" stroke="#10a37f" strokeWidth="2" />
            <rect x={getPointCoords(hoveredIndex).x - 50} y={getPointCoords(hoveredIndex).y - 35} 
                  width="100" height="28" fill="#101615" stroke="#10a37f" strokeWidth="1" rx="4" />
            <text x={getPointCoords(hoveredIndex).x} y={getPointCoords(hoveredIndex).y - 18} textAnchor="middle" 
                  className="tooltip-text" fontSize="12" fill="#7bf0cb" fontWeight="600">
              {hoveredPoint.value.toFixed(2)}s
            </text>
            <text x={getPointCoords(hoveredIndex).x} y={getPointCoords(hoveredIndex).y - 8} textAnchor="middle" 
                  className="tooltip-text" fontSize="11" fill="#888">
              Turn {hoveredIndex + 1}
            </text>
          </g>
        )}
      </svg>
      
      {/* Inference below chart */}
      <div className="sparkline-inference">
        {(() => {
          const rejected = points.filter(p => p.failed).length;
          const accepted = points.filter(p => !p.failed).length;
          const avgLatency = (points.reduce((sum, p) => sum + p.value, 0) / points.length).toFixed(1);
          const maxLatency = Math.max(...points.map(p => p.value));
          const rejectionRate = ((rejected / points.length) * 100).toFixed(0);
          const highLatencyRejects = points.filter(p => p.failed && p.value > maxLatency * 0.7).length;
          
          if (highLatencyRejects > rejected * 0.5) {
            return `High latency correlates with rejections. ${rejectionRate}% rejection rate. Peak ${maxLatency.toFixed(1)}s suggests timeouts or complex retrievals.`;
          } else if (rejected > accepted) {
            return `${rejectionRate}% rejection rate with avg latency ${avgLatency}s. Quality issues beyond latency detected.`;
          } else {
            return `Stable latency profile: avg ${avgLatency}s, peak ${maxLatency.toFixed(1)}s. ${rejectionRate}% rejection rate suggests selective edge cases.`;
          }
        })()}
      </div>
    </div>
  );
}

function ScoreRadar({ scores }) {
  const size = 220;
  const center = size / 2;
  const radius = 78;
  const [hoveredAxis, setHoveredAxis] = React.useState(null);
  
  const axes = scores.map((score, index) => {
    const angle = (Math.PI * 2 * index) / scores.length - Math.PI / 2;
    const outerX = center + Math.cos(angle) * radius;
    const outerY = center + Math.sin(angle) * radius;
    const valueRadius = (score.value / 5) * radius;
    const valueX = center + Math.cos(angle) * valueRadius;
    const valueY = center + Math.sin(angle) * valueRadius;
    const labelX = center + Math.cos(angle) * (radius + 28);
    const labelY = center + Math.sin(angle) * (radius + 28);
    return { ...score, outerX, outerY, valueX, valueY, labelX, labelY };
  });
  const polygon = axes.map((axis) => `${axis.valueX},${axis.valueY}`).join(' ');

  return (
    <svg className="score-radar" viewBox={`0 0 ${size} ${size}`}>
      {[0.25, 0.5, 0.75, 1].map((ring) => {
        const r = radius * ring;
        const points = scores.map((_, index) => {
          const angle = (Math.PI * 2 * index) / scores.length - Math.PI / 2;
          return `${center + Math.cos(angle) * r},${center + Math.sin(angle) * r}`;
        }).join(' ');
        return <polygon key={ring} points={points} className="radar-ring" />;
      })}
      {axes.map((axis) => (
        <g key={axis.label}>
          <line x1={center} y1={center} x2={axis.outerX} y2={axis.outerY} className="radar-axis" />
          <text x={axis.labelX} y={axis.labelY} textAnchor="middle" className="radar-label">{axis.shortLabel || axis.label}</text>
        </g>
      ))}
      <polygon points={polygon} className="radar-area" />
      {axes.map((axis) => (
        <circle
          key={`${axis.label}-dot`}
          cx={axis.valueX}
          cy={axis.valueY}
          r={hoveredAxis === axis.label ? "6" : "4"}
          className={`radar-dot ${hoveredAxis === axis.label ? 'hovered' : ''}`}
          onMouseEnter={() => setHoveredAxis(axis.label)}
          onMouseLeave={() => setHoveredAxis(null)}
          style={{ cursor: 'pointer', transition: 'r 0.1s ease' }}
        />
      ))}
      
      {/* Tooltip for hovered axis */}
      {hoveredAxis && (() => {
        const hovered = axes.find(ax => ax.label === hoveredAxis);
        if (!hovered) return null;
        return (
          <g>
            <circle cx={hovered.valueX} cy={hovered.valueY} r="8" fill="none" stroke="#10a37f" strokeWidth="1.5" opacity="0.6" />
            <rect x={hovered.valueX - 35} y={hovered.valueY - 28} width="70" height="24" fill="#101615" stroke="#10a37f" strokeWidth="1" rx="3" />
            <text x={hovered.valueX} y={hovered.valueY - 15} textAnchor="middle" fontSize="11" fill="#7bf0cb" fontWeight="600">
              {hovered.label}
            </text>
            <text x={hovered.valueX} y={hovered.valueY - 5} textAnchor="middle" fontSize="10" fill="#10a37f" fontWeight="700">
              {hovered.value.toFixed(2)}/5
            </text>
          </g>
        );
      })()}
    </svg>
  );
}

function OutcomeFunnel({ total, completed, accepted, rejected }) {
  const rows = [
    { label: 'Total turns', value: total, color: '#7bf0cb' },
    { label: 'Completed API turns', value: completed, color: '#10a37f' },
    { label: 'Accepted by GPT judge', value: accepted, color: '#22c55e' },
    { label: 'Rejected for review', value: rejected, color: '#ef4444' },
  ];
  const max = Math.max(total || 1, ...rows.map((row) => row.value || 0));

  return (
    <div className="outcome-funnel">
      {rows.map((row, index) => (
        <div className="funnel-row" key={row.label}>
          <span>{row.label}</span>
          <div className="funnel-shape" style={{ width: `${Math.max(18, (row.value / max) * 100)}%`, backgroundColor: row.color }}>
            <strong>{row.value}</strong>
          </div>
          {index < rows.length - 1 && <i></i>}
        </div>
      ))}
    </div>
  );
}

function SelectedTurnPlot({ title, record }) {
  if (!record) return null;
  const sources = getSources(record).slice(0, 5);
  const verdict = verdictOf(record);
  const sourceValues = sources.map((source) => ({
    label: source.section || source.doc_id,
    value: Number(source.similarity || 0),
  }));
  const maxSimilarity = Math.max(...sourceValues.map((source) => source.value), 1);
  const turnScores = scoreFields.map(([field, label]) => ({
    label,
    value: record?.judge?.[field] || 0,
  }));

  return (
    <div className="turn-plot-card">
      <div className="turn-plot-header">
        <div>
          <span className="section-label">{title}</span>
          <h2>{record.benchmark_session_id} / {record.turn_id}</h2>
        </div>
        <strong className={`verdict-badge ${verdict}`}>{verdict}</strong>
      </div>

      <div className="turn-plot-grid">
        <div className="turn-question-strip">
          <span>User query</span>
          <strong>{record.question}</strong>
          <p>{getAnswer(record)}</p>
        </div>
        <div className="turn-score-bars">
          {turnScores.map((score) => (
            <div className="turn-score-row" key={score.label}>
              <span>{score.label}</span>
              <div><i style={{ width: `${(score.value / 5) * 100}%` }}></i></div>
              <strong>{score.value}/5</strong>
            </div>
          ))}
        </div>
        <div className="source-plot">
          <span>Retrieved evidence similarity</span>
          {sourceValues.map((source) => (
            <div className="source-plot-row" key={source.label} title={source.label}>
              <label>{source.label}</label>
              <div><i style={{ width: `${Math.max(8, (source.value / maxSimilarity) * 100)}%` }}></i></div>
              <strong>{source.value.toFixed(2)}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function SessionTurnHeatmap({ sessions, onSelectTurn }) {
  return (
    <div className="turn-graph">
      {sessions.map((session) => (
        <div className="turn-graph-row" key={session.sessionId}>
          <div className="turn-graph-label">
            <strong>{session.sessionId}</strong>
            <span>{Math.round((session.accepted / session.total) * 100)}%</span>
          </div>
          <div className="turn-graph-line">
            {session.records.map((record) => {
              const groundedness = record?.judge?.groundedness_score || 0;
              const accepted = verdictOf(record) === 'accept';
              return (
                <button
                  key={`${record.benchmark_session_id}-${record.turn_id}`}
                  className={`turn-point ${accepted ? 'accepted' : 'rejected'}`}
                  style={{ '--score': groundedness / 5, '--y': `${100 - (groundedness / 5) * 100}%` }}
                  onClick={() => onSelectTurn(`${record.benchmark_session_id}-${record.turn_id}`)}
                  title={`${record.benchmark_session_id} ${record.turn_id}: ${verdictOf(record)}, groundedness ${groundedness}/5`}
                >
                  {record.turn_id.replace('T', '')}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

function TraceInspector({ record }) {
  if (!record) return null;
  const sources = getSources(record);

  const scoreSummary = scoreFields.map(([field, label]) => ({
    label,
    value: record?.judge?.[field] || 0,
  }));

  return (
    <article className="trace-inspector">
      <div className="trace-inspector-head">
        <div>
          <span>{record.benchmark_session_id} / {record.turn_id}</span>
          <h3>{record.objective}</h3>
        </div>
        <strong className={`verdict-badge ${verdictOf(record)}`}>{verdictOf(record)}</strong>
      </div>

      <div className="trace-flow">
        <div className="trace-stage">
          <span>1</span>
          <label>User Query</label>
          <p>{record.question}</p>
        </div>
        <div className="trace-stage">
          <span>2</span>
          <label>Groq + RAG Answer</label>
          <p>{getAnswer(record)}</p>
        </div>
        <div className="trace-stage verdict-stage">
          <span>3</span>
          <label>GPT Verdict</label>
          <strong className={`verdict-badge ${verdictOf(record)}`}>{verdictOf(record)}</strong>
          <p>{record?.judge?.reasoning || 'No validator reasoning captured.'}</p>
        </div>
      </div>

      <div className="score-strip">
        {scoreSummary.map((score) => (
          <div className="score-chip" key={score.label} title={`${score.label}: ${score.value}/5`}>
            <span>{score.label}</span>
            <strong>{score.value}/5</strong>
            <div><i style={{ width: `${(score.value / 5) * 100}%` }}></i></div>
          </div>
        ))}
      </div>

      <div className="tag-wrap compact-tags">
        {(record.metric_tags || []).map((tag) => <span key={tag}>{tag}</span>)}
      </div>

      <div className="source-grid">
        {sources.slice(0, 5).map((source) => (
          <div className="source-card" key={`${source.id}-${source.section}`}>
            <span>{source.doc_id}</span>
            <strong>{source.section}</strong>
            <p>{String(source.text || '').slice(0, 230)}{String(source.text || '').length > 230 ? '...' : ''}</p>
          </div>
        ))}
      </div>

      <div className="trace-two-column">
        <details className="trace-panel validator-json">
          <summary>GPT Validator JSON</summary>
          <pre>{JSON.stringify(record.judge || {}, null, 2)}</pre>
        </details>
        <details className="trace-panel validator-json">
          <summary>Rule Checks</summary>
          <pre>{JSON.stringify(record.rule_checks || {}, null, 2)}</pre>
        </details>
      </div>
    </article>
  );
}

function ValidationDashboard({ onToggleSidebar }) {
  const [summary, setSummary] = useState(null);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [verdictFilter, setVerdictFilter] = useState('all');
  const [tagFilter, setTagFilter] = useState('all');
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      loadJson('/validation-data/application_validation_summary.json'),
      loadJson('/validation-data/application_validation_runs.json'),
    ])
      .then(([summaryData, runData]) => {
        if (cancelled) return;
        setSummary(summaryData);
        setRuns(Array.isArray(runData) ? runData : []);
        const firstRejected = Array.isArray(runData) ? runData.find((record) => verdictOf(record) === 'reject') : null;
        setSelectedId(firstRejected ? `${firstRejected.benchmark_session_id}-${firstRejected.turn_id}` : null);
        setError(null);
      })
      .catch((loadError) => {
        if (cancelled) return;
        setError(loadError.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const derived = useMemo(() => {
    const completed = runs.filter(isCompleted);
    const accepted = runs.filter((record) => verdictOf(record) === 'accept');
    const rejected = runs.filter((record) => verdictOf(record) === 'reject');
    const sessionGroups = groupBy(runs, (record) => record.benchmark_session_id);
    const sessionStats = Object.entries(sessionGroups).map(([sessionId, records]) => ({
      sessionId,
      records,
      total: records.length,
      accepted: records.filter((record) => verdictOf(record) === 'accept').length,
      rejected: records.filter((record) => verdictOf(record) === 'reject').length,
      avgLatency: average(records.map((record) => record.execution?.latency_ms || 0)) || 0,
      avgGroundedness: average(records.map((record) => record.judge?.groundedness_score)) || 0,
    }));

    const allTags = Array.from(new Set(runs.flatMap((record) => record.metric_tags || []))).sort();
    const tagStats = allTags.map((tag) => {
      const records = runs.filter((record) => (record.metric_tags || []).includes(tag));
      return {
        tag,
        total: records.length,
        successRate: records.length ? (records.filter((record) => verdictOf(record) === 'accept').length / records.length) * 100 : 0,
      };
    }).sort((a, b) => b.total - a.total);

    const scoreAverages = scoreFields.map(([field, label]) => ({
      label,
      shortLabel: label.split(' ')[0],
      value: average(completed.map((record) => record.judge?.[field])) || 0,
    }));

    const sourceCounts = {};
    completed.forEach((record) => {
      getSources(record).forEach((source) => {
        if (!source.doc_id) return;
        sourceCounts[source.doc_id] = (sourceCounts[source.doc_id] || 0) + 1;
      });
    });
    const topSources = Object.entries(sourceCounts)
      .map(([docId, count]) => ({ docId, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8);

    const failureCategories = Object.entries(summary?.failure_categories || {})
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value);

    const latencyPoints = completed.map((record, index) => ({
      id: `${record.benchmark_session_id}-${record.turn_id}`,
      value: (record.execution?.latency_ms || 0) / 1000,
      failed: verdictOf(record) !== 'accept',
      index,
    }));

    return {
      completed,
      accepted,
      rejected,
      sessionStats,
      tagStats,
      scoreAverages,
      topSources,
      failureCategories,
      latencyPoints,
      allTags,
    };
  }, [runs, summary]);

  const selectedRecord = useMemo(() => {
    if (!runs.length) return null;
    return runs.find((record) => `${record.benchmark_session_id}-${record.turn_id}` === selectedId) || runs[0];
  }, [runs, selectedId]);

  const sampleRecords = useMemo(() => {
    const accepted = runs.find((record) => verdictOf(record) === 'accept' && record.expected_behaviors?.expects_grounded_answer) ||
      runs.find((record) => verdictOf(record) === 'accept');
    const rejected = runs.find((record) => verdictOf(record) === 'reject') ||
      runs.find((record) => verdictOf(record) !== 'accept');
    return { accepted, rejected };
  }, [runs]);

  const filteredRuns = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    return runs.filter((record) => {
      const verdictMatch = verdictFilter === 'all' || verdictOf(record) === verdictFilter;
      const tagMatch = tagFilter === 'all' || (record.metric_tags || []).includes(tagFilter);
      const searchText = `${record.benchmark_session_id} ${record.turn_id} ${record.question} ${record.objective} ${getAnswer(record)}`.toLowerCase();
      return verdictMatch && tagMatch && (!normalized || searchText.includes(normalized));
    });
  }, [runs, search, verdictFilter, tagFilter]);

  if (loading) {
    return (
      <div className="validation-page">
        <header className="validation-header">
          <ToggleButton onClick={onToggleSidebar} />
          <div className="validation-title-block">
            <span className="validation-eyebrow">Final review evidence</span>
            <h1>Validation Dashboard</h1>
          </div>
        </header>
        <div className="validation-loading">Loading integrated validation report...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="validation-page">
        <header className="validation-header">
          <ToggleButton onClick={onToggleSidebar} />
          <div className="validation-title-block">
            <span className="validation-eyebrow">Final review evidence</span>
            <h1>Validation Dashboard</h1>
          </div>
        </header>
        <div className="validation-loading error">{error}</div>
      </div>
    );
  }

  const metrics = summary?.metrics || {};
  const maxFailure = Math.max(...derived.failureCategories.map((item) => item.value), 1);
  const maxTagTotal = Math.max(...derived.tagStats.map((item) => item.total), 1);
  const maxSourceCount = Math.max(...derived.topSources.map((item) => item.count), 1);
  const maxScore = 5;

  return (
    <div className="validation-page">
      <header className="validation-header">
        <ToggleButton onClick={onToggleSidebar} />
        <div className="validation-title-block">
          <h1>Validation Dashboard</h1>
        </div>
        <div className="validation-model-badge">
          <span>Validator</span>
          <strong>{summary?.run_metadata?.validator_model || 'gpt-4.1-mini'}</strong>
        </div>
      </header>

      <main className="validation-content">
        <section className="validation-hero-grid">
          <div className="validation-method-panel">
            <div className="method-visual-head">
              <div>
                <div className="section-label">Validation flow</div>
                <h2>GPT judges the trace, not vibes.</h2>
              </div>
              <HelpTip text="The validator receives the original query, retrieved RAG chunks, generated answer, expected benchmark behavior, deterministic rule checks, and workflow metadata." />
            </div>
            <VisualPipeline />
            {/* <div className="flow-caption compact-flow-caption">
              <span>Real backend</span>
              <span>Real retrieval</span>
              <span>Separate judge</span>
            </div> */}
          </div>

          <div className="validation-run-card">
            <div className="section-label">Integrated report size</div>
            <div className="turn-count">{summary?.total_turns || runs.length}</div>
            <p>turns loaded from integrated JSON</p>
            <div className="completion-meter">
              <div style={{ width: `${((summary?.completed_turns || 0) / (summary?.total_turns || 1)) * 100}%` }}></div>
            </div>
            <div className="run-stats">
              <span><strong>{derived.accepted.length}</strong> accepted</span>
              <span><strong>{derived.rejected.length}</strong> rejected</span>
              <span><strong>{Math.round((summary?.average_latency_ms || 0) / 1000)}s</strong> average latency</span>
              <span><strong>{Math.round((summary?.p95_latency_ms || 0) / 1000)}s</strong> p95 latency</span>
            </div>
          </div>
        </section>

        <section className="validation-section sample-comparison-grid">
          <SelectedTurnPlot title="Accepted sample" record={sampleRecords.accepted} />
          <SelectedTurnPlot title="Rejected sample" record={sampleRecords.rejected} />
        </section>

        <section className="validation-section visual-story-grid">
          <article className="validation-card compact-chart-card">
            <div className="section-label">Outcome funnel</div>
            <h2>From run to verdict</h2>
            <OutcomeFunnel
              total={summary?.total_turns || runs.length}
              completed={summary?.completed_turns || derived.completed.length}
              accepted={derived.accepted.length}
              rejected={derived.rejected.length}
            />
          </article>
          <article className="validation-card compact-chart-card">
            <div className="section-label">Validator shape</div>
            <h2>Quality radar</h2>
            <ScoreRadar scores={derived.scoreAverages} />
          </article>
        </section>

        {/* <section className="validation-section">
          <div className="validation-section-heading">
            <div>
              <span className="section-label">Turn-level graph</span>
              <h2>Groundedness path per session</h2>
            </div>
            <p>Each point is one turn. Green means accepted, red means rejected, vertical position shows groundedness.</p>
          </div>
          <article className="validation-card">
            <SessionTurnHeatmap sessions={derived.sessionStats} onSelectTurn={setSelectedId} />
          </article>
        </section> */}

        <section className="validation-section">
          <div className="validation-section-heading">
            <div>
              <span className="section-label">Metric results and formulas</span>
              <h2>Metric board</h2>
            </div>
            <p>Hover the ? icons for formula and meaning.</p>
          </div>
          <div className="metric-grid wide">
            {Object.entries(metrics).map(([key, value]) => {
              const definition = metricDefinitions[key] || { label: key, formula: 'reported by validation harness', note: '', kind: 'rate' };
              const percent = toPercent(key, value);
              return (
                <article className="metric-card" key={key}>
                  <Donut percent={percent} inverse={definition.kind === 'inverseRate'} label={definition.label} />
                  <div className="metric-copy">
                    <div className="metric-topline">
                      <h3>{definition.label} <HelpTip text={`${definition.formula}. ${definition.note}`} /></h3>
                      <strong>{formatMetric(key, value)}</strong>
                    </div>
                    <MetricThermometer percent={percent} value={percent} inverse={definition.kind === 'inverseRate'} />
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section className="validation-section chart-grid">
          <article className="validation-card">
            <div className="section-label">Validator score profile</div>
            <h2>Average GPT scores</h2>
            <div className="bar-stack">
              {derived.scoreAverages.map((item) => (
                <BarRow key={item.label} label={item.label} value={item.value} max={maxScore} color="#10a37f" suffix="/5" />
              ))}
            </div>
          </article>

          <article className="validation-card">
            <div className="section-label">Failure categories</div>
            <h2>Rejected-turn causes</h2>
            <div className="bar-stack">
              {derived.failureCategories.map((item) => (
                <BarRow key={item.label} label={item.label.replace(/_/g, ' ')} value={item.value} max={maxFailure} color={item.label === 'no_error' ? '#10a37f' : '#ef4444'} />
              ))}
            </div>
          </article>

          <article className="validation-card wide-card">
            <div className="section-label">Latency across completed turns</div>
              <h2>Latency pulse</h2>
            <Sparkline points={derived.latencyPoints} />
            {/* <p className="validation-muted">Animated line = completed requests. Mint dots = accepted samples. Red dots = rejected samples.</p> */}
          </article>
        </section>

        <section className="validation-section chart-grid">
          <article className="validation-card">
            <div className="section-label">Metric tag coverage</div>
            <h2>Scenario families by count</h2>
            <div className="bar-stack tall">
              {derived.tagStats.slice(0, 12).map((item) => (
                <BarRow key={item.tag} label={`${item.tag} (${Math.round(item.successRate)}% accept)`} value={item.total} max={maxTagTotal} color="#7bf0cb" />
              ))}
            </div>
          </article>

          <article className="validation-card">
            <div className="section-label">Source evidence usage</div>
            <h2>Most retrieved documents</h2>
            <div className="bar-stack tall">
              {derived.topSources.map((item) => (
                <BarRow key={item.docId} label={item.docId.replace('ncie_', '').replace(/_/g, ' ')} value={item.count} max={maxSourceCount} color="#10a37f" />
              ))}
            </div>
          </article>

          <article className="validation-card wide-card">
            <div className="section-label">Per-session matrix</div>
            <h2>Acceptance and groundedness by benchmark session</h2>
            <div className="session-matrix">
              {derived.sessionStats.map((session) => {
                const acceptRate = session.total ? (session.accepted / session.total) * 100 : 0;
                return (
                  <button
                    key={session.sessionId}
                    className="session-cell"
                    style={{ '--cell-strength': acceptRate / 100 }}
                    onClick={() => {
                      const match = runs.find((record) => record.benchmark_session_id === session.sessionId);
                      if (match) setSelectedId(`${match.benchmark_session_id}-${match.turn_id}`);
                    }}
                  >
                    <strong>{session.sessionId}</strong>
                    <span>{Math.round(acceptRate)}% accepted</span>
                    <small>{session.total} turns, grounded {session.avgGroundedness.toFixed(1)}/5</small>
                  </button>
                );
              })}
            </div>
          </article>
        </section>

        <section className="validation-section">
          <div className="validation-section-heading">
            <div>
              <span className="section-label">Full trace explorer</span>
              <h2>Trace inspector</h2>
            </div>
            <p>Click a turn: query, RAG answer, evidence, verdict, and raw JSON unfold visually.</p>
          </div>

          <div className="trace-layout">
            <aside className="trace-list-panel">
              <div className="trace-controls">
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search question, answer, objective..."
                />
                <select value={verdictFilter} onChange={(event) => setVerdictFilter(event.target.value)}>
                  <option value="all">All verdicts</option>
                  <option value="accept">Accepted</option>
                  <option value="reject">Rejected</option>
                </select>
                <select value={tagFilter} onChange={(event) => setTagFilter(event.target.value)}>
                  <option value="all">All tags</option>
                  {derived.allTags.map((tag) => <option key={tag} value={tag}>{tag}</option>)}
                </select>
              </div>

              <div className="trace-list-count">{filteredRuns.length} matching turns</div>
              <div className="trace-list">
                {filteredRuns.map((record) => {
                  const id = `${record.benchmark_session_id}-${record.turn_id}`;
                  return (
                    <button
                      key={id}
                      className={`trace-list-item ${selectedId === id ? 'active' : ''}`}
                      onClick={() => setSelectedId(id)}
                    >
                      <div>
                        <strong>{record.benchmark_session_id} / {record.turn_id}</strong>
                        <span>{record.question}</span>
                      </div>
                      <em className={verdictOf(record)}>{verdictOf(record)}</em>
                    </button>
                  );
                })}
              </div>
            </aside>

            <TraceInspector record={selectedRecord} />
          </div>
        </section>

        
      </main>
    </div>
  );
}

export default ValidationDashboard;
