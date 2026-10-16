# Adjust AIRFLOW_VERSION to whatever the current stable release is when you build --
# pinned here to a known-good tag rather than `latest` for reproducibility.
FROM apache/airflow:2.10.4-python3.12

# Official image installs into its own venv (owned by the `airflow` user, not root)
# rather than system site-packages -- `--user` fails here because user site-packages
# aren't visible inside that venv, so a plain install is both correct and sufficient.
USER airflow
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
