# Hướng dẫn kỹ thuật — Vận hành pipeline

Tài liệu này dành cho dev đã setup xong môi trường (xem [Quickstart](quickstart.md)) và cần biết
**chạy gì, khi nào, và tại sao** để vận hành pipeline hằng ngày.

## 1) Kiến trúc & luồng dữ liệu

```
batdongsan.com.vn --(src/_web2br)--> BigQuery re_bronze
                                          |
                                        dbt staging
                                          v
                                    BigQuery re_silver
                                          |
                                     dbt marts
                                          v
                                    BigQuery re_gold
                                          |
                               Looker Studio dashboard
                       (BigQuery connector trực tiếp, khai báo qua
                        dbt exposure — dbt/models/marts/_exposures.yml)
```

Ba schema BigQuery: `re_bronze` (raw scrape) → `re_silver` (dbt staging, deduped/cleaned) →
`re_gold` (dbt marts, sẵn sàng cho báo cáo). Malloy (`malloy/`) và
`src/reports/report_builder.py` (→ `docs/reports/*.html`) không còn nằm trong pipeline sống —
xem mục 6.

Orchestration mặc định (giai đoạn 3) là **launchd bare-metal**: 1 job launchd gọi thẳng
`src/orchestrator/run_pipeline.py` qua `scripts/run_weekly_pipeline.sh`, không qua Docker, không
có process nào chạy liên tục giữa các lần. Airflow tự host (docker-compose, xem mục 2b) vẫn còn
trong repo như phương án thay thế cho ai muốn UI/retry/backfill của Airflow, đánh đổi lấy
`airflow-scheduler` + Postgres metadata phải chạy 24/7 chỉ để bắn 1 job/tuần — xem lý do đầy đủ ở
[CLAUDE.md § Giai đoạn 3](../CLAUDE.md).

## 2) Vận hành định kỳ — launchd bare-metal (mặc định)

**Vì sao bare-metal thay vì qua Docker**: batdongsan.com.vn chặn IP của cloud/CI runner — bước
scrape bắt buộc chạy từ IP dân dụng (máy cá nhân). Máy maintainer đã có sẵn conda env đúng
(`scrape_bds`, Python 3.12) nên không cần lớp Docker cho việc này — dùng Docker ở đây chỉ thêm
một dependency nữa (Docker Desktop cũng phải tự khởi động sau reboot) mà không có lợi ích tương
ứng cho 1 job chạy trên đúng 1 máy cố định.

Setup: copy `scripts/com.dataspi.batdongsan-weekly.plist` vào `~/Library/LaunchAgents/`, sửa
path nếu repo/conda env không nằm ở `/Users/spinokiem/...`, rồi:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.dataspi.batdongsan-weekly.plist
# test ngay không cần đợi thứ 2:
launchctl kickstart gui/$(id -u)/com.dataspi.batdongsan-weekly
```

Dùng `bootstrap`, không dùng `launchctl load` (lệnh cũ) -- trên macOS hiện đại (xác nhận trên
15.x Sequoia) `load` báo lỗi mù mờ "Input/output error" không rõ nguyên nhân thật sự, còn
`bootstrap` báo lỗi rõ ràng hơn hẳn. Gỡ job: `launchctl bootout gui/$(id -u)/com.dataspi.batdongsan-weekly`.

`StartCalendarInterval` bắn Thứ 2, 9h sáng. Khác cron thật: nếu máy đang ngủ đúng giờ đó, launchd
tự chạy bù ngay khi máy thức dậy thay vì bỏ qua hẳn lần chạy. `scripts/run_weekly_pipeline.sh` bọc
`caffeinate -i` để máy không ngủ giữa chừng, và ghi log ra `logs/pipeline_<timestamp>.log` (log
riêng của launchd — `StandardOutPath`/`StandardErrorPath` trong plist — ghi ra `logs/launchd.*.log`).

Các bước chạy tuần tự, **dừng ngay khi có bước lỗi** (`STEPS` trong `run_pipeline.py`):

1. `scrape_real_estate_hcm` / `scrape_real_estate_hn` — `src/_web2br/j_real_estate.py`
2. `scrape_real_estate_rent_hcm` / `scrape_real_estate_rent_hn` — `src/_web2br/j_real_estate_rent.py`
3. `scrape_projects_hcm` / `scrape_projects_hn` — `src/_web2br/j_projects.py`
4. `scrape_metadata` — `src/_web2br/j_metadata.py`
5. `dbt_run` — `dbt run --select stg_real_estate+ stg_real_estate_rent+`
6. `dbt_snapshot` — `dbt snapshot --select stg_real_estate+ stg_real_estate_rent+` (SCD2 history,
   xem mục 1b bên dưới)
7. `dbt_test` — `dbt test --select stg_real_estate+ stg_real_estate_rent+`

Sale ("bán") và cho thuê tách script/task riêng để bug ở nhánh này không ảnh hưởng nhánh kia —
2 schema BigQuery riêng (`re_bronze.real_estate` vs `re_bronze.real_estate_rent`), giá thuê là
giá/tháng nên không share price bin với giá bán.

Pipeline **không** rebuild `stg_locations_v1/v2` hay `stg_projects` mỗi tuần — đó là dữ liệu
tham chiếu gần như tĩnh (city/district/ward/project + lat/lng geocode), chỉ cần rebuild thủ
công khi nó thực sự thay đổi (xem mục 3).

Debug khi có bước lỗi: mở log file mới nhất trong `logs/` (`ls -t logs/pipeline_*.log | head -1`).

### 1b) Lịch sử thay đổi listing (SCD2/CDC)

`stg_real_estate`/`stg_real_estate_rent` chỉ giữ bản mới nhất mỗi tuần (dedup theo `scraped_at`).
`dbt/snapshots/snp_real_estate.sql` và `snp_real_estate_rent.sql` (dbt `snapshot`,
`strategy: check`) giữ lại **mọi** lần giá/diện tích/loại hình/... thay đổi, mỗi version 1 dòng
với `dbt_valid_from`/`dbt_valid_to`. `hard_deletes='new_record'` xử lý tin bị gỡ/bán xong: khi 1
`product_id` biến mất khỏi `stg_real_estate`, snapshot đóng dòng cũ và insert 1 dòng mới
`dbt_is_deleted = 'True'` làm "trạng thái hiện tại".

Không cần nhớ tên cột nội bộ của dbt — đọc trạng thái hiện tại (active/closed) qua
`vw_real_estate_current` / `vw_real_estate_rent_current`:

```sql
select * from re_gold.vw_real_estate_current where status = 'active';
```

Xem lịch sử đầy đủ 1 listing thì query thẳng bảng snapshot:

```sql
select * from re_silver.snp_real_estate
where product_id = '...'
order by dbt_valid_from;
```

## 2b) Vận hành định kỳ (tuỳ chọn) — Airflow self-hosted, docker-compose

**Vì sao tự host thay vì Airflow managed/cloud**: batdongsan.com.vn chặn IP của cloud/CI
runner — bước scrape bắt buộc phải chạy từ IP dân dụng (máy cá nhân). Container Docker chạy
trên máy local vẫn ra internet bằng IP của máy đó (NAT qua Docker Engine), nên Airflow ở đây
chạy self-hosted qua `docker-compose.yml` (LocalExecutor — một máy, task vốn đã tuần tự do
ràng buộc 1 IP scrape, không cần CeleryExecutor/Redis) thay vì managed Airflow trên cloud.

Setup lần đầu / chạy hằng ngày: xem
[Quickstart mục 6](quickstart.md#6-cách-khác--docker--airflow-self-hosted).

DAG chính — `dags/pipeline_weekly_dag.py`, lịch `0 9 * * 1` (Thứ 2, 9h sáng, đồng bộ với lịch
launchd ở mục 2), `catchup=False`, `retries=2`. Các task giống hệt danh sách 7 bước ở mục 2, chạy
tuần tự và **dừng ngay khi có task lỗi**.

Debug khi có task lỗi: mở Airflow UI (`localhost:8080`) → DAG → task → Logs, hoặc
`docker compose logs airflow-scheduler`.

## 3) Vận hành thủ công: rebuild location lineage

**Khi nào cần chạy mục này:** có quận/phường mới xuất hiện (VD: sáp nhập hành chính), hoặc
vừa geocode lại lat/lng cho `district_geo_v1` / `ward_geo_v2`.

Cách chạy chính: trigger DAG `lineage_rebuild` (`dags/lineage_rebuild_dag.py`) thủ công trên
Airflow UI — `schedule=None`, không nằm trong lịch tuần. Các bước bên dưới mô tả đúng những gì
DAG đó chạy, hữu ích khi debug từng bước hoặc chạy bare-metal.

### 3.1 Geocode district/ward mới (nếu cần)

```bash
python -m src._geocode.geocode_locations
```

- Cần `GOOGLE_MAPS_API_KEY` trong `.env` (khóa riêng cho Geocoding API, **không** dùng chung
  service account của `src/utils/gcp_conn.py`).
- Đọc toàn bộ district (v1) và ward (v2) hiện có trên BigQuery `re_bronze`, geocode qua Google
  Geocoding API, ghi kết quả đè lên `dbt/seeds/district_geo_v1.csv` và `dbt/seeds/ward_geo_v2.csv`.
- Địa chỉ không geocode được sẽ có `lat`/`lng` để trống (NULL sau khi seed) — không phải lỗi
  script, cần kiểm tra thủ công nếu tỷ lệ trống cao.

### 3.2 Nạp seed & rebuild lineage

```bash
cd dbt
dbt seed --select district_geo_v1 ward_geo_v2
dbt run --select stg_locations_v1+ stg_locations_v2+ stg_projects+
dbt test --select stg_locations_v1+ stg_locations_v2+ stg_projects+
```

`stg_locations_v1+`/`stg_locations_v2+` kéo theo cả `mart_real_estate` vì mart join trực tiếp
vào hai model này để lấy tên quận/phường + lat/lng — không cần chạy thêm lệnh riêng cho mart.

Nếu chỉ seed lat/lng thay đổi (không có district/ward mới), có thể bỏ qua bước 3.1 và chạy
thẳng bước 3.2.

## 4) Data tests

- **Schema tests** (`dbt/models/staging/_staging.yml`): `unique`/`not_null` trên khóa chính
  của từng model và seed (`unique_id`, `product_id`, `districtId`, `wardId`, `projectId`,
  `raw_token`...).
- **Custom tests** (`dbt/tests/`):
  - `assert_known_real_estate_type.sql` — fail nếu xuất hiện `real_estate_type` không khớp
    seed `real_estate_type_mapping` (dấu hiệu site đổi slug loại BĐS).
  - `assert_no_negative_price_or_area.sql` — fail nếu `price_num`/`area_num` âm (bug parse).

Chạy toàn bộ test:

```bash
cd dbt && dbt test
```

Chạy test cho riêng một nhánh (khớp với phạm vi `dbt run` tương ứng):

```bash
dbt test --select stg_real_estate+
```

## 5) dbt docs (xem lineage & catalog)

```bash
cd dbt
dbt docs generate --project-dir . --profiles-dir .
dbt docs serve --project-dir . --profiles-dir . --port 8080
```

Mở `http://localhost:8080`. Nếu `mart_real_estate` chưa từng được `dbt run`, bước `generate`
sẽ cảnh báo "Dataset re_gold not found" khi build catalog — không chặn việc serve, chỉ thiếu
sample data/column stats cho model đó.

## 6) Dashboard (Looker Studio) & Malloy/Reports (ngừng dùng)

- Dashboard sống: [Looker Studio](https://lookerstudio.google.com/reporting/9e21618f-97dc-4480-b101-cbda26b9b2a5),
  nối trực tiếp BigQuery `re_gold.mart_real_estate` qua BigQuery connector — không qua semantic
  layer trung gian. Lineage khai báo bằng dbt exposure ở `dbt/models/marts/_exposures.yml`
  (`depends_on: ref('mart_real_estate')`), nên hiện trong `dbt docs generate` / DAG.
- Malloy (`malloy/malloy_publisher/real_estate.malloy`) và pipeline báo cáo HTML tĩnh
  (`src/reports/report_builder.py` → `docs/reports/HCM-HN_*.html`) **không còn dùng** — cả hai
  trỏ vào Supabase/Postgres cũ, từ trước khi pipeline chuyển sang BigQuery. `docs/reports/*.html`
  hiện tại là artifact đông cứng từ lần build cuối (2026-05-20), không còn regenerate. Xem mục
  nợ kỹ thuật trong [CLAUDE.md](../CLAUDE.md) — dọn dẹp ở Stage 5.

## 7) Docker & Airflow — layout container

*Chỉ cần đọc mục này nếu bạn dùng path Airflow tuỳ chọn (mục 2b) hoặc muốn build/test bằng
Docker — pipeline chạy mặc định (mục 2) không phụ thuộc gì ở đây.*

- `Dockerfile` (root): image `pipeline` — Python 3.12 + `requirements.txt` + dbt CLI, dùng cho
  cả `docker run` trực tiếp lẫn task Airflow. `PYTHONPATH=/app` set sẵn trong image (trước đây
  chỉ set trong `.vscode/settings.json`, hỏng ngoài VS Code).
- `airflow/Dockerfile`: extend `apache/airflow` với `requirements.txt` cài vào venv của chính
  image Airflow (không dùng `pip install --user` — image Airflow chạy trong venv riêng, user
  site-packages không thấy được).
- `docker-compose.yml`: service `pipeline` (chạy pipeline độc lập) + cụm Airflow
  (`airflow-metadata-db` — Postgres **riêng**, không liên quan `DB_*`/Supabase cũ của Malloy;
  `airflow-init`, `airflow-webserver`, `airflow-scheduler`).
- Secrets: `env_file: .env` + bind-mount read-only `gcp_service_account.json` — không bake vào
  image layer nào (xem `.dockerignore`).
- `data/` bị gitignore (dump scrape output) nên không có sẵn khi clone mới — image tự tạo
  thư mục này (`RUN mkdir -p data` trong `Dockerfile`) và `docker-compose.yml` bind-mount
  `./data` vào cả service `pipeline` lẫn các container Airflow, vì `src/_web2br/*.py` ghi CSV
  ra path tương đối `data/...` theo mặc định.

## 8) CI/CD — GitHub Actions

GitHub-hosted runner **không** tới được batdongsan.com.vn (bị chặn) — CI không bao giờ chạy
scrape thật hay orchestration, việc đó ở lại hoàn toàn trên máy local (launchd, mục 2 — hoặc
Airflow, mục 2b, nếu bạn chọn path đó). CI chỉ làm 3 việc, đều là fast feedback trước khi merge:

- `.github/workflows/ci.yml`:
  - job `lint` — `ruff check .` (cấu hình ở `pyproject.toml`).
  - job `docker-build-push` — build `Dockerfile` mọi PR để validate; khi merge vào `main`,
    push lên GHCR (`ghcr.io/dataspi/scrape-batdongsan-data`, tag `latest` + sha).
- `.github/workflows/dbt-ci.yml`: `dbt compile --target ci`, chỉ chạy khi PR đụng `dbt/**`.
  Target `ci` (trong `dbt/profiles.yml.example`) dùng `keyfile_json` inline từ secret
  `GCP_CREDENTIALS_JSON` thay vì file — tái dùng đúng pattern `src/utils/gcp_conn.py` đã có
  sẵn cho ngữ cảnh GitHub Actions.

## 9) Publish lên GitHub Pages

`docs/` là source của GitHub Pages (Settings → Pages → `main` / `docs`), publish dưới dạng
HTML tĩnh, **không dùng Jekyll** (`docs/.nojekyll`) — không có build step, push lên `main` là
lên site ngay.

- `docs/index.html` — trang portal chính (giới thiệu, sơ đồ pipeline, link báo cáo/dashboard).
- `docs/reports/` — báo cáo HTML do `report_builder.py` sinh ra.
- `docs/figs/` — ảnh minh hoạ.
- `docs/quickstart.md`, `docs/technical-guides.md` — tài liệu kỹ thuật, đọc trực tiếp trên
  GitHub (không render qua Pages), `docs/index.html` link thẳng ra GitHub blob view.

Sau khi có báo cáo mới trong `docs/reports/`, thêm một card link trong phần `#reports` của
`docs/index.html` rồi commit/push như bình thường.

## 10) Troubleshooting

- **Lỗi kết nối BigQuery**: kiểm tra `gcp_service_account.json` tồn tại ở root và
  `dbt/profiles.yml` (copy từ `dbt/profiles.yml.example`) trỏ đúng file.
- **`dbt run`/`dbt test` lỗi credentials khi chạy qua Airflow nhưng OK khi chạy bare-metal**:
  `dbt/profiles.yml` có path `keyfile` tuyệt đối, path này khác nhau giữa bare-metal và trong
  container Airflow (`/opt/airflow/repo/gcp_service_account.json`) — xem comment trong
  `dbt/profiles.yml.example`.
- **Task scrape lỗi `OSError: Cannot save file into a non-existent directory: 'data'`**:
  `data/` bị gitignore nên không có sẵn ở máy mới — kiểm tra `docker-compose.yml` đã mount
  `./data` vào đúng service/container chưa (xem mục 7).
- **`launchctl load` báo "Input/output error"**: lệnh cũ, báo lỗi mù mờ trên macOS hiện đại —
  dùng `launchctl bootstrap gui/$(id -u) <path plist>` thay thế, lỗi sẽ rõ hơn nhiều (thường là
  file plist chưa được copy vào `~/Library/LaunchAgents/`, hoặc job đã load rồi).
- **launchd job chạy nhưng không thấy log file mới trong `logs/`**: `launchctl print
  gui/$(id -u)/com.dataspi.batdongsan-weekly` xem job có load không; nếu báo "could not find
  service", `bootstrap` lại đúng path plist trong `~/Library/LaunchAgents/`. Nếu job có load
  nhưng vẫn lỗi ngay từ đầu (trước khi kịp tạo log file trong `logs/`), xem
  `logs/launchd.err.log` (path set trong
  `StandardErrorPath` của plist) — thường là do path conda env trong
  `scripts/run_weekly_pipeline.sh` không khớp máy đang chạy.
- **DAG không xuất hiện trên Airflow UI hoặc báo import error**: `docker compose exec
  airflow-scheduler airflow dags list-import-errors`.
- **`dbt run` báo thiếu source table**: bước scrape (`src/_web2br/*.py`) chưa chạy hoặc chạy
  lỗi — kiểm tra log của đúng bước đó trước khi rerun dbt (Airflow UI → task → Logs).
- **Geocode script báo `GOOGLE_MAPS_API_KEY not set`**: thêm key vào `.env`, khóa này tách
  biệt với service account BigQuery.
- **Không có listing mới sau khi scrape**: website nguồn có thể đã đổi cấu trúc HTML, cần cập
  nhật lại selector trong `src/_web2br/`.
- **`assert_known_real_estate_type` fail**: site có loại BĐS mới chưa map — thêm dòng vào
  `dbt/seeds/real_estate_type_mapping.csv` rồi `dbt seed --select real_estate_type_mapping`.

## Điều hướng

- Về [Trung tâm tài liệu](README.md)
- Sang [Quickstart](quickstart.md)
- Về [Trang chủ dự án (GitHub Pages)](https://dataspi.github.io/scrape-batdongsan-data/)
