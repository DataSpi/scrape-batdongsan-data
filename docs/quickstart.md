# Quickstart

Tài liệu này giúp bạn chạy dự án nhanh trên máy cá nhân. Cách chạy mặc định (giai đoạn 3) là
**bare-metal + launchd** — không cần Docker.

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
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.dataspi.batdongsan-weekly.plist

# test ngay không cần đợi tới lịch (Thứ 2, 9h sáng):
launchctl kickstart gui/$(id -u)/com.dataspi.batdongsan-weekly
```

Dùng `bootstrap`, không dùng `launchctl load` (lệnh cũ) -- trên macOS hiện đại (xác nhận trên
15.x Sequoia) `load` báo lỗi mù mờ "Input/output error" không rõ nguyên nhân, còn `bootstrap`
báo lỗi rõ ràng hơn hẳn. Gỡ job: `launchctl bootout gui/$(id -u)/com.dataspi.batdongsan-weekly`.

Khác cron thật: nếu máy đang ngủ đúng giờ trigger, launchd tự chạy bù khi máy thức dậy thay vì
bỏ qua hẳn lần chạy đó. Log mỗi lần chạy nằm ở `logs/pipeline_<timestamp>.log`.

## 5) Kiểm tra nhanh

- Chạy `python -m src.orchestrator.run_pipeline` (hoặc `launchctl kickstart ...`) thấy log chạy hết
  cả 10 bước, exit code 0.
- Có dữ liệu mới trong BigQuery `re_bronze`/`re_silver`/`re_gold`.
- `re_silver.snp_real_estate` có dòng với `dbt_valid_from` = thời điểm vừa chạy.

## 6) Xử lý lỗi thường gặp

- **Không kết nối được BigQuery**: kiểm tra `gcp_service_account.json` có ở repo root và
  `dbt/profiles.yml` trỏ đúng file.
- **launchd job không chạy / không thấy log mới**: xem
  [technical-guides.md mục 10](technical-guides.md#10-troubleshooting).
- **`dbt run`/`dbt test` báo lỗi credentials trong container**: `dbt/profiles.yml` có
  path `keyfile` tuyệt đối — path này khác nhau giữa bare-metal và trong container
  `pipeline` (`/app/gcp_service_account.json`), xem `dbt/profiles.yml.example`.
- **Không có listing mới sau khi scrape**: website nguồn có thể đã đổi cấu trúc, cần
  cập nhật lại selector trong `src/scrapers/`.

## Điều hướng

- Về [Trang chủ dự án (GitHub Pages)](https://dataspi.github.io/scrape-batdongsan-data/)
- Về [Trung tâm tài liệu](README.md)
- Sang [Hướng dẫn kỹ thuật](technical-guides.md)
