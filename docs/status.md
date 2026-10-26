---
last_verified: 2026-10-26
verified_commit: 2c4618c
owner: DataSpi
---

# Trạng thái dự án (snapshot)

Tài liệu DUY NHẤT chứa trạng thái theo ngày. README và CLAUDE.md chỉ giữ quy ước và cấu trúc.

## Phạm vi

Scrape batdongsan.com.vn (sale/rent/projects, HCM + HN) → BigQuery `re_bronze` → dbt → `re_silver` → `re_gold` → Looker Studio (đang thử thay bằng site tĩnh ở 2 repo phụ, xem mục "Dashboard site tĩnh"). Dự án cá nhân, một người maintain. Chạy tuần bằng launchd trên máy local (scrape bắt buộc IP dân dụng).

## Đã làm

- Pipeline 3 tầng bronze/silver/gold trên BigQuery + dbt, Looker Studio nối thẳng `re_gold` (giai đoạn 1).
- Docker, Airflow DAG, CI/CD GitHub Actions, docs (giai đoạn 2, Stage 0–4 xong). Airflow DAG đã bị xoá khỏi repo 2026-10-16 (xem bên dưới), bản cuối còn Airflow ở git tag `airflow-final`.
- Live scheduler chuyển từ Airflow sang launchd (`src/ops/run_weekly_pipeline.sh`, Thứ 2 9h) (giai đoạn 3, `feat/scd2-launchd-scheduling`). Wrapper nằm ở `scripts/` đến PR #14 (2026-10-18).
- SCD2 listing qua dbt snapshot `snp_real_estate*` + view `vw_real_estate_current`/`vw_real_estate_rent_current` (giai đoạn 3).
- Đổi tên `fct_`/`dim_` xuyên bronze/silver, bỏ prefix `j_`; đã rename 20 bảng trên production BigQuery, test 28/31 pass (giai đoạn 4, 2026-09-23, `refactor/silver-star-schema-naming`).
- Fix parse giá VN, hash số điện thoại agent ở silver facts (2026-10-01, `7974530`).
- Helper Cloudflare clearance session cho scraper (`src/utils/scrape_session.py`, 2026-10-01, `5f6f049`).
- Code Elementary observability + healthcheck ping + Slack alert trong run tuần, merge vào main (2026-10-16, `feat/elementary-observability`).
- Elementary đã chạy lên production: dataset `re_elementary` tồn tại, có 2 `dbt_invocations` và 57 dòng `data_monitoring_metrics` (kiểm 2026-10-16). Baseline anomaly vẫn đang tích.
- CI static checks merge vào main (2026-10-16, PR #2 `ci/static-checks`): ruff check + format cả repo, compileall, sqlfluff, shellcheck, actionlint, plist, compose config, `dbt parse` không cần credential. Test dbt và phần CI/CD còn lại do session riêng làm.
- Scrape hôm nay 2026-10-16 chạy được qua orchestrator: 6 bước scrape, 3.627 dòng vào bronze (sale 480, rent 450, projects 2.697).
- PR #3 `feat/pipeline-run-log` merge vào main (2026-10-16, `496b614`):
    - Log vận hành vào BigQuery `re_meta` (`pipeline_runs`, `pipeline_step_runs`, view `vw_pipeline_runs`), gồm rows_loaded và error tail theo step.
    - Overlap lock `flock` trong wrapper bash, timeout từng step (`PIPELINE_STEP_TIMEOUT_S`, mặc định 3600s) kill cả process group.
    - Bronze sale/rent idempotent theo `(date_scraped, product_id)`: chạy lại cùng ngày thay vì nhân đôi dòng.
    - Cửa sổ Chrome warm-up Cloudflare được minimize qua CDP (macOS kẹp `--window-position` về lại màn hình, nên không giấu được bằng toạ độ).
- PR #4 `chore/remove-airflow` merge vào main (2026-10-16, `4e3ee1a`): xoá `dags/`, `airflow/Dockerfile` và các service Airflow trong `docker-compose.yml` (chỉ còn service `pipeline`); CI `compileall` không còn `dags`; docs cập nhật. Lý do ở mục Quyết định.
- PR #5 `fix/scrape-warmup-and-run-ui` (2026-10-16, `34c28f1`): chạy tay `run_weekly_pipeline.sh` có TTY thì in tiến độ từng step, tóm tắt cuối và thông báo macOS; dưới launchd (không TTY) hành vi giữ nguyên. Exit code lấy từ `PIPESTATUS`.
- PR #6 `fix/scrape-pagination` (2026-10-16, `a8bda1a`): site đổi pager sang `<div class="re__pagination-number" data-page>`, nên trước đó mỗi quận chỉ scrape trang đầu (20 tin) mà step vẫn báo Done. Đã đọc `data-page` ở `real_estate.py`, `real_estate_rent.py`, `projects.py`.
- PR #8 `feat/scrape-resilience` (2026-10-16, `55ce7a5`; retarget của #7): retry 429/5xx có backoff, `scrape_health.py` đổi số trang lỗi thành exit code (0 đủ, 2 partial khi ≥50% trang, 1 dưới đó), load bronze từng quận ngay khi scrape xong, step scrape non-fatal, run kết thúc "partial" (exit 3, healthchecks vẫn ping thành công + cảnh báo Slack), watermark incremental của `fct_real_estate*` đổi `>` thành `>=`.
- PR #9 `fix/edr-report-caffeinate` (2026-10-18): `caffeinate -i` bọc cả bước build Elementary report, vì Mac idle-sleep sau khi pipeline xong làm `edr` chạy rất chậm và `alarm()` không đếm lúc máy ngủ.
- Dọn repo, merge vào main 2026-10-18:
    - PR #10 `chore/remove-dead-code`: xoá `malloy/`, `sql/`, `src/malloy_py`, `src/reports`, `src/_pg2bq`, `malloy_cli_runner`, `sqlalchemy_conn`, `getting_metadata`, `.github/copilot-instructions.md`; `common_tools.py` chỉ còn `setup_logging`; bỏ 6 dependency (`malloy`, `plotly`, `jinja2`, `apscheduler`, `sqlalchemy`, `psycopg2-binary`). Đây là Stage 5 dọn code cũ.
    - PR #11 `refactor/src-naming`: `src/_web2br` thành `src/scrapers`, `src/_geocode` thành `src/geocode`; `scrapers/metadata.py` bọc trong `main()` với `__main__` guard (trước đó import là scrape và `WRITE_TRUNCATE` vào `re_bronze.dim_*_v2`).
    - PR #12 `chore/content-layout`: `docs/blog_drafts/` và `docs/interview-prep.md` sang `content/`.
    - PR #14 `refactor/ops-folder`: `scripts/` thành `src/ops/` (`PROJECT_ROOT` trong wrapper lên 2 cấp).
    - PR #13 `chore/runtime-dirs` (merge sau #14, phải gộp main để hết conflict đổi tên file): `edr report --target-path logs/edr_target`, để `edr_target/` không còn sinh ra ở gốc repo. Chưa thấy chạy thật; xác nhận sau lần chạy tuần kế tiếp.
- `src/ops/launchd_ctl.py` (2026-10-18, `38cb952`, trên main): CLI stdlib cho job launchd (`status`, `schedule`, `install`, `run`, `uninstall`). Nguồn thật là plist trong `src/ops/`; `install`/`schedule` copy sang `~/Library/LaunchAgents` rồi nạp lại.
- 2026-10-19: repo chuyển từ `~/scrape-batdongsan-data` sang `~/wrk/scrape-batdongsan-data` (gom mọi repo vào `~/wrk`). Đã sửa đường dẫn tuyệt đối trong `src/ops/com.dataspi.batdongsan-weekly.plist` (3 chỗ) và `dbt/profiles.yml` (gitignored), cài lại plist vào `~/Library/LaunchAgents`, job đã load. Plist (lịch **Thứ 2 00:25**, khớp bản đang cài) và xử lý quận trống của scraper (`NoListingsError`: quận không có tin bị bỏ qua, không tính là trang lỗi) commit 2026-10-26 ở branch `chore/wrk-move-empty-districts`, **PR đang mở**. Hai lần chạy tự động gần nhất (đọc từ log, kiểm 2026-10-26):
    - 2026-10-19 (bắt đầu 00:25, đường dẫn cũ): `scrape_real_estate_hcm` Partial (exit 2), `scrape_real_estate_rent_hcm` Failed (exit 1), các bước còn lại Done; kết thúc "partial data".
    - 2026-10-26 (đường dẫn mới `~/wrk`, dbt xong lúc 11:33): `scrape_real_estate_hcm` Failed (timeout 3600s), các bước còn lại Done; kết thúc "partial data", exit 3. Xác nhận job chạy được từ đường dẫn mới.

### Dashboard site tĩnh thay Looker (2 repo phụ, tạo 2026-10-19)

Hai repo phụ cùng cấp với repo này trong `~/wrk/`, đều public, deploy GitHub Pages bằng GitHub Actions từ **CSV đã tổng hợp được commit**, nên CI không cần key. Key GCP của repo này chỉ dùng ở máy local qua biến môi trường/đường dẫn (không copy vào repo phụ); script trích xuất chỉ `SELECT` và không xuất dữ liệu từng tin. Looker Studio vẫn chạy song song (dbt exposure `dashboard_gia_bds_hcm_hn`; chưa có exposure cho 2 site mới).

- `DataSpi/scrape-bds-rp-evidence` → <https://dataspi.github.io/scrape-bds-rp-evidence/>
    - Evidence **legacy** 40.x (SQL DuckDB WASM chạy trong trình duyệt). PR #1 (prototype + Pages), #2 (dữ liệu thật, chung cư snapshot 16–18/10/2026), #3 (site theo kỳ: home Giá mua/Giá thuê, template `[period].md`, mục "So với kỳ trước", trang thuê có P/R ratio) đều merge 2026-10-19, deploy xanh.
    - Đọc `re_gold.mart_real_estate_period` / `mart_real_estate_rent_period` (PR #16 của repo này) qua `scripts/extract_data.py`; dùng **trung bình** (khớp bài P2). Có chung cư mua và thuê cho kỳ 2026-07 và 2026-10; nhà đất mua chỉ kỳ 2026-07 (chưa cào nhà đất kỳ 10); thuê nhà đất "sắp có".
    - Bản build local khoảng 179 MB (kiểm 2026-10-26; có 2 file DuckDB WASM, trình duyệt tải một file 30+ MB lần đầu); chữ trên giao diện chung (sidebar, nhãn tháng trên trục) còn tiếng Anh.
- `DataSpi/scrape-bds-rp-astro` → <https://dataspi.github.io/scrape-bds-rp-astro/>
    - Astro + Observable Plot: chart là SVG dựng lúc build, **không có JavaScript** ở trình duyệt, `dist/` khoảng 168 KB (kiểm 2026-10-26). Hai commit 2026-10-19 (`87abaf3` scaffold, `188e6be` dữ liệu thật, trang theo bài P2), deploy xanh.
    - Chỉ chung cư mua, **một snapshot**: tin thấy trong cửa sổ 14 ngày tính từ đợt cào gần nhất của mỗi thành phố, đọc `mart_real_estate` qua `scripts/export_data.py`; dùng **trung vị**; mỗi thành phố một URL (`/ho-chi-minh/`, `/ha-noi/`). Chưa có so sánh theo kỳ, chưa có trang thuê hay nhà đất.
- Observable Framework: chưa dựng.
- Hai site **không cho cùng một con số** vì định nghĩa khác nhau. Ví dụ HCM: giá/m² 84,2 (trung bình, Evidence) và 68,0 (trung vị, Astro); Quận 1 240,9 và 206,7; số tin có giá 14.973 và 14.977.

### Đang chờ merge (chưa vào main)

- PR #16 `feat/report-period-models` (2026-10-19, `2c4618c`, **đang mở**; nội dung theo mô tả PR, chưa tự chạy lại dbt): dựng báo cáo theo kỳ từ bronze để so sánh tháng 7 và tháng 10 cùng điều kiện. Lọc `date_scraped` trên `mart_real_estate` không dùng được cho kỳ cũ vì mart chỉ giữ bản cào mới nhất của mỗi tin, và `snp_*` mới bắt đầu từ 2026-09-23.
    - Seed `dim_report_period` (2026-07: 10–14/07, 2026-10: 16–18/10); `fct_real_estate(_rent)_period` (silver) và `mart_real_estate(_rent)_period` (gold), grain tin × kỳ. Logic làm sạch chuyển vào macro `clean_sale_listings`/`clean_rent_listings`, body mart vào `sale_mart`/`rent_mart`; SQL compile của `fct_*`/`mart_*` hiện có không đổi (đã so sánh bản compile trước/sau). Test: `(period, product_id)` không trùng, các kỳ không chồng nhau.
    - **Các bảng đã được tạo trên BigQuery production** (`re_bronze.dim_report_period`, `re_silver.fct_*_period`, `re_gold.mart_*_period`), chỉ thêm bảng mới. Repo Evidence (đã merge) đang đọc các bảng này, nhưng code dbt tạo ra chúng chưa nằm trong `main`.
    - `dbt test` liên quan: PASS=31, WARN=3 (cả 3 có từ trước). Các model `*_period` không nằm trong `DBT_SELECT` của lịch tuần; thêm kỳ mới chạy tay `dbt seed -s dim_report_period` + `dbt run -s dim_report_period+`.
    - CI đỏ do `launchd_ctl.py` chưa format (từ `38cb952` trên main) và sqlfluff không load macro; sửa ở `cfee540` (thêm `load_macros_from_path = dbt/macros` vào `.sqlfluff`), CI xanh 2026-10-26.
    - Đối chiếu với bài cũ: thuê HCM 7.674 tin và nhà riêng HCM 9,20 tỷ / 129,2 tr/m² khớp bài tháng 7; chung cư tháng 7 lệch nhẹ (8,41 so với 8,22 tỷ ở HCM) vì bài cũ dùng mẫu khác (gồm cả tin không có ngày cào).

- `test/dbt-unit-tests` (local, chưa push/PR, 2026-10-16; commit hiện tại `8ab5e41`, `562116a`, `08c91b2`, `0c6e482`; tạo trước PR #5–#14 nên cần rebase lên main, dự kiến xung đột ở `run_pipeline.py` vì module `src.scrapers`/`src.geocode` và đường dẫn `src/ops/` đã đổi):
    - 14 dbt unit test (mock input) cho `fct_real_estate`, `fct_real_estate_rent`, 2 mart, 2 view `vw_*_current`: parse giá/diện tích VN, thứ tự token `can-ho-chung-cu-mini`, link tuyệt đối, ngưỡng outlier [5, 1000], dedupe, hash phone, bin ở biên, fallback `districtId=0`, status snapshot.
    - Bước `dbt_unit_tests` chạy đầu `STEPS` (fatal, trước scrape) trong `run_pipeline.py` và DAG; `dbt_test` thêm `--exclude test_type:unit` để không chạy hai lần. DAG đã bị xoá ở main (PR #4), nên khi rebase bỏ phần sửa DAG.
    - `dbt_utils` 1.4.1 pin trực tiếp; generic test mới (`accepted_values` intent/bin, `accepted_range` price/area, price/m2 khớp price/area, `not_null` title) và 5 singular test (mart khớp fct, bin khớp order, snapshot 1 dòng mở/không chồng lấn).
    - Kiểm chứng trên BigQuery 2026-10-16: 73 pass, 5 warn, 0 lỗi; ruff và sqlfluff sạch. Test đột biến bắt được lỗi bin/ngưỡng outlier.

- `feat/scrape-sanity-checks` (local, chưa push/PR, 2026-10-16; commit `77314be`, `18ce759`; xếp chồng lên PR #3 nên cần rebase lên main):
    - Check cấu trúc trước khi ghi bronze (kết quả rỗng, cột khoá/cột chính null vượt ngưỡng) bằng `src/utils/scrape_checks.py`; fail thì scraper thoát non-zero và không ghi gì vào bronze.
    - `re_bronze.fct_project` thêm `scraped_at`/`date_scraped`; chạy lại cùng ngày thay dòng theo `link`. `delete_existing_batch` trả 0 khi bảng chưa có cột ngày, nên lần chạy đầu thêm cột không lỗi. Chưa chạy trên scraper thật, tuần tới là lần đầu thêm cột vào bảng production.

## Chưa làm

- Bronze sale có 13.072 nhóm `(product_id, date_scraped)` lặp từ trước khi có idempotency (13.248 dòng thừa, kiểm 2026-10-16), tập trung ở 2026-07-10 (12.667 dòng thừa). Phần lớn (12.504 nhóm) có nội dung khác nhau: cùng một tin thấy qua nhiều trang quận nên `link`/`location`/`districtId`/`wardId` khác nhau. Silver không bị trùng (103.543 dòng = 103.543 `product_id`), nhưng luật chọn dòng `scraped_at desc nulls last, link asc` khiến tin trùng nhiều quận trong cùng một lần scrape được chọn theo thứ tự chữ cái của `link`, quận có thể không đúng. Chưa sửa; xem Câu hỏi chờ.
- `re_bronze.fct_project`: các dòng cũ (10.805 dòng cho 2.752 dự án, `prid`) không có `scraped_at`, giữ null, không dọn. Bảng chưa được model nào đọc.
- Retry cho lỗi tạm thời của scraper (403, mạng).
- Chưa có view/dashboard sức khoẻ pipeline gộp `re_meta` với `re_elementary`, SLA bằng số, runbook sự cố, retention cho `re_meta`/`logs/`.
- Scrape HCM không ổn định, chưa tìm nguyên nhân (chưa đọc log từng step): `scrape_real_estate_hcm` Partial (exit 2) ngày 2026-10-19 rồi Failed do timeout 3600s ngày 2026-10-26; `scrape_real_estate_rent_hcm` Failed (exit 1) ngày 2026-10-19 nhưng Done ngày 2026-10-26. Ảnh hưởng độ phủ HCM của dữ liệu cho các dashboard.
- Thay Looker bằng site tĩnh (xem mục "Dashboard site tĩnh" ở Đã làm):
    - Merge PR #16 (code dbt của các bảng `*_period` đã có trên prod).
    - Chuyển SQL tổng hợp trong 2 repo phụ (`scripts/extract_data.py`, `scripts/export_data.py`) thành dbt `mart_site_*` ở repo này để test được; hiện SQL nằm trong script.
    - Service account riêng chỉ có quyền đọc cho việc trích xuất; hiện cả hai repo phụ dùng chung key của pipeline (liên quan mục Governance bên dưới).
    - Chưa có step extract/build/deploy trong `STEPS` hay lịch tuần: số trên site đang cập nhật tay (chạy script, commit CSV, push).
    - Dbt exposure cho 2 site vào `dbt/models/marts/_exposures.yml` (hiện chỉ có Looker).
    - Phần Looker có mà 2 site chưa có: trang theo dự án, lọc khoảng giá, click-để-lọc.
    - Cào nhà đất kỳ 2026-10 (site Evidence chỉ có nhà đất kỳ 07).
    - CLAUDE.md của repo này chưa nhắc 2 repo phụ.
- CI của `main` đỏ từ 2026-10-18: `ruff format --check` fail ở `src/ops/launchd_ctl.py` (`38cb952` push thẳng main). Hết khi merge PR #16 hoặc PR `chore/wrk-move-empty-districts` (cả hai đều format file này). Job GitHub Pages ("pages build and deployment") trên main cũng fail, chưa xem nguyên nhân.
- `snp_real_estate*` không bao giờ ghi nhận tin bị gỡ: 0 dòng `dbt_is_deleted = 'True'` qua 5 lần chạy 23/09–26/10 (kiểm 2026-10-26). Snapshot đọc `fct_real_estate*`, mà fct là incremental merge nên không bao giờ xoá tin; `hard_deletes='new_record'` vì thế không kích hoạt, `vw_real_estate*_current` luôn trả `active`. Hướng đã bàn: bỏ `snp_*`, dựng lịch sử SCD2 từ bronze (append-only, có từ tháng 7, `valid_from` = ngày cào), làm sau khi PR #16 merge vì dùng lại macro làm sạch (xem Câu hỏi chờ).
- Service `pipeline` trong `docker-compose.yml` còn đó nhưng không scrape được trong container (cần Chrome headed).
- Governance còn trống: PII register (`agent_name`, `agent_phone_hash`), ghi chú ToS/phạm vi dùng dữ liệu scrape, ADR (`docs/decisions/`), metadata dbt (`meta:` owner/pii/sla, description còn thưa), tách service account theo vai trò, secret scanning (gitleaks/pre-commit).
- Cảnh báo dbt test đang có (kiểm 2026-10-16): outlier giá/m2 (397 dòng), FK `projectId` thiếu (sale 43.057, rent 347 dòng), `area_num` rác vượt 1.000.000 m2 (1 dòng mỗi bảng, vd 931 triệu m2 ở sale, 76 triệu m2 ở rent; chưa lọc ở silver).
- `fct_real_estate` có 24.172 dòng `date_scraped` null (kiểm 2026-10-16); watermark incremental `date_scraped > max(...)` không quét lại các dòng này. Chưa rõ là dữ liệu legacy hay lỗi scraper, nên chưa thêm test `not_null`.
- Testing còn lại: pytest cho parser scraper (`soup_to_df`, `extract_page_tracking_data`... cần sửa tối thiểu vì import có side effect), CI chưa chạy unit test dbt (cần credential BigQuery, hiện CI chỉ `dbt parse`), chưa bật `--store-failures`, chưa cập nhật CLAUDE.md/`docs/technical-guides.md` (còn thiếu step `dbt_unit_tests`).
- Các bản nháp blog trong `content/blog_drafts/` còn nhắc đường dẫn cũ (`src/_web2br`, `docs/blog_drafts`); để nguyên vì là nội dung lịch sử.

## Quyết định đã chốt

- Scrape không chạy trên cloud/CI vì batdongsan.com.vn chặn IP datacenter; CI chỉ lint/build/compile/parse.
- 2026-10-16: Cloudflare Managed Challenge (đại trà, không nhắm riêng scraper) buộc bước warm-up lấy `cf_clearance` chạy patchright **headed**, cửa sổ minimize qua CDP (headless vẫn bị phát hiện); fetch hàng loạt vẫn dùng `curl_cffi` với cookie cache (TTL 1200s, browser mở lại mỗi lần cookie hết hạn). Lý do kỹ thuật đầy đủ ở CLAUDE.md mục "Ràng buộc scrape".
- launchd thay Airflow làm live scheduler (Airflow cần ~1–1.5GB RAM 24/7 cho 1 job/tuần).
- 2026-10-16: xoá hẳn Airflow khỏi repo (PR #4). Task scrape của DAG chạy trong container nên không qua được Cloudflare (warm-up cần Chrome headed), chỉ nửa dbt chạy được; DAG không ghi `re_meta` và phải đồng bộ tay với `STEPS`. Bản cuối còn Airflow giữ ở git tag `airflow-final` (`bde5640`), dùng làm bằng chứng khi cần.
- Lineage location/project và metadata scrape (`metadata.py`) là bước thủ công, ngoài lịch tuần.
- Không thêm layer `int_`; `re_bronze` không phải dbt model nhưng dùng cùng prefix `fct_`/`dim_`.
- Malloy và báo cáo HTML tĩnh ngừng dùng (trỏ Supabase cũ); 2026-10-18 xoá hẳn khỏi repo (PR #10, còn trong git history). `docs/reports/*.html` giữ làm artifact đông cứng cho trang Pages.
- 2026-10-18: package trong `src/` đặt tên theo vai trò, không prefix gạch dưới (`scrapers`, `geocode`, `orchestrator`, `utils`, `ops`). Nội dung cá nhân (bản nháp blog, interview-prep) nằm ở `content/`, không để trong `docs/` vì `docs/` là nguồn GitHub Pages. Gộp `scripts/` vào `src/ops/` (PR #14).
- 2026-10-18: Label launchd đặt dạng `com.dataspi.<repo>-<tần suất>`, quy ước ghi ở `~/.claude/CLAUDE.md` (áp dụng mọi repo).
- 2026-10-18: Stage 5 dọn code cũ: làm (PR #10), không để nguyên.
- 2026-10-16: không dùng volume gate (so số dòng với tuần trước). Số dòng bronze phụ thuộc phạm vi crawl và thị trường (49.435 dòng sale ngày 2026-07-13, 480 dòng ngày 2026-10-16), không có baseline ổn định. Thay bằng check cấu trúc (`scrape_checks.py`), ngưỡng từ lịch sử: 0% null ở mọi lần load trước, khoá 0%, cột chính 5%.
- 2026-10-16: cột `phone` ở bronze không bao giờ chứa số đầy đủ (site che sẵn trong HTML, dạng `0906 435 *** · Hiện số`; ~98% rỗng, phần còn lại bị che, kiểm trên BigQuery). Không coi bronze là kho PII thô; `agent_phone_hash` ở silver chỉ là tín hiệu yếu "cùng một môi giới".
- 2026-10-16: idempotency của bronze xoá theo `(date_scraped, product_id)`, không xoá theo ngày, vì HCM và HN ghi cùng bảng cùng ngày. `fct_project` khoá theo `link` (xem dưới), chưa merge.
- 2026-10-16: `fct_project` thêm `scraped_at`/`date_scraped` (chốt). Cột `id` không phải khoá dự án: nó là tag vị trí trang (`ipos=..,pgno=..,prid=..`) đổi giữa các lần chạy, nên không upsert theo `id`; có 2.752 `prid` (dự án thật) trên 8.408 `id`. Các dòng lặp là snapshot của các lần chạy khác nhau (một lần chạy cho khoảng một dòng mỗi dự án, suy ra từ 2.697 dòng của lần 2026-10-16), không hẳn trùng trong một lần.
- 2026-10-16: bronze là lớp landing append-only, trùng ở đó là bình thường; việc dedupe nằm ở bước bronze → silver. Hướng đề xuất (chưa chốt): không xoá bản trùng cũ ở bronze, chỉ chỉnh luật chọn dòng ở silver.
- 2026-10-16: test dbt và CI/CD do một session riêng phụ trách, không làm trong nhánh observability (session đó là `test/dbt-unit-tests`).
- 2026-10-16: unit test dbt chạy ở local trong `run_pipeline.py`, trước bước scrape; CI không giữ service-account secret nên chỉ chạy `dbt parse`. Target `dev` trỏ thẳng dataset production, nên không dùng `dbt run` để thử đột biến.
- 2026-10-19: báo cáo công khai chuyển sang **site tĩnh dựng bằng code**, thay dần Looker Studio (không dùng Streamlit hay server chạy liên tục). Lý do: dữ liệu cập nhật hàng tuần, người xem là độc giả blog, muốn dashboard-as-code thay vì kéo thả, host miễn phí. Chấp nhận: người xem chỉ lọc trong dữ liệu đã build sẵn; site public nên chỉ đưa bảng đã tổng hợp, không bao giờ dữ liệu từng tin.
- 2026-10-19: host GitHub Pages; repo phụ public, build trong GitHub Actions từ CSV đã commit. Key GCP không vào repo phụ, CI hay GitHub Secrets.
- 2026-10-19: Evidence dùng bản **legacy** 40.x, không dùng Evidence Core/Studio. Core không có lệnh build tĩnh (chỉ `evidence serve` + Docker, Basic Auth) nên không lên Pages được. Chấp nhận legacy đã đóng băng (template chuyển sang Core 2026-08-20, bản npm cuối 40.1.8). Đây là chọn giữa Core và legacy, chưa phải chọn Evidence thay cho các framework khác (xem Câu hỏi chờ).
- 2026-10-19: mỗi framework một repo `scrape-bds-rp-<framework>`, cùng đặc tả đầu ra để so sánh; đặt cùng cấp với repo này trong `~/wrk/`.
- 2026-10-19: so sánh giữa các kỳ phải cùng điều kiện, nên dựng bảng theo kỳ từ bronze (PR #16) thay vì lọc `date_scraped` trên `mart_real_estate`.
- 2026-10-19: gom mọi repo vào `~/wrk`; cài lại plist sau khi job 00:25 của ngày đó đã chạy xong.
- Looker Studio chưa tắt: còn trang theo dự án và lọc khoảng giá mà 2 site chưa có.

## Câu hỏi chờ

- Luật chọn dòng ở silver khi một tin trùng nhiều quận trong cùng một lần scrape: đổi sang ưu tiên dòng có `crawled_district_id = districtId` (tin nằm đúng trang quận của nó) thay cho `link asc`? Và có xoá bản trùng cũ ở bronze sale không (đề xuất: không)?
- Bản nào thay Looker: Evidence legacy, Astro, hay cả hai, và có dựng thêm Observable Framework để so sánh không? Chưa có quyết định chọn giữa các bản. Astro nhẹ hơn nhiều (khoảng 168 KB, không JS, so với khoảng 179 MB) nhưng mới có chung cư mua, một snapshot; Evidence có site theo kỳ và trang thuê nhưng nặng.
- Thống nhất định nghĩa số giữa các site và bài Substack: trung bình hay trung vị; kỳ theo `dim_report_period` hay cửa sổ 14 ngày tính từ đợt cào gần nhất.
- Deploy site từ launchd thế nào: tự commit+push CSV, hay build local rồi đẩy `build/`/`dist/`; xác thực git dưới launchd ra sao. Step này phải non-fatal.
- Lịch sử SCD2 từ bronze (thay `snp_*`): thế nào là "một đợt cào đầy đủ" để đóng tin? Đề xuất: ngày cào cách nhau ≤ 3 ngày là một đợt; theo thành phố × mua/thuê, đợt chỉ được đóng tin khi số tin ≥ 70% đợt trước (bronze có các ngày lẻ như 23/09 1.000 dòng, 28/09 260, 25/10 376, nếu coi là đợt đủ sẽ đóng sai khoảng 100 nghìn tin). Chưa chốt; tạm giữ hướng hiện tại.
- Vì sao chung cư HN kỳ 2026-10 có nhiều hơn kỳ 07 tới **+64%** số tin (HCM −3%): độ phủ scraper, tin chưa xác thực, hay thực tế? Chưa rõ thì các site không kết luận xu hướng giá HN.
