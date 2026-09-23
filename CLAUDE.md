# CLAUDE.md

Snapshot trạng thái dự án cho Claude Code (và bất kỳ ai đọc lại sau này). File này được cập nhật ở mỗi bước tiến của giai đoạn 2 (Docker/Airflow/CI-CD/Docs) — xem checklist ở cuối file.

## Dự án là gì

Scrape dữ liệu bất động sản từ [batdongsan.com.vn](https://batdongsan.com.vn), chuẩn hoá qua dbt, phục vụ phân tích thị trường BĐS Việt Nam (dashboard Looker Studio + báo cáo HTML tĩnh + series blog Substack). Dự án cá nhân, một mình maintain (DataSpi/spyno).

## Kiến trúc hiện tại (giai đoạn 1)

```
batdongsan.com.vn --(src/_web2br/*.py, curl_cffi + BeautifulSoup)--> BigQuery re_bronze (raw)
                                                                          |
                                                                dbt star schema (fct_/dim_ models)
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
`snapshot` với `strategy: check` + `hard_deletes='new_record'`) — `fct_real_estate*` chỉ giữ bản
mới nhất mỗi tuần, còn `snp_real_estate*` giữ mọi lần thay đổi giá/diện tích/loại hình... và đánh
dấu tin đã bị gỡ (`dbt_is_deleted`). `mart_real_estate*` không đổi hành vi (vẫn build từ
`fct_real_estate*`, không có lịch sử); đọc "trạng thái hiện tại" (active/closed) qua
`vw_real_estate_current`/`vw_real_estate_rent_current` — xem Giai đoạn 3.

Malloy (`malloy/malloy_publisher/`) và pipeline báo cáo HTML tĩnh (`src/reports/report_builder.py`
→ `docs/reports/*.html`) đã **ngừng dùng** — cả hai trỏ vào Supabase/Postgres cũ, không còn
được regenerate. Đây là code mồ côi (xem mục nợ kỹ thuật), không phải nhánh sống của pipeline.

**Orchestration**: `src/orchestrator/run_pipeline.py` — 9 bước tuần tự (scrape sale HCM/HN, scrape rent HCM/HN, scrape projects HCM/HN, `dbt run`, `dbt snapshot`, `dbt test`), dừng ngay khi có bước lỗi. Live path là launchd job (`scripts/run_weekly_pipeline.sh` + `scripts/com.dataspi.batdongsan-weekly.plist`, Thứ 2 9h sáng) trên máy local của maintainer — không có process nào chạy liên tục giữa các lần. Airflow (`dags/pipeline_weekly_dag.py`, tự host qua `docker-compose`) vẫn tồn tại trong repo như path tuỳ chọn cho ai muốn UI/retry/backfill, nhưng không phải default nữa — xem Giai đoạn 3 để biết lý do đảo ngược quyết định Stage 2. Location/project lineage (geocode + seed) **và** metadata scrape (`metadata.py` — city/ward/street/project lookup, nguồn bronze cho lineage đó) là bước thủ công riêng, không nằm trong lịch tuần — dbt không rebuild `dim_location_v1/v2`/`dim_project` hàng tuần nên scrape lại metadata mỗi tuần cũng vô nghĩa, xem docstring `run_pipeline.py`.

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
2. **SCD2/CDC cho listing**: `fct_real_estate`/`fct_real_estate_rent` trước giờ dedup bằng
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

## Giai đoạn 4 — Naming cleanup: `fct_`/`dim_` nhất quán xuyên bronze/silver (`refactor/silver-star-schema-naming`)

Rename thuần tuý (không đổi logic SQL/Python nào), 2 phần:

1. **`re_silver` → `fct_`/`dim_` thay vì `stg_` chung**: `stg_real_estate`/`stg_real_estate_rent`
   → `fct_real_estate`/`fct_real_estate_rent` (fact, grain = 1 listing); `stg_projects` →
   `dim_project`, `stg_locations_v1`/`stg_locations_v2` → `dim_location_v1`/`dim_location_v2`
   (dimension, join nhiều bảng master từ bronze). Folder `dbt/models/staging/` → tách thành
   `dbt/models/silver/facts/` + `dbt/models/silver/dimensions/`, thể hiện star schema qua chính
   cấu trúc thư mục — trước đây `stg_` dùng chung cho cả 2 vai trò khác nhau, che mất shape thật
   của model dù `docs/data-modeling.md` đã mô tả bằng lời từ lâu. `re_bronze` **không đổi tên**
   (không phải dbt model — Python ghi thẳng, gắn `stg_` vào đó sẽ hiểu nhầm theo convention dbt);
   **không thêm layer `int_`** (chưa có bước intermediate thật sự, thêm lúc này là
   over-engineer so với quy mô 1 người/weekly batch). `snp_*`/`vw_*`/`mart_*` giữ nguyên — prefix
   đã đúng vai trò từ trước.
2. **Bỏ prefix `j_` ở `src/_web2br/`**: `j_real_estate.py`/`j_real_estate_rent.py`/`j_projects.py`/
   `j_metadata.py` → `real_estate.py`/`real_estate_rent.py`/`projects.py`/`metadata.py` — prefix
   này từng dùng để phân biệt cùng tên file giữa `_web2br/` và `_br2sil/` (2 pipeline stage khác
   nhau cùng xử lý 1 domain entity), nhưng `_br2sil/` giờ chỉ còn `.pyc` mồ côi (xem nợ kỹ thuật,
   xoá ở Stage 5) nên `j_` không còn ý nghĩa phân biệt gì trong folder duy nhất còn lại.
3. **`re_bronze` cũng đổi sang `fct_`/`dim_`** (mở rộng quyết định 1 xuống cả bronze, sau khi
   review lại thấy giữ 2 từ vựng song song — `m_` ở bronze, `dim_`/`fct_` ở silver — cho cùng 1
   khái niệm chỉ gây rối chứ không thêm tín hiệu gì): `real_estate`/`real_estate_rent`/`projects`
   → `fct_real_estate`/`fct_real_estate_rent`/`fct_project` (raw, event-grain); `m_cities`/
   `m_districts`/`m_wards`/`m_streets`/`m_projects` (legacy v1, frozen) → `dim_city_v1`/
   `dim_district_v1`/`dim_ward_v1`/`dim_street_v1`/`dim_project_v1`; `m_cities_v2`/`m_wards_v2`/
   `m_streets_v2`/`m_projects_v2` (active) → `dim_city_v2`/`dim_ward_v2`/`dim_street_v2`/
   `dim_project_v2`; 3 seed `real_estate_type_mapping`/`district_geo_v1`/`ward_geo_v2` →
   `dim_real_estate_type_mapping`/`dim_district_geo_v1`/`dim_ward_geo_v2`. Tên bảng trùng giữa
   `re_bronze`/`re_silver` (VD `fct_real_estate` ở cả 2 schema) là chủ ý — cùng 1 entity, khác mức
   refine, schema phân biệt layer còn prefix phân biệt vai trò, 2 trục độc lập không lẫn nhau.

Đã cập nhật đồng bộ mọi reference: `ref()`/`source()` trong dbt (models/snapshots/tests/seeds),
`DBT_SELECT`/`STEPS`/module path/query đọc bronze (hardcode trong `real_estate.py`/
`real_estate_rent.py` để lấy danh sách district) trong `run_pipeline.py` và cả 2 Airflow DAG,
comment trong `src/_geocode/geocode_locations.py` (kể cả path CSV output), `docker-compose.yml`,
và toàn bộ doc (`technical-guides.md`, `data-modeling.md`, `interview-prep.md`) — **trừ**
`docs/blog_drafts/technical-writeup-2026-07-personal.md` (bài blog draft mô tả trạng thái tại
thời điểm viết 07/2026, cố tình giữ nguyên tên cũ vì sửa lại là viết lại lịch sử) và các mô tả
lịch sử về `src/_br2sil/` (code mồ côi đã xoá, tên bảng trong mô tả đó là tên tại thời điểm script
đó còn chạy, sửa lại sẽ sai sự thật).

**Đã chạy thật trên production BigQuery** (không chỉ đổi code): cả 20 bảng (5 silver + 15 bronze,
gồm 12 bảng raw + 3 seed) đổi tên bằng `ALTER TABLE ... RENAME TO` thay vì để dbt tạo bảng mới rồi
bỏ bảng cũ — giữ nguyên data/lịch sử tức thì, không tốn compute quét lại bronze. Verify: row count
khớp tuyệt đối trước/sau mọi rename; `dbt run`/`dbt snapshot`/`dbt test` chạy lại sau đó xác nhận
DAG resolve đúng bảng mới (`fct_real_estate` incremental MERGE 0 rows — không rescan bronze thừa;
`dbt snapshot` báo đúng 0 rows changed — rename không vô tình tạo lịch sử SCD2 giả); 28/31 test
pass, 3 warning còn lại (outlier giá/m2, FK `projectId` thiếu ~5%) là hành vi đã biết từ trước,
không liên quan tới rename.
