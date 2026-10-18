---
last_verified: 2026-10-18
verified_commit: dbacd9c
owner: DataSpi
---

# Trạng thái dự án (snapshot)

Tài liệu DUY NHẤT chứa trạng thái theo ngày. README và CLAUDE.md chỉ giữ quy ước và cấu trúc.

## Phạm vi

Scrape batdongsan.com.vn (sale/rent/projects, HCM + HN) → BigQuery `re_bronze` → dbt → `re_silver` → `re_gold` → Looker Studio. Dự án cá nhân, một người maintain. Chạy tuần bằng launchd trên máy local (scrape bắt buộc IP dân dụng).

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

### Đang chờ merge (chưa vào main)

- PR #13 `chore/runtime-dirs` (mở 2026-10-18, đã gộp main để hết conflict với #14): `edr report --target-path logs/edr_target`, để `edr_target/` không còn sinh ra ở gốc repo. Chưa merge.

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
- Plist launchd chưa reload sau PR #14 (kiểm 2026-10-18): file cài ở `~/Library/LaunchAgents` vẫn trỏ `scripts/run_weekly_pipeline.sh`, mà thư mục chính đã chuyển sang `main` mới nhất (không còn `scripts/`). Cho đến khi `launchctl bootout` + copy `src/ops/com.dataspi.batdongsan-weekly.plist` + `bootstrap` lại, job tuần sẽ không chạy được (lần gần nhất bị ảnh hưởng: Thứ 2 2026-10-19 9h).
- Service `pipeline` trong `docker-compose.yml` còn đó nhưng không scrape được trong container (cần Chrome headed).
- Governance còn trống: PII register (`agent_name`, `agent_phone_hash`), ghi chú ToS/phạm vi dùng dữ liệu scrape, ADR (`docs/decisions/`), metadata dbt (`meta:` owner/pii/sla, description còn thưa), tách service account theo vai trò, secret scanning (gitleaks/pre-commit).
- Cảnh báo dbt test đang có (kiểm 2026-10-16): outlier giá/m2 (397 dòng), FK `projectId` thiếu (sale 43.057, rent 347 dòng), `area_num` rác vượt 1.000.000 m2 (1 dòng mỗi bảng, vd 931 triệu m2 ở sale, 76 triệu m2 ở rent; chưa lọc ở silver).
- `fct_real_estate` có 24.172 dòng `date_scraped` null (kiểm 2026-10-16); watermark incremental `date_scraped > max(...)` không quét lại các dòng này. Chưa rõ là dữ liệu legacy hay lỗi scraper, nên chưa thêm test `not_null`.
- Testing còn lại: pytest cho parser scraper (`soup_to_df`, `extract_page_tracking_data`... cần sửa tối thiểu vì import có side effect), CI chưa chạy unit test dbt (cần credential BigQuery, hiện CI chỉ `dbt parse`), chưa bật `--store-failures`, chưa cập nhật CLAUDE.md/`docs/technical-guides.md` (còn thiếu step `dbt_unit_tests`).
- Còn phải quét các comment/doc nhắc code đã xoá: `docs/blog_drafts` → `content/blog_drafts` và `src/_web2br` trong các bản nháp blog cũ không sửa (nội dung lịch sử).

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

## Câu hỏi chờ

- Luật chọn dòng ở silver khi một tin trùng nhiều quận trong cùng một lần scrape: đổi sang ưu tiên dòng có `crawled_district_id = districtId` (tin nằm đúng trang quận của nó) thay cho `link asc`? Và có xoá bản trùng cũ ở bronze sale không (đề xuất: không)?
- Khi nào pull `main` về thư mục chính và reload launchd (xem mục Chưa làm)? Cần chọn một ngày không phải Thứ 2, và merge PR #13 trước hoặc sau đó.
