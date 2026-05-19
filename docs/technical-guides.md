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
- Mô hình Malloy trong `models/real_estate.malloy`.
- dbt mart model trong `dbt/models/marts/`.
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

Nội dung nên có:
- Lịch chạy jobs.
- Workflow CI/CD ingestion.
- Cách debug khi task bị lỗi.

Gợi ý file liên quan:
- `.github/workflows/d_ingest_main.yml`
- `dags/real_estate_dag.py`

## Điều hướng

- Về [Trung tâm tài liệu](README.md)
- Sang [Quickstart](quickstart.md)
- Về [Trang chủ dự án](../index.md)
