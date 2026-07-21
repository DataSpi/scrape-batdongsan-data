# Quickstart

Tài liệu này giúp bạn chạy dự án nhanh trên máy cá nhân, qua Docker + Airflow (cách
chạy chính thức từ giai đoạn 2). Có mục [chạy bare-metal](#6-chạy-bare-metal-không-qua-docker)
ở cuối nếu bạn không muốn dùng Docker.

## 1) Yêu cầu trước khi bắt đầu

- Docker Desktop (hoặc Docker Engine + Compose plugin) đã cài và chạy.
- File service account BigQuery: `gcp_service_account.json` ở repo root (liên hệ
  maintainer nếu bạn không có project GCP riêng).
- **batdongsan.com.vn chặn IP của cloud/CI runner** — pipeline này bắt buộc chạy từ
  máy cá nhân (IP dân dụng), không chạy được trên VM cloud thông thường. Container
  Docker chạy trên máy bạn vẫn dùng đúng IP của máy đó nên không vi phạm ràng buộc
  này — xem [technical-guides.md](technical-guides.md) để biết chi tiết.

## 2) Cài đặt

```bash
git clone https://github.com/DataSpi/scrape-batdongsan-data.git
cd scrape-batdongsan-data
cp .env.example .env            # điền GOOGLE_MAPS_API_KEY nếu cần rebuild location lineage
cp dbt/profiles.yml.example dbt/profiles.yml   # sửa `project` + `keyfile` cho đúng máy bạn
# đặt gcp_service_account.json ở repo root
```

## 3) Build & khởi động

```bash
docker compose build
docker compose up airflow-init      # migrate DB metadata Airflow + tạo user admin (chạy 1 lần)
docker compose up -d                # bật scheduler + webserver + metadata DB
```

Mở [http://localhost:8080](http://localhost:8080) (đăng nhập `admin` / `admin`, đổi
sau khi dùng thật). Có 2 DAG:

- `pipeline_weekly` — scrape + dbt run/test, lịch mặc định Thứ 2 9h sáng (thay thế
  crontab cũ). Có thể trigger tay để chạy thử ngay.
- `lineage_rebuild` — chỉ trigger thủ công, dùng khi cần geocode lại district/ward
  hoặc có district/ward mới (xem [technical-guides.md](technical-guides.md) mục 3).

## 4) Tạo báo cáo

```bash
docker compose run --rm pipeline python src/reports/report_builder.py
```

Báo cáo được lưu vào `docs/reports/`.

## 5) Kiểm tra nhanh

- Trigger `pipeline_weekly` trên Airflow UI, xem cả 9 task chuyển xanh theo đúng thứ tự.
- Có dữ liệu mới trong BigQuery `re_bronze`/`re_silver`/`re_gold`.
- Có file HTML báo cáo mới trong `docs/reports/`.
- Xem báo cáo mẫu: [HCM-HN_prj.html](reports/HCM-HN_prj.html)

## 6) Chạy bare-metal (không qua Docker)

Vẫn hoạt động, dùng khi debug nhanh 1 script hoặc không muốn cài Docker — không còn
là cách chạy mặc định của dự án.

```bash
python -m venv venv && source venv/bin/activate   # hoặc conda
pip install -r requirements.txt
python -m src.orchestrator.run_pipeline
```

Copy `dbt/profiles.yml.example` thành `dbt/profiles.yml` trước khi chạy lần đầu —
lưu ý path `keyfile` cho bare-metal khác với path dùng trong container (xem comment
trong file `.example`).

## 7) Xử lý lỗi thường gặp

- **Container không kết nối được BigQuery**: kiểm tra `gcp_service_account.json` có ở
  repo root và được mount đúng trong `docker-compose.yml`.
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
