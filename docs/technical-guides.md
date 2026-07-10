# Hướng dẫn kỹ thuật — Vận hành pipeline

Tài liệu này dành cho dev đã setup xong môi trường (xem [Quickstart](quickstart.md)) và cần biết
**chạy gì, khi nào, và tại sao** để vận hành pipeline hằng ngày.

## 1) Kiến trúc & luồng dữ liệu

```
batdongsan.com.vn --(src/_web2br)--> BigQuery re_bronze
                                          |
                                   dbt staging (src/_br2sil ported to SQL)
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
`re_gold` (dbt marts, sẵn sàng cho báo cáo). `src/_br2sil/*.py` là bản Python gốc, đã được
port sang dbt staging models — không dùng nữa cho luồng chính, giữ lại để tham chiếu.

## 2) Vận hành định kỳ (weekly, tự động qua crontab)

Toàn bộ pipeline chạy trên máy local (không dùng GitHub Actions/Airflow) vì
batdongsan.com.vn chặn IP của cloud runner — bước scrape bắt buộc phải chạy từ máy cá nhân.

```bash
python -m src.orchestrator.run_pipeline
```

Các bước chạy tuần tự, **dừng ngay khi có bước lỗi** (xem `src/orchestrator/run_pipeline.py`):

1. `scrape_real_estate` — `src/_web2br/j_real_estate.py`
2. `scrape_projects` — `src/_web2br/j_projects.py`
3. `scrape_metadata` — `src/_web2br/j_metadata.py`
4. `dbt run --select stg_real_estate+` — rebuild `stg_real_estate` và mọi model downstream
   (bao gồm `mart_real_estate`)
5. `dbt test --select stg_real_estate+`

Pipeline **không** rebuild `stg_locations_v1/v2` hay `stg_projects` mỗi tuần — đó là dữ liệu
tham chiếu gần như tĩnh (city/district/ward/project + lat/lng geocode), chỉ cần rebuild thủ
công khi nó thực sự thay đổi (xem mục 3).

Crontab mẫu (`crontab -e`):

```
0 9 * * 1 cd /path/to/scrape-batdongsan-data && ./venv/bin/python -m src.orchestrator.run_pipeline >> logs/pipeline_cron.log 2>&1
```

Debug khi có bước lỗi: đọc `logs/pipeline_cron.log` — stdout/stderr của đúng bước lỗi được in
ra, pipeline dừng ngay tại đó nên không cần đoán bước nào đã chạy.

## 3) Vận hành thủ công: rebuild location lineage

**Khi nào cần chạy mục này:** có quận/phường mới xuất hiện (VD: sáp nhập hành chính), hoặc
vừa geocode lại lat/lng cho `district_geo_v1` / `ward_geo_v2`.

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

## 7) Publish lên GitHub Pages

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

## 8) Troubleshooting

- **Lỗi kết nối BigQuery**: kiểm tra `gcp_service_account.json` tồn tại ở root và
  `dbt/profiles.yml` (copy từ `dbt/profiles.yml.example`) trỏ đúng file.
- **`dbt run` báo thiếu source table**: bước scrape (`src/_web2br/*.py`) chưa chạy hoặc chạy
  lỗi — kiểm tra log của đúng bước đó trước khi rerun dbt.
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
