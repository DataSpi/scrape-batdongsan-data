# CLAUDE.md

Snapshot trạng thái dự án cho Claude Code (và bất kỳ ai đọc lại sau này). File này được cập nhật ở mỗi bước tiến của giai đoạn 2 (Docker/Airflow/CI-CD/Docs) — xem checklist ở cuối file.

## Dự án là gì

Scrape dữ liệu bất động sản từ [batdongsan.com.vn](https://batdongsan.com.vn), chuẩn hoá qua dbt, phục vụ phân tích thị trường BĐS Việt Nam (dashboard Looker Studio + báo cáo HTML tĩnh + series blog Substack). Dự án cá nhân, một mình maintain (DataSpi/spyno).

## Kiến trúc hiện tại (giai đoạn 1)

```
batdongsan.com.vn --(src/_web2br/*.py, curl_cffi + BeautifulSoup)--> BigQuery re_bronze (raw)
                                                                          |
                                                                    dbt staging models
                                                                          v
                                                                   BigQuery re_silver (deduped/cleaned)
                                                                          |
                                                                      dbt marts
                                                                          v
                                                                   BigQuery re_gold (analysis-ready)
                                                                          |
                                    +-------------------------------------+-------------------------------------+
                                    v                                                                           v
                        Malloy (malloy/malloy_publisher, TRỎ VÀO SUPABASE/POSTGRES CŨ,               src/reports/report_builder.py
                        CHƯA MIGRATE BIGQUERY — nợ kỹ thuật)                                                    |
                                    |                                                                docs/reports/*.html (GitHub Pages)
                          Looker Studio dashboard
```

**Orchestration**: `src/orchestrator/run_pipeline.py` — 9 bước tuần tự (scrape sale HCM/HN, scrape rent HCM/HN, scrape projects HCM/HN, scrape metadata, `dbt run`, `dbt test`), dừng ngay khi có bước lỗi. Chạy qua crontab (Thứ 2, 9h sáng) trên máy local của maintainer, không retry, không alerting. Location/project lineage (geocode + seed) là bước thủ công riêng, không nằm trong lịch tuần.

**Ràng buộc quan trọng nhất**: batdongsan.com.vn chặn IP của cloud/CI runner — bước scrape bắt buộc chạy từ IP dân dụng (máy local). Đây là lý do pipeline hiện không dùng GitHub Actions/Airflow, và là ràng buộc thiết kế xuyên suốt giai đoạn 2 (xem bên dưới).

**Stack**: Python 3.12, `requirements.txt` phẳng (không có pyproject.toml/Pipfile). dbt-bigquery cho transform (`dbt/`, schema `re_bronze` → `re_silver` → `re_gold`). Malloy cho semantic layer + báo cáo (đang trỏ Postgres cũ, tech debt). Không có test suite Python (test data quality nằm hết ở `dbt/tests/`).

**Docker/CI-CD**: chưa có gì ở thời điểm viết file này (2026-07-21) — đây chính là nội dung giai đoạn 2.

## Nợ kỹ thuật đã biết (ngoài phạm vi giai đoạn 2, không đụng vào)

- Malloy (`malloy/malloy_publisher/real_estate.malloy`) vẫn trỏ Supabase/Postgres cũ, chưa migrate BigQuery. `src/utils/malloy_cli_runner.py` có đường dẫn config hardcode kiểu Windows. Theo quyết định của maintainer, **bỏ qua hoàn toàn ở giai đoạn 2**.
- `apscheduler` trong `requirements.txt` là dependency chết, không dùng ở đâu trong `src/`.
- `src/_br2sil/` chỉ còn file `.pyc` mồ côi, không có source `.py`.
- `src/utils/getting_metadata.py` không được import ở đâu trong `src/` — code mồ côi khác, phát hiện khi thêm ruff (Stage 3).
- `src/utils/common_tools.py` và `src/utils/sqlalchemy_conn.py` là 2 helper Postgres gần trùng nhau đã lệch nhau (một đọc biến env `DB_DB_NAME` không tồn tại trong `.env` thực tế).
- `docs/quickstart.md` mô tả setup theo conda + Python 3.10 + Supabase — lỗi thời so với thực tế (Python 3.12 + BigQuery), sẽ được sửa ở Stage 4.

## Giai đoạn 2 — mục tiêu

Đóng gói dự án bằng Docker, orchestrate bằng Airflow (tự host local vì ràng buộc IP), và áp dụng CI/CD best practice qua GitHub Actions — để dev khác dễ dàng chạy được dự án, đồng thời là dịp luyện tập/thể hiện kỹ năng. Chi tiết kế hoạch đầy đủ: xem plan đã duyệt trong phiên làm việc (các stage: Docker → Airflow → CI/CD → Docs, mỗi stage 1 branch/PR riêng).

### Checklist tiến độ

- [x] Stage 0 — Khởi tạo CLAUDE.md (`chore/init-claude-md`)
- [x] Stage 1 — Dockerize (`feat/stage2-docker`): `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env.example`. Validated: `docker compose build` OK, container reaches batdongsan.com.vn from local machine (HTTP 200 on `GetCitiesV2`), confirming Docker doesn't break the residential-IP scraping constraint.
- [x] Stage 2 — Airflow DAGs (`feat/stage2-airflow`): `airflow/Dockerfile`, mở rộng `docker-compose.yml` (LocalExecutor, Postgres metadata DB riêng), `dags/pipeline_weekly_dag.py`, `dags/lineage_rebuild_dag.py`, sửa `.gitignore` (dòng `dags/` cũ sẽ nuốt mất DAG source). Validated: 2 DAG parse không lỗi (`airflow dags list-import-errors` → No data found), `airflow-init` migrate DB + tạo admin user thành công, import module Python đúng PYTHONPATH trong container scheduler. Lưu ý: `dbt/profiles.yml` (gitignored) cần path `keyfile` khác nhau giữa bare-metal và trong container Airflow — xem comment trong `dbt/profiles.yml.example`.
- [x] Stage 3 — CI/CD (`feat/stage2-cicd`): `.github/workflows/ci.yml` (lint, docker-build-push lên GHCR), `.github/workflows/dbt-ci.yml` (dbt compile, path-filtered `dbt/**`), `pyproject.toml` (ruff), sửa `.github/actions/setup-python-env` (bỏ base64 `.env` decode không dùng, fix mô tả Python 3.14→3.12). Validated: `ruff check .` pass sạch toàn repo (per-file-ignore cho vài file legacy nhiều tab/dòng dài — nợ kỹ thuật, xem mục trên), YAML workflow hợp lệ, `docker compose build` vẫn OK. Phát hiện phụ trong lúc test Stage 2: `src/_web2br/*.py` ghi CSV ra `data/` tương đối (thư mục gitignored) — đã fix bằng cách mount + tạo `data/` trong `Dockerfile`/`docker-compose.yml`. `src/utils/getting_metadata.py` là code mồ côi khác (không được import ở đâu), thêm vào danh sách nợ kỹ thuật Stage 5.
- [x] Stage 4 — Docs (`feat/stage2-docs`): cập nhật `README.md` (sơ đồ mermaid: Airflow thay crontab), `docs/quickstart.md` (viết lại hoàn toàn theo Docker+Airflow, giữ mục bare-metal fallback), `docs/technical-guides.md` (thêm mục Docker/Airflow layout + CI/CD, sửa câu sai "không dùng GitHub Actions/Airflow", thêm troubleshooting cho container/DAG).
- [ ] Stage 5 (tuỳ chọn) — Dọn code cũ (`chore/legacy-cleanup`): xoá `apscheduler`, `src/_br2sil/`, gộp 2 helper Postgres trùng nhau
