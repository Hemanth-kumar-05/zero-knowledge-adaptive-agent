import React, { useEffect, useRef, useState } from 'react';

const PLOTLY_SCRIPT_ID = 'plotly-runtime-script';
const PLOTLY_CDN = 'https://cdn.plot.ly/plotly-2.35.2.min.js';

function loadPlotly() {
  return new Promise((resolve, reject) => {
    if (window.Plotly) {
      resolve(window.Plotly);
      return;
    }

    const existing = document.getElementById(PLOTLY_SCRIPT_ID);
    if (existing) {
      existing.addEventListener('load', () => resolve(window.Plotly), { once: true });
      existing.addEventListener('error', () => reject(new Error('Failed to load Plotly.')), { once: true });
      return;
    }

    const script = document.createElement('script');
    script.id = PLOTLY_SCRIPT_ID;
    script.src = PLOTLY_CDN;
    script.async = true;
    script.onload = () => resolve(window.Plotly);
    script.onerror = () => reject(new Error('Failed to load Plotly.'));
    document.body.appendChild(script);
  });
}

function PlotlyChart({ figure }) {
  const chartRef = useRef(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    const renderChart = async () => {
      if (!figure || !chartRef.current) return;

      try {
        const Plotly = await loadPlotly();
        if (cancelled || !chartRef.current) return;

        await Plotly.newPlot(
          chartRef.current,
          Array.isArray(figure.data) ? figure.data : [],
          figure.layout || {},
          {
            responsive: true,
            displayModeBar: true,
            ...figure.config,
          }
        );
        setError('');
      } catch (err) {
        if (!cancelled) {
          setError(err?.message || 'Failed to render chart.');
        }
      }
    };

    renderChart();

    return () => {
      cancelled = true;
      if (window.Plotly && chartRef.current) {
        window.Plotly.purge(chartRef.current);
      }
    };
  }, [figure]);

  if (!figure) return null;
  if (error) {
    return <div className="plotly-chart-error">{error}</div>;
  }

  return <div ref={chartRef} className="plotly-chart-canvas" />;
}

export default PlotlyChart;
