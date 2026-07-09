# Hướng dẫn kỹ thuật

Trang này tổng hợp các hướng dẫn kỹ thuật chi tiết cho từng phần của dự án. Bạn có thể bổ sung hoặc mở rộng theo nhóm chủ đề dưới đây.

## 1) Lớp thu thập dữ liệu (Scraping Layer)

Nội dung nên có:
- Kiến trúc crawler, chia batch, retry, throttle.
- Mapping các script trong `src/web2br/`.
- Cách cập nhật selector khi website thay đổi.

Gợi ý file liên quan:
- `src/web2br/j_real_estate.py`
- `src/web2br/j_projects.py`
- `src/web2br/j_metadata.py`

## 2) Làm sạch dữ liệu (Bronze -> Silver)

Nội dung nên có:
- Quy tắc làm sạch dữ liệu (giá, diện tích, chuẩn hoá loại hình).
- Kiểm tra trùng lặp và chất lượng dữ liệu.
- Các bảng output và quy ước schema.

Gợi ý file liên quan:
- `src/br2sil/j_real_estate.py`

## 3) Semantic Modeling và Analytics

Nội dung nên có:
- Mô hình Malloy trong `models/malloy_publisher/real_estate.malloy` (hiện vẫn trỏ vào Supabase, chưa migrate theo BigQuery — xem ghi chú trong plan đánh giá kiến trúc).
- dbt staging models trong `dbt/models/staging/` (bronze -> silver, thay `src/_br2sil/*.py`) và mart trong `dbt/models/marts/` (gold).
- Nguyên tắc đặt tên dimensions và joins.

## 4) Báo cáo và trực quan hoá (Reports & Visualization)

Nội dung nên có:
- Script tạo báo cáo HTML.
- Các chỉ số KPI và ý nghĩa.
- Quy trình xuất/chia sẻ kết quả.

Gợi ý file liên quan:
- `src/reports/generate_report.py`
- `reports/output/malloy_result.html`

## 5) Orchestration

Pipeline chạy hoàn toàn trên máy local qua `src/orchestrator/run_pipeline.py`
(scrape -> `dbt seed` -> `dbt run` -> `dbt test`, dừng ngay khi 1 bước lỗi), kích hoạt
bằng crontab — không dùng GitHub Actions/Airflow, vì batdongsan.com.vn chặn IP của các
cloud runner nên bước scrape bắt buộc phải chạy local.

Ví dụ crontab (`crontab -e`):
```
0 9 * * 1 cd /path/to/scrape-batdongsan-data && ./venv/bin/python -m src.orchestrator.run_pipeline >> logs/pipeline_cron.log 2>&1
```

Debug khi task lỗi: xem log tương ứng (stdout/stderr của bước lỗi được in ra trong log
trên), pipeline dừng lại ngay tại bước đó nên không cần đoán bước nào đã chạy.

Gợi ý file liên quan:
- `src/orchestrator/run_pipeline.py`

## Điều hướng

- Về [Trung tâm tài liệu](README.md)
- Sang [Quickstart](quickstart.md)
- Về [Trang chủ dự án](../index.md)
