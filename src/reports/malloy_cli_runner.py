import json
import os
import subprocess
import sys
import shutil
import tempfile
from html import escape
from pathlib import Path


DEFAULT_CONFIG = Path(r"C:\Users\LAP14354\.config\malloy\malloy-config.json")


def _resolve_malloy_cli() -> str:
	"""Resolve Malloy CLI executable path on Windows/PATH."""
	for candidate in ("malloy-cli", "malloy-cli.cmd", "malloy-cli.exe"):
		resolved = shutil.which(candidate)
		if resolved:
			return resolved

	raise FileNotFoundError(
		"Could not find Malloy CLI on PATH. Install it or set PATH so one of "
		"malloy-cli, malloy-cli.cmd, or malloy-cli.exe is discoverable."
	)


def ml_go(args: list[str], config_path: Path = DEFAULT_CONFIG) -> int:
	"""Run malloy-cli with a fixed --config and forwarded arguments."""
	malloy_cli = _resolve_malloy_cli()
	cmd = [malloy_cli, "--config", str(config_path), *args]

	# .cmd/.bat launch reliably through cmd on Windows.
	if malloy_cli.lower().endswith((".cmd", ".bat")):
		cmd = ["cmd", "/c", *cmd]

	completed = subprocess.run(
		cmd,
		check=False,
		capture_output=True,
		text=True,
		encoding="utf-8",
		errors="replace",
	)

	# Print captured output so results appear in terminals and interactive windows.
	if completed.stdout:
		print(completed.stdout, end="")
	if completed.stderr:
		print(completed.stderr, end="", file=sys.stderr)

	return completed.returncode


def _run_malloy_json(args: list[str], config_path: Path = DEFAULT_CONFIG) -> dict | list:
    """Run malloy-cli with JSON output and return parsed JSON."""
    malloy_cli = _resolve_malloy_cli()
    cmd = [malloy_cli, "--config", str(config_path), *args]

    if malloy_cli.lower().endswith((".cmd", ".bat")):
        cmd = ["cmd", "/c", *cmd]

    completed = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)

    if completed.returncode != 0:
        raise RuntimeError(f"Malloy CLI exited with code {completed.returncode}.")

    return json.loads(completed.stdout)


def run_malloy_file(file_path: str, query_name: str | None = None) -> dict | list:
    """
    Run an existing Malloy file and return the result as parsed JSON.

    Args:
        file_path:   Path to the .malloy file to run.
        query_name:  Optional named query inside the file to execute.
                     If omitted, malloy-cli runs the default (last) query.
    """
    args = ["run", str(Path(file_path).resolve())]

    if query_name:
        args.append(query_name)

    return _run_malloy_json(args)
    


def run_direct_query(model_path: str, query: str) -> dict | list:
    """
    Create a temporary Malloy file that imports the model and runs the query string.
    Returns the parsed JSON result.

    The temp file is created next to the model file so the import path always
    resolves correctly regardless of how model_path is specified.
    """
    model_file = Path(model_path).resolve()
    model_dir = model_file.parent
    import_name = model_file.name  # just the filename - temp file sits beside it

    tmp_content = f'import "./{import_name}"\n\nrun: {query}\n'

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".malloy", dir=model_dir)
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp:
            tmp.write(tmp_content)

        return _run_malloy_json(["run", tmp_path])
    finally:
        os.unlink(tmp_path)


def _is_scalar(value: object) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _format_number(value: int | float) -> str:
    """Round to integer and format with thousand separators for readability."""
    return f"{round(value):,}"


def _json_value_to_html(value: object) -> str:
    """Render a JSON-compatible value into nested HTML."""
    if isinstance(value, dict):
        if not value:
            return '<span class="empty">empty object</span>'

        # Leaf-level object is rendered as 1-row table with field columns,
        # matching the familiar Malloy tabular layout.
        if all(_is_scalar(v) for v in value.values()):
            columns = list(value.keys())
            header = "".join(f"<th>{escape(str(col))}</th>" for col in columns)
            cells = "".join(f"<td>{_json_value_to_html(value.get(col))}</td>" for col in columns)
            return (
                '<table class="leaf-table">'
                f"<thead><tr>{header}</tr></thead>"
                f"<tbody><tr>{cells}</tr></tbody>"
                "</table>"
            )

        rows: list[str] = []
        for key, val in value.items():
            rows.append(
                "<tr>"
                f"<th>{escape(str(key))}</th>"
                f"<td>{_json_value_to_html(val)}</td>"
                "</tr>"
            )

        return (
            '<table class="kv-table">'
            '<thead><tr><th>Field</th><th>Value</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody>"
            "</table>"
        )

    if isinstance(value, list):
        if not value:
            return '<span class="empty">empty list</span>'

        if all(isinstance(item, dict) for item in value):
            columns: list[str] = []
            for item in value:
                for key in item:
                    if key not in columns:
                        columns.append(key)

            header = "".join(f"<th>{escape(str(col))}</th>" for col in columns)
            body_rows: list[str] = []

            for item in value:
                cells = "".join(
                    f"<td>{_json_value_to_html(item.get(col))}</td>" for col in columns
                )
                body_rows.append(f"<tr>{cells}</tr>")

            return (
                '<table class="list-table">'
                f"<thead><tr>{header}</tr></thead>"
                f"<tbody>{''.join(body_rows)}</tbody>"
                "</table>"
            )

        items = "".join(f"<li>{_json_value_to_html(item)}</li>" for item in value)
        return f"<ol class=\"json-list\">{items}</ol>"

    if value is None:
        return '<span class="null">null</span>'

    if isinstance(value, bool):
        return str(value).lower()

    if isinstance(value, (int, float)):
        return _format_number(value)

    return escape(str(value))


def malloy_result_to_html(result: dict | list, title: str = "Malloy Query Result") -> str:
        """Convert Malloy JSON output into a styled HTML document."""
        content = _json_value_to_html(result)
        return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape(title)}</title>
    <style>
        :root {{
            --bg: #f2f5f9;
            --card: #ffffff;
            --line: #b8c3d1;
            --text: #0f172a;
            --muted: #475569;
            --accent: #0b7285;
            --header-bg: #dff1f6;
            --header-text: #073642;
            --cell-bg: #ffffff;
        }}
        body {{
            margin: 0;
            font-family: "Segoe UI", Tahoma, sans-serif;
            background: linear-gradient(180deg, #e8eef5 0%, var(--bg) 100%);
            color: var(--text);
        }}
        .wrap {{
            max-width: 1100px;
            margin: 32px auto;
            padding: 0 16px;
        }}
        .card {{
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 16px;
            box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
            overflow-x: auto;
        }}
        h1 {{
            margin: 0 0 14px;
            font-size: 24px;
            color: var(--accent);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 8px 0;
            table-layout: auto;
        }}
        th, td {{
            border: 1px solid var(--line);
            padding: 8px 10px;
            vertical-align: top;
            text-align: left;
            word-break: break-word;
            background: var(--cell-bg);
            color: var(--text);
        }}
        th {{
            background: var(--header-bg);
            color: var(--header-text);
            font-weight: 600;
        }}
        .kv-table th {{
            width: 180px;
            min-width: 180px;
        }}
        .leaf-table td,
        .list-table td {{
            background: #fbfdff;
        }}
        .json-list {{
            margin: 0;
            padding-left: 18px;
        }}
        .null, .empty {{
            color: var(--muted);
            font-style: italic;
        }}
        .legend {{
            margin: 0 0 14px;
            padding: 10px 12px;
            border: 1px dashed var(--line);
            border-radius: 10px;
            background: #f8fcfe;
            color: var(--header-text);
        }}
        .legend p {{
            margin: 0 0 6px;
            font-weight: 600;
        }}
        .legend ul {{
            margin: 0;
            padding-left: 18px;
        }}
    </style>
</head>
<body>
    <div class="wrap">
        <div class="card">
            <h1>{escape(title)}</h1>
            <div class="legend">
                <p>Chú thích</p>
                <ul>
                    <li>price: triệu VND</li>
                    <li>area: m2</li>
                </ul>
            </div>
            {content}
        </div>
    </div>
</body>
</html>
"""


def export_malloy_result_html(
        result: dict | list,
        output_path: str,
        title: str = "Báo cáo giá bất động sản theo dự án tại HN & TPHCM",
) -> Path:
        """Write rendered Malloy JSON output to an HTML file."""
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(malloy_result_to_html(result, title=title), encoding="utf-8")
        return output_file



# ml_go(args=["run", "sample.malloy", "test_query"])
result = run_malloy_file(file_path="D:/scrape-batdongsan-data/tmp/test_tmp.malloy")
export_malloy_result_html(result, output_path="reports/output/HCM-HN_prj.html")