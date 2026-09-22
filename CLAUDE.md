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
                          Looker Studio dashboard (BigQuery connector trực tiếp vào
                          re_gold.mart_real_estate, khai báo qua dbt exposure —
                          dbt/models/marts/_exposures.yml)
```

`re_silver` cũng chứa lịch sử SCD2 của từng listing (`dbt/snapshots/snp_real_estate*`, dbt
`snapshot` với `strategy: check` + `hard_deletes='new_record'`) — `stg_real_estate*` chỉ giữ bản
mới nhất mỗi tuần, còn `snp_real_estate*` giữ mọi lần thay đổi giá/diện tích/loại hình... và đánh
dấu tin đã bị gỡ (`dbt_is_deleted`). `mart_real_estate*` không đổi hành vi (vẫn build từ
`stg_real_estate*`, không có lịch sử); đọc "trạng thái hiện tại" (active/closed) qua
`vw_real_estate_current`/`vw_real_estate_rent_current` — xem Giai đoạn 3.

Malloy (`malloy/malloy_publisher/`) và pipeline báo cáo HTML tĩnh (`src/reports/report_builder.py`
→ `docs/reports/*.html`) đã **ngừng dùng** — cả hai trỏ vào Supabase/Postgres cũ, không còn
được regenerate. Đây là code mồ côi (xem mục nợ kỹ thuật), không phải nhánh sống của pipeline.

**Orchestration**: `src/orchestrator/run_pipeline.py` — 10 bước tuần tự (scrape sale HCM/HN, scrape rent HCM/HN, scrape projects HCM/HN, scrape metadata, `dbt run`, `dbt snapshot`, `dbt test`), dừng ngay khi có bước lỗi. Live path là launchd job (`scripts/run_weekly_pipeline.sh` + `scripts/com.dataspi.batdongsan-weekly.plist`, Thứ 2 9h sáng) trên máy local của maintainer — không có process nào chạy liên tục giữa các lần. Airflow (`dags/pipeline_weekly_dag.py`, tự host qua `docker-compose`) vẫn tồn tại trong repo như path tuỳ chọn cho ai muốn UI/retry/backfill, nhưng không phải default nữa — xem Giai đoạn 3 để biết lý do đảo ngược quyết định Stage 2. Location/project lineage (geocode + seed) là bước thủ công riêng, không nằm trong lịch tuần.

**Ràng buộc quan trọng nhất**: batdongsan.com.vn chặn IP của cloud/CI runner — bước scrape bắt buộc chạy từ IP dân dụng (máy local). Đây là lý do pipeline không dùng GitHub Actions để scrape, và là ràng buộc thiết kế xuyên suốt cả giai đoạn 2 lẫn giai đoạn 3.

**Stack**: Python 3.12, `requirements.txt` phẳng (không có pyproject.toml/Pipfile). dbt-bigquery cho transform (`dbt/`, schema `re_bronze` → `re_silver` → `re_gold`). BI layer là Looker Studio nối trực tiếp BigQuery `re_gold` (dbt exposure). Malloy/Supabase không còn dùng — xem mục nợ kỹ thuật. Không có test suite Python (test data quality nằm hết ở `dbt/tests/`).

**Docker/CI-CD**: chưa có gì ở thời điểm viết file này (2026-07-21) — đây chính là nội dung giai đoạn 2.

## Nợ kỹ thuật đã biết (ngoài phạm vi giai đoạn 2, không đụng vào)

- Malloy (`malloy/malloy_publisher/real_estate.malloy`) và `src/reports/report_builder.py` (→ `docs/reports/*.html`) không còn được dùng — cả hai trỏ Supabase/Postgres cũ, đã bị thay hoàn toàn bởi Looker Studio nối trực tiếp BigQuery `re_gold` (xem kiến trúc ở trên). `docs/reports/*.html` hiện là artifact đông cứng từ lần build cuối, không còn regenerate. `src/utils/malloy_cli_runner.py` có đường dẫn config hardcode kiểu Windows. Xoá/dọn ở Stage 5 (đã thêm vào checklist).
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
- [ ] Stage 5 (tuỳ chọn) — Dọn code cũ (`chore/legacy-cleanup`): xoá `apscheduler`, `src/_br2sil/`, gộp 2 helper Postgres trùng nhau, xoá `malloy/` + `src/reports/report_builder.py` (ngừng dùng, xem mục nợ kỹ thuật)

## Giai đoạn 3 — Scheduling gọn + SCD2/CDC (`feat/scd2-launchd-scheduling`)

Hai quyết định độc lập, không nằm trong scope giai đoạn 2 gốc:

1. **Đảo ngược quyết định Stage 2 về live scheduler**: Airflow (`airflow-scheduler` + Postgres
   metadata riêng) cần chạy liên tục 24/7 (~1–1.5GB RAM không đổi) chỉ để bắn 1 job/tuần — sau khi
   cân nhắc resource cost, chuyển live path về launchd (`scripts/run_weekly_pipeline.sh` +
   `scripts/com.dataspi.batdongsan-weekly.plist`) gọi thẳng `src/orchestrator/run_pipeline.py`
   bare-metal (conda env `scrape_bds`), không qua Docker — không có process nào sống giữa các lần
   chạy. Dùng launchd thay vì cron thật: cron bỏ qua hẳn lần chạy nếu máy đang ngủ đúng giờ trigger,
   launchd (`StartCalendarInterval`) tự chạy bù khi máy thức dậy. `caffeinate -i` giữ máy không ngủ
   trong lúc chạy. Airflow (`dags/pipeline_weekly_dag.py`, `docker-compose.yml`, `airflow/`)
   **không bị xoá** — vẫn là path hợp lệ, tài liệu hoá là tuỳ chọn thay vì default. Cả hai path
   (`run_pipeline.py` STEPS và DAG) được giữ đồng bộ thủ công — sửa 1 bên nhớ sửa bên kia.
2. **SCD2/CDC cho listing**: `stg_real_estate`/`stg_real_estate_rent` trước giờ dedup bằng
   `ROW_NUMBER() PARTITION BY product_id ORDER BY scraped_at DESC` rồi `WHERE rn = 1` — mỗi lần
   `dbt run` xoá mất lịch sử thay đổi, chỉ giữ bản hiện tại. Thêm dbt `snapshot`
   (`dbt/snapshots/snp_real_estate.sql`, `snp_real_estate_rent.sql`, `strategy: check` trên các cột
   nghiệp vụ price/area/type/bedrooms/toilets/expired/vipType/productType,
   `hard_deletes='new_record'` để đánh dấu tin bị gỡ thay vì xoá mất) chạy sau `dbt run`, trước
   `dbt test`, ở cả `run_pipeline.py` và DAG. Đọc trạng thái hiện tại qua view tiện dụng
   `vw_real_estate_current`/`vw_real_estate_rent_current` (`status = 'active'/'closed'`) thay vì
   phải biết tên cột nội bộ của dbt (`dbt_valid_to`, `dbt_is_deleted` — lưu ý: string `'True'/'False'`,
   không phải bool). `mart_real_estate*` không đổi — marts vẫn phản ánh trạng thái hiện tại như cũ,
   không ảnh hưởng dashboard Looker Studio đang chạy.

Việc dọn crontab rác cũ trên máy (dòng trỏ project không liên quan, path
`~/Documents/1. Data_Science/scrape_bds`) và cài đặt launchd job thật (`launchctl load`) là thao
tác thủ công ngoài git repo, không nằm trong commit nào.
