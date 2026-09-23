# AE - TPF Interview — Script thuyết trình (dự án scrape-batdongsan-data)

Script Show → Why → What-if cho 5 core area, dùng dự án này làm bằng chứng sống. Thời lượng
theo đề bài: 5 phút overview + 75 phút (15 phút/area, tối đa 3 sub-topic/area, ~5 phút/sub-topic)
+ 10 phút Q&A.

## 0. Overview (~5 phút)

- Dự án cá nhân, 1 mình maintain: scrape bất động sản từ batdongsan.com.vn → BigQuery
  (`re_bronze` → `re_silver` → `re_gold` qua dbt) → Looker Studio.
- Tech stack đúng yêu cầu: **dbt Core** (transform) + **BigQuery** (cloud DWH) + **Looker
  Studio** (BI, nối trực tiếp `re_gold`).
- Thứ tự trình bày: Data Modeling → Data Transformation → Data Governance → Data Insight →
  DataOps (báo trước cho interviewer theo đúng format đề bài cho phép).
- Ràng buộc thiết kế xuyên suốt dự án, nên nhắc ngay từ đầu: batdongsan.com.vn chặn IP
  cloud/CI runner → scrape bắt buộc chạy từ IP dân dụng → orchestration mặc định là
  **launchd bare-metal** trên máy cá nhân (`scripts/run_weekly_pipeline.sh` +
  `.plist`), và vì sao GitHub Actions không chạy scrape thật (chỉ lint/dbt compile/docker
  build). Airflow self-hosted (docker-compose, từ Stage 2) vẫn còn trong repo như path tuỳ
  chọn cho ai muốn UI/retry/backfill, nhưng không phải default — chi tiết ở mục 5.

## 1. Data Modeling & Architecture (~15 phút)

Chi tiết đầy đủ + mermaid ERD: [data-modeling.md](data-modeling.md). Tóm tắt để nói:

- **Show**: silver = star schema (`stg_real_estate` fact, `stg_projects`/`stg_locations_v1(v2)`
  dimension). Gold = OBT (`mart_real_estate`, `mart_real_estate_rent`) — pre-join sẵn.
- **Why**: OBT ở gold không phải re-model domain, chỉ physicalize lại star schema ở silver
  cho đúng constraint của Looker Studio (free tier join kém).
- **What-if**: volume tăng / nhiều BI tool khác / thêm fact mới → quay lại re-project silver
  thành star schema thật ở gold, không patch tiếp OBT.

## 2. Data Transformation (~15 phút)

- **Show**:
  - Dedup thật bằng `row_number() over (partition by product_id order by scraped_at desc)`
    trong `stg_real_estate.sql`/`stg_real_estate_rent.sql` — thay cho script Python cũ
    (`src/_br2sil/`) chỉ log trùng lặp, không thực sự dedup.
  - Business logic đáng nói: parse số Việt Nam (`.` = phân nghìn, `,` = phân cách thập
    phân), match `real_estate_type` từ slug URL với thứ tự ưu tiên tránh substring shadowing
    (comment rõ trong code), seed `real_estate_type_mapping` để chuẩn hoá nhãn.
  - 5 custom singular test trong `dbt/tests/` (giá/diện tích âm, outlier giá/m2, type lạ
    chưa map...), có phân biệt `severity: error` vs `warn`.
- **Why**: `+materialized: table` cho cả staging + marts (`dbt_project.yml`) — full-refresh mỗi
  lần chạy, không incremental. Chọn vậy vì data nhỏ, pipeline chạy weekly, và full-refresh
  đảm bảo mọi thay đổi ở dimension (silver) tự động propagate đúng vào gold mà không cần logic
  merge riêng.
- **Show (kỹ thuật dbt nâng cao — mới)**: `dbt/snapshots/snp_real_estate.sql` +
  `snp_real_estate_rent.sql` — SCD2 history thật, xây trên `stg_real_estate` (đã dedup) chứ
  không phải bronze thô. `strategy: check` với `check_cols` liệt kê tường minh (loại cột
  near-static như `districtId` và cột noisy như `title`, không dùng `'all'`). `hard_deletes=
  'new_record'`: khi 1 `product_id` biến mất khỏi nguồn (tin bị gỡ/bán), snapshot đóng dòng cũ
  + insert 1 dòng mới `dbt_is_deleted='True'` làm "trạng thái hiện tại" — đọc qua view
  `vw_real_estate_current`. Đây trực tiếp trả lời được What-if "cần historical analysis" đặt ra
  ở mục Data Modeling — không còn là giả thuyết, đã build thật.
- **Chính xác cần biết** — snapshot dùng insert-only logic giống incremental nhưng là
  **resource type riêng** trong dbt DAG (`{% snapshot %}`), **không phải**
  `materialized='incremental'` trên 1 model thường — 2 khái niệm khác nhau, đừng nhận lầm
  snapshot là "đã có incremental rồi" nếu bị hỏi.
- **Show (đã đóng gap incremental)**: `stg_real_estate.sql`/`stg_real_estate_rent.sql` giờ
  `materialized='incremental'`, `unique_key='product_id'`. Watermark filter đặt trên
  `source('bronze', ...)`: `{% if is_incremental() %} where date_scraped > (select
  max(date_scraped) from {{ this }}) {% endif %}` — dùng `date_scraped` chứ không phải
  `scraped_at`, vì `scraped_at` bị comment out khỏi select cuối (dòng cuối file) nên không đọc
  lại được từ `{{ this }}`; `date_scraped` là cột duy nhất còn giữ đủ tín hiệu thời gian ở
  output. Dedup `row_number()` vẫn chạy như cũ, chỉ scope lại theo từng batch incremental
  (an toàn cho rerun ghi trùng bronze trong cùng batch). Verify bằng `dbt compile` (không cần
  chạy thật): `is_incremental()` trả `True` ngay vì bảng đã tồn tại từ lần full-refresh trước
  — không cần `--full-refresh` khi chuyển, vì bảng cũ đã có đủ lịch sử deduped, chỉ merge thêm
  batch mới vào từ watermark hiện tại.
- **What-if (câu hỏi tự nhiên nhất): "đổi materialization ở staging có làm vỡ mart/snapshot
  không?"** — Không, cả `mart_real_estate(_rent)` và `snp_real_estate(_rent)` chỉ làm
  `select * from {{ ref('stg_real_estate') }}`; `ref()` luôn trả về **state đầy đủ, mới nhất**
  của bảng, bất kể bảng được build bằng incremental merge hay full-refresh table — không cần
  sửa 1 dòng code nào ở downstream. Đây là điểm đáng nói: dbt `ref()` che giấu physical
  materialization khỏi consumer, nên đổi materialization ở 1 layer là thay đổi cục bộ, an toàn
  theo thiết kế. `stg_projects`/`stg_locations_v1/v2` vẫn để `table` — dữ liệu tham chiếu
  near-static, incremental không mang lại lợi ích.

## 3. Data Governance — Quality & Security (~15 phút)

- **Show (data quality)**: 2 lớp test trong `dbt/`:
  - Generic tests (`not_null`, `unique`, `relationships` với `severity: warn` cho FK
    `projectId` — vì ~5% listing thiếu project, không muốn fail cả build vì 1 FK optional).
  - Contract enforced (`config.contract.enforced: true`) trên cả 2 model gold — dbt sẽ fail
    build nếu column/type lệch khỏi khai báo trong `_marts.yml`, khoá schema ở đúng biên giữa
    silver và gold.
  - 5 custom singular test (mục 2) — business rule không generic test nào cover được (giá âm,
    outlier giá/m2, type chưa biết).
- **Show (sensitive data)**: bronze scrape có PII thật — `agent_name`, `phone` của người đăng
  tin (`src/_web2br/j_real_estate.py:101-123`). Ở `stg_real_estate.sql` (silver), 2 cột này được
  select vào CTE trung gian rồi **comment out khỏi select cuối** (dòng 170-171) — PII bị cắt
  ngay biên bronze→silver, không bao giờ chạm tới gold/BI. Đây là data minimization, không phải
  mask/hash — nói rõ sự khác biệt nếu bị hỏi ("tại sao không hash thay vì xoá hẳn": vì listing
  agent contact không phục vụ bất kỳ metric phân tích nào ở gold, giữ lại chỉ tăng surface lộ
  dữ liệu mà không tăng giá trị).
  - Secrets: `gcp_service_account.json` + `dbt/profiles.yml` đều gitignored; CI dùng
    `GCP_CREDENTIALS_JSON` (GitHub Actions secret, base64) thay vì mount key file
    (`.github/workflows/dbt-ci.yml`); `GITHUB_TOKEN` trong `docker-build-push` job chỉ xin
    đúng 2 quyền cần (`contents: read`, `packages: write`) — least privilege.
- **What-if (gap thật, chuẩn bị sẵn câu trả lời)**: hiện **không có environment isolation** —
  `dbt/macros/get_custom_schema_name.sql` override để schema luôn là đúng tên custom
  (`re_silver`/`re_gold`) bất kể `target`, nghĩa là target `dev` và target thật đang ghi vào
  **cùng** dataset. Nếu được hỏi "vậy dev/staging tách sao": trả lời thật — chưa tách, vì 1
  mình dev + data không nhạy cảm ở mức cần isolation; hướng mở rộng tự nhiên là thêm
  `{{ target.name }}` vào tên schema khi `target != prod`, hoặc dùng project GCP riêng cho dev.

## 4. Data Insight (~15 phút)

- **Show**: [Looker Studio dashboard](https://lookerstudio.google.com/reporting/9e21618f-97dc-4480-b101-cbda26b9b2a5)
  nối **trực tiếp** BigQuery `re_gold.mart_real_estate` bằng BigQuery connector — không qua
  semantic layer trung gian. Lineage khai báo tường minh bằng dbt exposure
  (`dbt/models/marts/_exposures.yml`, `depends_on: ref('mart_real_estate')`) — hiện luôn trong
  `dbt docs generate`/DAG, nối BI vào đúng graph của dbt thay vì là 1 kết nối "vô hình" ngoài
  version control.
- **Why (nối lại với Data Modeling)**: chính vì Looker Studio free tier join kém nên gold được
  thiết kế OBT — `district_name`, `city_name`, `bin_price`/`bin_price_order` đã được resolve
  và bin sẵn trong `mart_real_estate.sql`, nghĩa là filter/group theo quận hoặc theo khoảng giá
  ngay trên Looker Studio **không cần thêm 1 phép join hay CASE WHEN nào ở BI layer** — toàn bộ
  logic đã test trong dbt.
- **Show (SQL logic + business impact)**: metric trung tâm là giá/m2 theo quận/dự án.
  `is_price_outlier` (`stg_real_estate.sql`) loại các listing có `price_1m2 < 5` hoặc `> 1000`
  triệu/m2 — bắt lỗi nhập liệu ở nguồn (VD product_id 45698293, lệch đơn vị triệu/tỷ), gold
  filter hẳn các row này ra (`where not is_price_outlier`) để dashboard không bị outlier kéo
  lệch trung bình/phân phối giá — business impact: người xem dashboard (kể cả bản thân dùng
  để viết blog Substack) không bị đánh giá sai thị trường vì 1 vài lỗi nhập liệu hiếm.
- **What-if**: thêm 1 metric mới (VD giá thuê/m2 theo quận) — chỉ cần thêm 1 CASE WHEN bin
  trong `mart_real_estate_rent.sql` (đã có `bin_price_per_month`), không cần đổi gì ở BI vì
  Looker Studio đọc trực tiếp cột mới ngay sau `dbt run`.

## 5. DataOps (~15 phút)

- **Show (git branching)**: 1 branch/PR riêng cho mỗi stage — `chore/init-claude-md`,
  `feat/stage2-docker`, `feat/stage2-airflow`, `feat/stage2-cicd`, `feat/stage2-docs` (xem
  `git log --oneline --graph --all`). Có cả merge commit thật (`af4b83a`) mang fix từ
  `stage2-docker` sang nhánh `stage2-airflow` trước khi cả 2 lên `main` — không phải fake
  history.
- **Show (CI/CD)**: `.github/workflows/`:
  - `ci.yml` — lint (`ruff check .`) mọi PR; `docker-build-push` build mọi PR (validate
    Dockerfile) nhưng **chỉ push GHCR khi merge vào `main`** (`if: github.event_name == 'push'
    && github.ref == 'refs/heads/main'`), tag cả `latest` và `${{ github.sha }}` — có thể
    rollback về đúng commit.
  - `dbt-ci.yml` — path-filtered (`paths: dbt/**`) để PR không đụng dbt không tốn 1 lượt
    BigQuery round-trip; chạy `dbt compile --target ci` với service-account JSON từ secret,
    không phải file mount.
- **Why**: CI không chạy scrape/pipeline thật vì GitHub-hosted runner bị chặn IP — tách rõ
  "CI lo fast feedback (lint/compile/build)" khỏi "runtime thật chạy trên máy cá nhân" — đúng
  ràng buộc IP nhắc ở phần Overview, không phải thiếu sót.
- **Cập nhật quan trọng (Giai đoạn 3 — đảo ngược 1 phần Stage 2)**: orchestration mặc định
  không còn là Airflow self-hosted nữa mà là **launchd bare-metal**
  (`scripts/run_weekly_pipeline.sh` + `scripts/com.dataspi.batdongsan-weekly.plist`) — không
  Docker, không process nào chạy 24/7. Lý do đảo ngược: Airflow cần `airflow-scheduler` +
  Postgres metadata chạy liên tục chỉ để bắn đúng 1 job/tuần — chi phí vận hành không tương
  xứng với giá trị cho 1 máy cố định chạy 1 job định kỳ. Airflow (`dags/`, docker-compose)
  **vẫn còn trong repo** như path tuỳ chọn cho ai muốn UI/retry/backfill — không phải xoá bỏ,
  chỉ không còn là default. Nếu bị hỏi "vậy Stage 2 Docker/Airflow làm gì": vẫn là evidence tốt
  cho containerize + CI/CD build, chỉ không còn là đường vận hành chính.
- **Release process**: image `:latest` + `:sha` vẫn lên GHCR (`ghcr.io/<repo>`) sau khi merge
  `main`, phục vụ path Docker/Airflow tuỳ chọn. Với vận hành mặc định (launchd), không có khái
  niệm "deploy image" — chỉ `git pull` code mới trên máy, launchd tự chạy theo lịch
  (`StartCalendarInterval`, bắn bù nếu máy đang ngủ đúng giờ).
- **What-if**: cần rollback nhanh cho path Docker/Airflow — đã có tag theo sha nên chỉ cần đổi
  tag trong `docker-compose.yml` rồi `docker compose up -d`, không cần rebuild. Cần thêm staging
  env trước khi lên main — thêm 1 job `docker-build-push` riêng chạy trên branch `develop`, push
  tag `:staging` thay vì `:latest`.
