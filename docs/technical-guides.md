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
                    +---------------------+---------------------+
                    v                                           v
        Malloy (malloy/malloy_publisher)              src/reports/report_builder.py
                    |                                           |
             Looker Studio dashboard                   docs/reports/*.html (GitHub Pages)
```

Ba schema BigQuery: `re_bronze` (raw scrape) → `re_silver` (dbt staging, deduped/cleaned) →
`re_gold` (dbt marts, sẵn sàng cho báo cáo).

Từ giai đoạn 2, toàn bộ orchestration chạy qua **Airflow tự host** (docker-compose, xem mục 2)
thay vì crontab gọi thẳng `src/orchestrator/run_pipeline.py`. Module đó vẫn còn trong repo như
phương án dự phòng thủ công, nhưng đường chính giờ là 2 DAG trong `dags/`.

## 2) Vận hành định kỳ — Airflow (self-hosted, docker-compose)

**Vì sao tự host thay vì Airflow managed/cloud**: batdongsan.com.vn chặn IP của cloud/CI
runner — bước scrape bắt buộc phải chạy từ IP dân dụng (máy cá nhân). Container Docker chạy
trên máy local vẫn ra internet bằng IP của máy đó (NAT qua Docker Engine), nên Airflow ở đây
chạy self-hosted qua `docker-compose.yml` (LocalExecutor — một máy, task vốn đã tuần tự do
ràng buộc 1 IP scrape, không cần CeleryExecutor/Redis) thay vì managed Airflow trên cloud.

Setup lần đầu / chạy hằng ngày: xem [Quickstart mục 3](quickstart.md#3-build--khởi-động).

DAG chính — `dags/pipeline_weekly_dag.py`, lịch `0 9 * * 1` (Thứ 2, 9h sáng, thay thế crontab
cũ), `catchup=False`, `retries=2`. Các task chạy tuần tự, **dừng ngay khi có task lỗi**, đúng
semantics của `STEPS` cũ trong `src/orchestrator/run_pipeline.py`:

1. `scrape_real_estate_hcm` / `scrape_real_estate_hn` — `src/_web2br/j_real_estate.py`
2. `scrape_real_estate_rent_hcm` / `scrape_real_estate_rent_hn` — `src/_web2br/j_real_estate_rent.py`
3. `scrape_projects_hcm` / `scrape_projects_hn` — `src/_web2br/j_projects.py`
4. `scrape_metadata` — `src/_web2br/j_metadata.py`
5. `dbt_run` — `dbt run --select stg_real_estate+ stg_real_estate_rent+`
6. `dbt_test` — `dbt test --select stg_real_estate+ stg_real_estate_rent+`

Sale ("bán") và cho thuê tách script/task riêng để bug ở nhánh này không ảnh hưởng nhánh kia —
2 schema BigQuery riêng (`re_bronze.real_estate` vs `re_bronze.real_estate_rent`), giá thuê là
giá/tháng nên không share price bin với giá bán.

Pipeline **không** rebuild `stg_locations_v1/v2` hay `stg_projects` mỗi tuần — đó là dữ liệu
tham chiếu gần như tĩnh (city/district/ward/project + lat/lng geocode), chỉ cần rebuild thủ
công khi nó thực sự thay đổi (xem mục 3).

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

## 6) Semantic modeling (Malloy) & Reports

- Model Malloy: `malloy/malloy_publisher/real_estate.malloy` — **lưu ý: hiện vẫn trỏ vào
  Supabase, chưa migrate theo BigQuery** sau lần đổi pipeline sang BigQuery. Cần cập nhật
  connection trước khi dùng lại các query trong `malloy/_analysing/` và
  `malloy/_materialize/materialize.malloysql`.
- Sinh báo cáo HTML tĩnh:

  ```bash
  python src/reports/report_builder.py
  ```

  Ghi ra `docs/reports/HCM-HN_prj.html` và `docs/reports/HCM-HN_districts.html` — nằm luôn
  trong thư mục publish của GitHub Pages, không cần copy thủ công.

## 7) Docker & Airflow — layout container

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
scrape thật hay các DAG orchestration, việc đó ở lại hoàn toàn trên Airflow local (mục 2).
CI chỉ làm 3 việc, đều là fast feedback trước khi merge:

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
