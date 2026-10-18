# CLAUDE.md

Convention và kiến trúc của dự án. Trạng thái, tiến độ, việc tồn đọng: xem `docs/status.md`.

## Dự án là gì

Scrape dữ liệu bất động sản từ [batdongsan.com.vn](https://batdongsan.com.vn), chuẩn hoá qua dbt, phục vụ phân tích thị trường BĐS Việt Nam (dashboard Looker Studio + series blog Substack). Dự án cá nhân, một mình maintain (DataSpi/spyno).

## Kiến trúc

```
batdongsan.com.vn --(src/scrapers/*.py, curl_cffi + BeautifulSoup)--> BigQuery re_bronze (raw)
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

**Stack**: Python 3.12, `requirements.txt` phẳng (không có pyproject.toml cho dependency; `pyproject.toml` chỉ cấu hình ruff). dbt-bigquery cho transform (`dbt/`). Không có test suite Python, test data quality nằm hết ở `dbt/tests/` và `_sources.yml`.

**Orchestration**: `src/orchestrator/run_pipeline.py` chạy `STEPS` tuần tự (scrape sale/rent/projects HCM+HN, `dbt run`, `dbt snapshot`, `dbt test`, cộng các step observability non-fatal), dừng ngay khi bước fatal lỗi. Live path là launchd (`src/ops/run_weekly_pipeline.sh` + `src/ops/com.dataspi.batdongsan-weekly.plist`) chạy bare-metal trên máy local (conda env `scrape_bds`), không qua Docker. Dùng launchd thay cron vì launchd chạy bù khi máy ngủ đúng giờ trigger; `caffeinate -i` giữ máy thức trong lúc chạy.

Không có Airflow/DAG (đã bỏ; bản cuối giữ ở git tag `airflow-final`): `STEPS` trong `run_pipeline.py` là nguồn duy nhất của thứ tự chạy. `docker-compose.yml` chỉ có service `pipeline` để build/test image, không scrape được trong container.

Plist đã cài ở `~/Library/LaunchAgents` trỏ đường dẫn tuyệt đối tới `src/ops/run_weekly_pipeline.sh`. Đổi vị trí hoặc tên file đó (hay Label) thì phải `launchctl bootout` + copy plist mới + `bootstrap` lại, và không làm vào ngày job chạy.

Location/project lineage (geocode + seed) và scrape metadata (`metadata.py`) là bước thủ công, không nằm trong lịch tuần, vì dbt không rebuild `dim_location_v1/v2`/`dim_project` hàng tuần.

## Ràng buộc scrape (quan trọng nhất)

- batdongsan.com.vn chặn IP cloud/CI runner: scrape bắt buộc chạy từ IP dân dụng (máy local). GitHub Actions chỉ lint/build/compile, không scrape.
- Site đặt sau Cloudflare Managed Challenge, áp dụng đại trà cho mọi truy cập (không phải bị flag riêng scraper). Challenge chạy JS kiểm tra tín hiệu automation:
  - `curl_cffi` với `impersonate="chrome124"` chỉ qua được tầng TLS/network, không đủ.
  - Playwright thường luôn set `navigator.webdriver = True` nên bị phát hiện ngay.
  - `patchright` vá cờ `webdriver` nhưng `headless=True` vẫn bị bắt qua tín hiệu khác (rendering, GPU, timing), patchright không vá hết được.
  - Chỉ chạy **headed** (`headless=False`) mới qua hoàn toàn. Cửa sổ Chrome được đẩy ra ngoài màn hình bằng `--window-position` để không hiện popup. Vì vậy bước warm-up cần máy có GUI session thật (máy Mac của maintainer), không chạy được trong container/headless server.
- Cách làm: `src/utils/scrape_session.py` mở browser headed đúng 1 lần mỗi TTL (`CF_SESSION_TTL_SECONDS`, mặc định 1200s) để lấy `cf_clearance`, cache ở `data/cf_session_cache.json`. Toàn bộ fetch hàng loạt sau đó vẫn dùng `curl_cffi` nhanh, tái sử dụng cookie này (cookie có hiệu lực toàn site, gồm cả API `/Product/ProductSearch/*`).
- Hệ quả thiết kế: không dựng scraper trong Docker container mà chưa giải bài toán headed browser.

## Convention dữ liệu

- **Naming**: `fct_` (fact, grain = 1 listing/event), `dim_` (dimension), `snp_` (snapshot SCD2), `vw_` (view tiện dụng), `mart_` (gold). Dùng đồng nhất ở cả `re_bronze` và `re_silver`; tên bảng trùng giữa 2 schema (VD `fct_real_estate`) là chủ ý: cùng entity, schema phân biệt layer, prefix phân biệt vai trò. Không thêm layer `int_` (quy mô 1 người/weekly batch chưa cần).
- **Cấu trúc dbt**: `dbt/models/silver/facts/` + `dbt/models/silver/dimensions/` thể hiện star schema qua thư mục. Python script scrape ở `src/scrapers/` đặt tên không prefix (`real_estate.py`, `real_estate_rent.py`, `projects.py`, `metadata.py`).
- **Cấu trúc thư mục**: package trong `src/` đặt tên theo vai trò, không prefix gạch dưới: `scrapers/` (web → bronze), `geocode/` (lineage thủ công), `orchestrator/`, `utils/`, `ops/` (wrapper + plist launchd). `content/` là bản nháp blog và ghi chú cá nhân, không liên quan pipeline. `docs/` là tài liệu kỹ thuật và cũng là nguồn GitHub Pages, nên không đặt nội dung cá nhân ở đó. Thư mục sinh ra khi chạy (`data/`, `logs/`) đã gitignore.
- **Đổi tên bảng/model**: cập nhật đồng bộ `ref()`/`source()`, `DBT_SELECT`/`STEPS`/module path trong `run_pipeline.py`, query bronze hardcode trong `src/scrapers/real_estate*.py`, comment trong `src/geocode/`, `docker-compose.yml` và doc. Trên BigQuery production dùng `ALTER TABLE ... RENAME TO` thay vì để dbt tạo bảng mới.
- **SCD2/CDC**: `snp_real_estate*` (dbt snapshot, `strategy: check`, `hard_deletes='new_record'`) giữ mọi lần thay đổi giá/diện tích/loại hình và đánh dấu tin bị gỡ. `fct_real_estate*` chỉ giữ bản mới nhất. `mart_real_estate*` build từ `fct_*`, không có lịch sử. Đọc trạng thái hiện tại qua `vw_real_estate_current`/`vw_real_estate_rent_current` (`status = 'active'/'closed'`). Lưu ý `dbt_is_deleted` là string `'True'/'False'`, không phải bool.
- **Observability**: Elementary (`dbt/packages.yml`, dataset `re_elementary`), anomaly test (tag `elementary`, severity warn) khai báo trong `dbt/models/silver/_sources.yml`. Các step observability là non-fatal (phần tử thứ 3 `fatal=False` trong `STEPS`). `src/ops/run_weekly_pipeline.sh` archive artifacts dbt và build `edr report`.
- **`dbt/profiles.yml`** (gitignored): path `keyfile` khác nhau giữa bare-metal và container Docker, xem `dbt/profiles.yml.example`.
- **Code đã xoá**: Malloy, report builder HTML và helper Postgres/Supabase cũ không còn trong repo (còn trong git history). `docs/reports/*.html` là artifact đông cứng từ pipeline đó, đừng regenerate.

## Quy ước làm việc

- Mỗi thay đổi lớn một branch/PR riêng. Lint bằng `ruff check .` (cấu hình trong `pyproject.toml`, có per-file-ignore cho vài file legacy).
- Module scraper/geocode không được làm việc gì khi import: logic nằm sau `if __name__ == "__main__"`. Import để lint hay kiểm tra mà lại scrape hoặc ghi BigQuery là lỗi (đã từng xảy ra với `metadata.py`, ghi đè `re_bronze.dim_*_v2`). Kiểm tra module resolve bằng `importlib.util.find_spec`, đừng import thật.
- Docker/CI: `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml` (lint + build/push GHCR), `dbt-ci.yml` (dbt compile, path-filter `dbt/**`). Scraper ghi CSV ra `data/` tương đối (gitignored), container phải mount thư mục này.

<!-- project-status-rule -->
## Phân vai tài liệu

- CLAUDE.md chỉ ghi convention và quy trình làm việc. **Không ghi trạng thái**, ngày tháng hay "đang làm gì".
- Trạng thái theo ngày (đã làm, chưa làm, quyết định đã chốt, câu hỏi chờ) chỉ ghi ở `docs/status.md`.
- Đầu phiên cần nắm tiến độ: dùng skill `project-status` (đọc delta, không quét lại codebase).
