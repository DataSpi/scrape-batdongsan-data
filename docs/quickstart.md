# Quickstart

Tài liệu này giúp bạn chạy dự án nhanh trên máy cá nhân. Cách chạy mặc định (giai đoạn 3) là
**bare-metal + launchd** — không cần Docker. Có mục
[chạy qua Docker + Airflow](#6-cách-khác--docker--airflow-self-hosted) ở cuối nếu bạn muốn UI
theo dõi/retry tự động, đánh đổi lấy việc phải giữ `airflow-scheduler` chạy liên tục.

## 1) Yêu cầu trước khi bắt đầu

- Python 3.12 (conda hoặc venv đều được).
- File service account BigQuery: `gcp_service_account.json` ở repo root (liên hệ
  maintainer nếu bạn không có project GCP riêng).
- **batdongsan.com.vn chặn IP của cloud/CI runner** — pipeline này bắt buộc chạy từ
  máy cá nhân (IP dân dụng), không chạy được trên VM cloud thông thường — xem
  [technical-guides.md](technical-guides.md) để biết chi tiết.

## 2) Cài đặt

```bash
git clone https://github.com/DataSpi/scrape-batdongsan-data.git
cd scrape-batdongsan-data
cp .env.example .env            # điền GOOGLE_MAPS_API_KEY nếu cần rebuild location lineage
cp dbt/profiles.yml.example dbt/profiles.yml   # sửa `project` + `keyfile` cho đúng máy bạn
# đặt gcp_service_account.json ở repo root

python -m venv venv && source venv/bin/activate   # hoặc conda create -n scrape_bds python=3.12
pip install -r requirements.txt
```

## 3) Chạy thử thủ công

```bash
python -m src.orchestrator.run_pipeline
```

Chạy tuần tự: scrape sale HCM/HN → scrape rent HCM/HN → scrape projects HCM/HN → scrape
metadata → `dbt run` → `dbt snapshot` (SCD2 history, xem
[technical-guides.md mục 1b](technical-guides.md#1b-lịch-sử-thay-đổi-listing-scd2cdc)) → `dbt
test`. Dừng ngay khi có bước lỗi.

## 4) Cài đặt chạy định kỳ (launchd)

```bash
cp scripts/com.dataspi.batdongsan-weekly.plist ~/Library/LaunchAgents/
# sửa các path /Users/spinokiem/... trong file plist + trong
# scripts/run_weekly_pipeline.sh cho khớp máy bạn (repo path, conda env path)
launchctl load ~/Library/LaunchAgents/com.dataspi.batdongsan-weekly.plist

# test ngay không cần đợi tới lịch (Thứ 2, 9h sáng):
launchctl start com.dataspi.batdongsan-weekly
```

Khác cron thật: nếu máy đang ngủ đúng giờ trigger, launchd tự chạy bù khi máy thức dậy thay vì
bỏ qua hẳn lần chạy đó. Log mỗi lần chạy nằm ở `logs/pipeline_<timestamp>.log`.

## 5) Kiểm tra nhanh

- Chạy `python -m src.orchestrator.run_pipeline` (hoặc `launchctl start ...`) thấy log chạy hết
  cả 10 bước, exit code 0.
- Có dữ liệu mới trong BigQuery `re_bronze`/`re_silver`/`re_gold`.
- `re_silver.snp_real_estate` có dòng với `dbt_valid_from` = thời điểm vừa chạy.

## 6) Cách khác — Docker + Airflow (self-hosted)

Nếu muốn theo dõi qua UI, retry tự động, hoặc backfill — dùng Airflow tự host thay vì launchd.
Đánh đổi: `airflow-scheduler` + Postgres metadata phải chạy liên tục (~1–1.5GB RAM) chỉ để bắn 1
job/tuần, xem [CLAUDE.md § Giai đoạn 3](../CLAUDE.md).

```bash
docker compose build
docker compose up airflow-init      # migrate DB metadata Airflow + tạo user admin (chạy 1 lần)
docker compose up -d                # bật scheduler + webserver + metadata DB
```

Mở [http://localhost:8080](http://localhost:8080) (đăng nhập `admin` / `admin`, đổi
sau khi dùng thật). Có 2 DAG:

- `pipeline_weekly` — scrape + dbt run/snapshot/test, lịch mặc định Thứ 2 9h sáng (đồng bộ với
  launchd ở mục 4). Có thể trigger tay để chạy thử ngay.
- `lineage_rebuild` — chỉ trigger thủ công, dùng khi cần geocode lại district/ward
  hoặc có district/ward mới (xem [technical-guides.md](technical-guides.md) mục 3).

## 7) Tạo báo cáo

```bash
python src/reports/report_builder.py   # hoặc: docker compose run --rm pipeline python src/reports/report_builder.py
```

Báo cáo được lưu vào `docs/reports/`.

## 8) Xử lý lỗi thường gặp

- **Không kết nối được BigQuery**: kiểm tra `gcp_service_account.json` có ở repo root và
  `dbt/profiles.yml` trỏ đúng file.
- **launchd job không chạy / không thấy log mới**: xem
  [technical-guides.md mục 10](technical-guides.md#10-troubleshooting).
- **`dbt run`/`dbt test` báo lỗi credentials trong Airflow**: `dbt/profiles.yml` có
  path `keyfile` tuyệt đối — path này khác nhau giữa bare-metal và trong container
  Airflow (`/opt/airflow/repo/gcp_service_account.json`), xem `dbt/profiles.yml.example`.
- **DAG không xuất hiện trên Airflow UI**: kiểm tra `docker compose logs airflow-scheduler`
  và `airflow dags list-import-errors` (chạy qua `docker compose exec airflow-scheduler ...`).
- **Không có listing mới sau khi scrape**: website nguồn có thể đã đổi cấu trúc, cần
  cập nhật lại selector trong `src/_web2br/`.

## Điều hướng

- Về [Trang chủ dự án (GitHub Pages)](https://dataspi.github.io/scrape-batdongsan-data/)
- Về [Trung tâm tài liệu](README.md)
- Sang [Hướng dẫn kỹ thuật](technical-guides.md)
