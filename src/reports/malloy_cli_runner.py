"""Backward-compatible wrapper for Malloy runner/report APIs.

Use utils.malloy_cli_runner for CLI utilities and src.reports.report_builder
for report generation orchestration.
"""

from report_builder import (
    build_report_from_direct_query,
    build_report_from_malloy_file,
    export_malloy_result_html,
    malloy_result_to_html,
)

from utils.malloy_cli_runner import ml_go, run_direct_query, run_malloy_file


__all__ = [
    "ml_go",
    "run_malloy_file",
    "run_direct_query",
    "malloy_result_to_html",
    "export_malloy_result_html",
    "build_report_from_malloy_file",
    "build_report_from_direct_query",
]


if __name__ == "__main__":
    report_path = build_report_from_malloy_file(
        malloy_file_path="D:/scrape-batdongsan-data/tmp/test_tmp.malloy",
        output_path="reports/output/HCM-HN_prj.html",
    )
    print(f"Report generated: {report_path}")
