import json
import os
import shutil
import subprocess
import sys
import tempfile
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
        file_path: Path to the .malloy file to run.
        query_name: Optional named query inside the file to execute.
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
    import_name = model_file.name

    tmp_content = f'import "./{import_name}"\n\nrun: {query}\n'

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".malloy", dir=model_dir)
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp:
            tmp.write(tmp_content)

        return _run_malloy_json(["run", tmp_path])
    finally:
        os.unlink(tmp_path)
