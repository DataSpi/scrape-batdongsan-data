# Technical Guides

Trang nay la khung tong hop cac huong dan ky thuat chi tiet. Ban co the bo sung theo tung nhom sau.

## 1) Scraping Layer

Noi dung nen co:
- Kien truc crawler, batching, retry, throttle.
- Mapping cac script trong `src/web2br/`.
- Cach cap nhat selector khi website thay doi.

Goi y file lien quan:
- `src/web2br/j_real_estate.py`
- `src/web2br/j_projects.py`
- `src/web2br/j_metadata.py`

## 2) Bronze -> Silver

Noi dung nen co:
- Quy tac clean du lieu (price, area, type normalization).
- Duplicate checks va quality checks.
- Cac table output va schema conventions.

Goi y file lien quan:
- `src/br2sil/j_real_estate.py`

## 3) Semantic Modeling va Analytics

Noi dung nen co:
- Mo hinh Malloy trong `models/real_estate.malloy`.
- dbt mart model trong `dbt/models/marts/`.
- Nguyen tac dat ten dimensions va joins.

## 4) Reports va Visualization

Noi dung nen co:
- Script tao report HTML.
- Cac chi so KPI va y nghia.
- Quy trinh export/chia se ket qua.

Goi y file lien quan:
- `src/reports/generate_report.py`
- `reports/output/malloy_result.html`

## 5) Orchestration

Noi dung nen co:
- Lich chay jobs.
- Workflow CI/CD ingestion.
- Cach debug task fail.

Goi y file lien quan:
- `.github/workflows/d_ingest_main.yml`
- `dags/real_estate_dag.py`

## Dieu huong

- Ve [Docs Hub](README.md)
- Sang [Quickstart](quickstart.md)
- Ve [Trang chu du an](../readme.md)
