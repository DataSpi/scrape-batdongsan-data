# Quickstart

Tài liệu này giúp bạn chạy dự án nhanh trên máy cá nhân.

## 1) Yêu cầu trước khi bắt đầu

- Python 3.10 trở lên (nên dùng môi trường conda riêng).
- Có quyền truy cập database Supabase/PostgreSQL.
- Tạo file `.env` (hoặc thiết lập biến môi trường) với các biến tối thiểu:
  - `DB_HOST`
  - `DB_PORT`
  - `DB_DB_NAME`
  - `DB_USER`
  - `DB_PASSWORD`

## 2) Cài đặt

```bash
pip install -r requirements.txt
```

Nếu dùng conda:

```bash
conda create -n bds_scraper python=3.10 -y
conda activate bds_scraper
pip install -r requirements.txt
```

## 3) Chạy pipeline cơ bản

Chạy toàn bộ pipeline (scrape -> dbt seed/run/test) bằng một lệnh:

```bash
python -m src.orchestrator.run_pipeline
```

Hoặc chạy từng bước riêng lẻ khi cần debug:

### 3.1 Thu thập listings

```bash
python -m src._web2br.j_real_estate
```

### 3.2 Thu thập dự án

```bash
python -m src._web2br.j_projects
```

### 3.3 Lấy metadata

```bash
python -m src._web2br.j_metadata
```

### 3.4 Làm sạch dữ liệu (Bronze -> Silver -> Gold, dbt)

```bash
cd dbt && dbt seed && dbt run && dbt test
```

Copy `dbt/profiles.yml.example` thành `dbt/profiles.yml` (đã gitignore) trước khi chạy lần đầu.

## 4) Tạo báo cáo

```bash
python src/reports/generate_report.py
```

Báo cáo sẽ được lưu trong thư mục `reports/output/`.

## 5) Kiểm tra nhanh

- Có dữ liệu trong schema Bronze/Silver trên database.
- Có file HTML báo cáo mới trong `reports/output/`.
- Xem báo cáo mẫu: [malloy_result.html](../reports/output/malloy_result.html)

## 6) Xử lý lỗi thường gặp

- Lỗi kết nối DB: kiểm tra lại `.env` và quyền truy cập Supabase.
- Lỗi package: chạy lại `pip install -r requirements.txt` trong đúng environment.
- Không có listing: website nguồn có thể đã đổi cấu trúc, cần cập nhật lại selector scraper.

## Điều hướng

- Về [Trang chủ dự án](../index.md)
- Về [Trung tâm tài liệu](README.md)
- Sang [Hướng dẫn kỹ thuật](technical-guides.md)
