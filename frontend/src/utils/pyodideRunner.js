let pyodideReadyPromise = null;

const PYODIDE_SCRIPT_ID = 'pyodide-runtime-script';
const PYODIDE_VERSION = '0.27.2';

const emitStatus = (onStatus, step, detail = null) => {
  if (typeof onStatus === 'function') {
    onStatus({
      step,
      detail,
      timestamp: new Date().toISOString(),
    });
  }
};

function loadPyodideScript(onStatus) {
  return new Promise((resolve, reject) => {
    if (window.loadPyodide) {
      console.log('[Pyodide] Loader already available in window');
      emitStatus(onStatus, 'Loader already available');
      resolve();
      return;
    }

    const existing = document.getElementById(PYODIDE_SCRIPT_ID);
    if (existing) {
      existing.addEventListener('load', () => resolve(), { once: true });
      existing.addEventListener('error', () => reject(new Error('Failed to load Pyodide script.')), { once: true });
      return;
    }

    const script = document.createElement('script');
    script.id = PYODIDE_SCRIPT_ID;
    script.src = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/pyodide.js`;
    script.async = true;
    script.onload = () => {
      console.log('[Pyodide] Script loaded from CDN');
      emitStatus(onStatus, 'Script loaded from CDN');
      resolve();
    };
    script.onerror = () => reject(new Error('Failed to load Pyodide script.'));
    document.body.appendChild(script);
    console.log('[Pyodide] Injecting runtime script tag');
    emitStatus(onStatus, 'Injecting runtime script tag');
  });
}

async function getPyodideRuntime(onStatus) {
  if (!pyodideReadyPromise) {
    pyodideReadyPromise = (async () => {
      console.log('[Pyodide] Initializing runtime...');
      emitStatus(onStatus, 'Initializing runtime');
      await loadPyodideScript(onStatus);
      const pyodide = await window.loadPyodide({
        indexURL: `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`,
      });
      console.log('[Pyodide] Loading pandas and micropip runtime packages...');
      emitStatus(onStatus, 'Loading pandas and micropip runtime packages');
      await pyodide.loadPackage(['pandas', 'micropip']);
      console.log('[Pyodide] Installing Plotly Python package...');
      emitStatus(onStatus, 'Installing Plotly Python package');
      await pyodide.runPythonAsync(`
import micropip
try:
    import plotly
except ModuleNotFoundError:
    await micropip.install("plotly")
`);
      console.log('[Pyodide] Runtime ready');
      emitStatus(onStatus, 'Runtime ready');
      return pyodide;
    })();
  } else {
    console.log('[Pyodide] Reusing existing runtime promise');
    emitStatus(onStatus, 'Reusing existing runtime promise');
  }

  return pyodideReadyPromise;
}

const EXECUTION_WRAPPER = `
import csv
import io
import json
import pandas as pd
import re
import traceback
import plotly.io as pio
from plotly.basedatatypes import BaseFigure
from collections import Counter, defaultdict

def _normalize_value(value):
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value

    text = str(value).strip()
    if text == "":
        return None

    lowered = text.lower()
    if lowered in {"na", "n/a", "null", "none", "-", "--"}:
        return None

    cleaned = text.replace(",", "").replace("%", "").strip()
    try:
        number = float(cleaned)
        if number.is_integer():
            return int(number)
        return number
    except Exception:
        return text

def _load_rows(raw_text, raw_name):
    raw_name = (raw_name or "").lower()

    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
            return [{k: _normalize_value(v) for k, v in item.items()} for item in parsed]
        if isinstance(parsed, dict):
            for key in ["rows", "records", "data", "items", "students", "results"]:
                value = parsed.get(key)
                if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                    return [{k: _normalize_value(v) for k, v in item.items()} for item in value]
            if all(not isinstance(v, (list, dict)) for v in parsed.values()):
                return [{k: _normalize_value(v) for k, v in parsed.items()}]
    except Exception:
        pass

    sample = raw_text[:4096]
    delimiters = [",", "\\t", ";", "|"]
    delimiter = ","
    best_score = -1
    for candidate in delimiters:
        score = sample.count(candidate)
        if score > best_score:
            delimiter = candidate
            best_score = score

    reader = csv.DictReader(io.StringIO(raw_text), delimiter=delimiter)
    rows = []
    for row in reader:
        if not row:
            continue
        cleaned = {}
        for key, value in row.items():
            if key is None:
                continue
            cleaned[str(key).strip()] = _normalize_value(value)
        if any((str(v).strip() if v is not None else "") for v in cleaned.values()):
            rows.append(cleaned)
    return rows

def _load_dataframe(raw_text, raw_name):
    raw_name = (raw_name or "").lower()

    if raw_name.endswith(".json"):
        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, list):
                return pd.DataFrame(parsed)
            if isinstance(parsed, dict):
                for key in ["rows", "records", "data", "items", "students", "results"]:
                    value = parsed.get(key)
                    if isinstance(value, list):
                        return pd.DataFrame(value)
                return pd.DataFrame([parsed])
        except Exception:
            pass

    sample = raw_text[:4096]
    delimiters = [",", "\\t", ";", "|"]
    delimiter = ","
    best_score = -1
    for candidate in delimiters:
        score = sample.count(candidate)
        if score > best_score:
            delimiter = candidate
            best_score = score

    return pd.read_csv(io.StringIO(raw_text), sep=delimiter)

def to_markdown_table(rows):
    if not rows:
        return "No rows found."

    if isinstance(rows, dict):
        rows = [rows]

    normalized_rows = []
    for row in rows:
        if isinstance(row, dict):
            normalized_rows.append(row)
        else:
            normalized_rows.append({"value": row})

    columns = []
    seen = set()
    for row in normalized_rows:
        for key in row.keys():
            if key not in seen:
                columns.append(key)
                seen.add(key)

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in normalized_rows:
        body.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\\n".join([header, separator] + body)

def _coerce_plotly_figure(value):
    if value is None:
        return None
    try:
        if hasattr(value, "to_plotly_json") or hasattr(value, "to_dict"):
            return json.loads(pio.to_json(value, pretty=False))
    except Exception:
        pass
    if hasattr(value, "to_plotly_json"):
        return _json_safe(value.to_plotly_json())
    if hasattr(value, "to_dict"):
        maybe_dict = value.to_dict()
        if isinstance(maybe_dict, dict):
            return _json_safe(maybe_dict)
    if isinstance(value, dict) and "data" in value:
        return _json_safe(value)
    return _json_safe(value)

def _capture_plotly_show(self, *args, **kwargs):
    coerced = _coerce_plotly_figure(self)
    if coerced is not None:
        plotly_figures.append(coerced)
    return coerced

def _json_safe(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "tolist"):
        try:
            return _json_safe(value.tolist())
        except Exception:
            pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value)

def _validate_user_code(user_code):
    reserved_names = ["df", "rows", "file_name", "file_text", "df_columns", "df_shape", "df_head", "df_numeric_summary"]
    patterns = [
        re.compile(rf"^\\s*{name}\\s*=", re.MULTILINE) for name in reserved_names
    ] + [
        re.compile(rf"^\\s*{name}\\s*[+\\-*/%]=", re.MULTILINE) for name in reserved_names
    ]

    for pattern in patterns:
        if pattern.search(user_code):
            raise ValueError(
                "Do not overwrite runtime dataset variables such as df, rows, file_name, file_text, df_columns, df_shape, df_head, or df_numeric_summary. "
                "Inspect them and create derived variables instead."
            )

    forbidden_imports = [
        "import matplotlib",
        "from matplotlib",
        "import seaborn",
        "from seaborn",
    ]
    lowered = user_code.lower()
    for blocked in forbidden_imports:
        if blocked in lowered:
            raise ValueError(
                "Do not import matplotlib, seaborn, or Python plotly packages in the sandbox. "
                "Use pandas for analysis and assign a Plotly-compatible dictionary to plotly_figure."
            )

df = _load_dataframe(raw_file_text, raw_file_name)
df.columns = [str(col).strip() for col in df.columns]
df = df.where(pd.notnull(df), None)
rows = [
    {str(key).strip(): _normalize_value(value) for key, value in row.items()}
    for row in df.to_dict(orient="records")
]
file_name = raw_file_name
file_text = raw_file_text
df_columns = list(df.columns)
df_shape = tuple(df.shape)
df_head = df.head(5).to_dict(orient="records")
df_numeric_summary = df.describe(include="all").fillna("").to_dict()
result_markdown = ""
result = None
plotly_figure = None
plotly_figures = []
execution_error = ""
stdout_buffer = io.StringIO()

import sys
old_stdout = sys.stdout
sys.stdout = stdout_buffer
_original_plotly_show = BaseFigure.show
BaseFigure.show = _capture_plotly_show
try:
    _validate_user_code(user_code)
    exec(user_code, globals(), globals())
    if plotly_figure is not None:
        plotly_figure = _coerce_plotly_figure(plotly_figure)
        if plotly_figure is not None:
            plotly_figures.append(plotly_figure)
    elif "fig" in globals():
        plotly_figure = _coerce_plotly_figure(globals().get("fig"))
        if plotly_figure is not None and not plotly_figures:
            plotly_figures.append(plotly_figure)
except Exception:
    execution_error = traceback.format_exc()
finally:
    BaseFigure.show = _original_plotly_show
    sys.stdout = old_stdout

stdout_output = stdout_buffer.getvalue().strip()
if execution_error:
    final_output = json.dumps({
        "success": False,
        "error": execution_error,
        "row_count": len(rows),
        "column_count": len(df.columns),
    })
elif plotly_figures:
    final_output = json.dumps({
        "success": True,
        "output": result_markdown.strip() if isinstance(result_markdown, str) else "",
        "output_type": "plotly",
        "plotly_figure": _json_safe(plotly_figures[-1]),
        "plotly_figures": _json_safe(plotly_figures),
        "row_count": len(rows),
        "column_count": len(df.columns),
    })
elif isinstance(result_markdown, str) and result_markdown.strip():
    final_output = json.dumps({
        "success": True,
        "output": result_markdown.strip(),
        "output_type": "markdown",
        "row_count": len(rows),
        "column_count": len(df.columns),
    })
elif result is not None:
    if isinstance(result, (list, tuple, dict)):
        final_output = json.dumps({
            "success": True,
            "output": to_markdown_table(result),
            "output_type": "markdown",
            "row_count": len(rows),
            "column_count": len(df.columns),
        })
    else:
        final_output = json.dumps({
            "success": True,
            "output": str(result),
            "output_type": "text",
            "row_count": len(rows),
            "column_count": len(df.columns),
        })
elif stdout_output:
    final_output = json.dumps({
        "success": True,
        "output": stdout_output,
        "output_type": "text",
        "row_count": len(rows),
        "column_count": len(df.columns),
    })
else:
    final_output = json.dumps({
        "success": True,
        "output": f"Code executed successfully on {len(rows)} rows, but no output was produced.",
        "output_type": "text",
        "row_count": len(rows),
        "column_count": len(df.columns),
    })

final_output
`;

export async function runPythonOnDataset({ code, datasetText, fileName, onStatus }) {
  if (!datasetText) {
    throw new Error('No dataset is available for execution.');
  }

  emitStatus(onStatus, 'Starting execution', {
    fileName: fileName || 'dataset.csv',
    datasetLength: datasetText.length,
    codeLength: (code || '').length,
  });
  console.log('[Pyodide] Starting execution', {
    fileName: fileName || 'dataset.csv',
    datasetLength: datasetText.length,
    codeLength: (code || '').length,
  });

  const pyodide = await getPyodideRuntime(onStatus);
  pyodide.globals.set('raw_file_text', datasetText);
  pyodide.globals.set('raw_file_name', fileName || 'dataset.csv');
  pyodide.globals.set('user_code', code);

  try {
    console.log('[Pyodide] Running Python wrapper...');
    emitStatus(onStatus, 'Running Python wrapper');
    const output = pyodide.runPython(EXECUTION_WRAPPER);
    const normalized = typeof output === 'string' ? output : String(output);
    let parsed = null;

    try {
      parsed = JSON.parse(normalized);
    } catch {
      return normalized;
    }

    if (parsed && parsed.success === false) {
      console.error('[Pyodide] Execution failed inside sandbox', parsed.error);
      emitStatus(onStatus, 'Execution failed inside sandbox', parsed.error);
      throw new Error(parsed.error || 'Python execution failed.');
    }

    console.log('[Pyodide] Execution completed successfully');
    emitStatus(onStatus, 'Execution completed successfully');
    return parsed || normalized;
  } finally {
    console.log('[Pyodide] Cleaning sandbox globals');
    emitStatus(onStatus, 'Cleaning sandbox globals');
    pyodide.globals.delete('raw_file_text');
    pyodide.globals.delete('raw_file_name');
    pyodide.globals.delete('user_code');
  }
}
