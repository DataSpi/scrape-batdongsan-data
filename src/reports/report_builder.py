import sys
from html import escape
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.malloy_cli_runner import run_malloy_file


DEFAULT_REPORT_TITLE = "Bao cao gia bat dong san theo du an tai HN & TPHCM"


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
        return f'<ol class="json-list">{items}</ol>'

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
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
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
            font-family: \"Segoe UI\", Tahoma, sans-serif;
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
    <div class=\"wrap\">
        <div class=\"card\">
            <h1>{escape(title)}</h1>
            <div class=\"legend\">
                <p>Chu thich</p>
                <ul>
                    <li>price: trieu VND</li>
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
    title: str = DEFAULT_REPORT_TITLE,
) -> Path:
    """Write rendered Malloy JSON output to an HTML file."""
    output_file = Path(output_path).resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(malloy_result_to_html(result, title=title), encoding="utf-8")
    return output_file

def build_report(
    malloy_file_path: str,
    output_path: str,
    query_name: str | None = None,
    title: str = DEFAULT_REPORT_TITLE,
) -> Path:
    """Execute a Malloy file and export the result into an HTML report."""
    result = run_malloy_file(model_path=malloy_file_path, query_name=query_name)
    return export_malloy_result_html(result=result, output_path=output_path, title=title)


if __name__ == "__main__":
    by_project_rp = build_report(
        malloy_file_path="models/analysing/q_general_info.malloy",
        query_name="general_info_by_project",
        title="Báo cáo giá bất động sản theo dự án tại HN & TPHCM",
        output_path="reports/output/HCM-HN_prj.html",
    )
    print(f"Report generated: {by_project_rp}")
    
    by_district_rp = build_report(
        malloy_file_path="models/analysing/q_general_info.malloy",
        query_name="general_info_by_district",
        title="Báo cáo giá bất động sản theo quận tại HN & TPHCM",
        output_path="reports/output/HCM-HN_districts.html",
    )
    print(f"Report generated: {by_district_rp}")
