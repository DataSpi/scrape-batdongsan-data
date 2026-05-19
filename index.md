# Scrape Batdongsan Data

Dự án mã nguồn mở cá nhân để thu thập, chuẩn hoá và phân tích dữ liệu bất động sản từ [batdongsan.com.vn](https://batdongsan.com.vn).
- Báo cáo mẫu: [Báo cáo giá bất động sản theo dự án tại HN & TPHCM](reports\output\HCM-HN_prj_rp.html)

## Bắt đầu nhanh

- Quickstart: [docs/quickstart.md](docs/quickstart.md)
- Hướng dẫn kỹ thuật: [docs/technical-guides.md](docs/technical-guides.md)

## Tổng quan

Dự án xây dựng pipeline dữ liệu có thể lặp lại:

1. Thu thập listings, dự án và metadata vị trí.
2. Lưu trữ và xử lý dữ liệu trên Supabase/PostgreSQL.
3. Mô hình hoá phục vụ phân tích với Malloy + dbt.
4. Tạo báo cáo và dashboard phân tích thị trường.

![Quy trình dữ liệu](figs/project-flow2.png)
![Dashboard minh hoạ](figs/dashboard-preview.png)

```mermaid
subgraph B[Lớp Web Scraping]
		B1[j_real_estate.py<br/>Crawler listings + merge tracking JSON]
		B2[j_projects.py<br/>Crawler dự án]
		B3[j_metadata.py<br/>API metadata thành phố, phường, đường, dự án]
end

B --> C[(Supabase PostgreSQL<br/>re_bronze)]

C --> D[br2sil/j_real_estate.py<br/>Làm sạch + chuẩn hoá]
D --> E[(Supabase PostgreSQL<br/>re_silver.real_estate)]

E --> F[Malloy Semantic Model<br/>models/real_estate.malloy]
C --> F

C --> G[dbt Mart Model<br/>dbt/models/marts/fct_real_estate.sql]
E --> G

F --> H[Truy vấn phân tích<br/>models/materialize.malloysql]
G --> H

H --> I[Looker Studio Dashboard]

J[APScheduler local jobs] -. lên lịch .-> B
K[Airflow DAG scaffold] -. điều phối .-> B
K -. điều phối .-> D
```

## Lý do nên dùng dự án này

- Biến dữ liệu marketplace phi cấu trúc thành bảng có thể truy vấn.
- Giảm công quét thủ công nhờ tập trung listings và thông tin dự án.
- Xử lý các vấn đề chất lượng dữ liệu để sẵn sàng phân tích.
- Cung cấp semantic layer để trả lời nhanh các câu hỏi về giá và cung-cầu.

## Tính năng chính

- Scraper bất đồng bộ, chia batch, giả lập trình duyệt để tăng tỉ lệ thành công.
- Merge listing cards với `window.pageTrackingData` theo `product_id`.
- Ingest metadata cho thành phố, phường, đường, dự án.
- Pipeline Bronze -> Silver:
	- Parse giá và diện tích về số.
	- Chuẩn hoá loại hình bất động sản.
	- Tính lại giá theo m2.
	- Kiểm tra trùng lặp và bổ sung ngày scrape.
- Semantic model bằng Malloy và mart model bằng dbt.
- Hỗ trợ orchestration bằng APScheduler và Airflow scaffold.

## Lệnh chạy nhanh

```bash
pip install -r requirements.txt
python -m src.web2br.j_real_estate
python -m src.web2br.j_projects
python -m src.web2br.j_metadata
python -m src.br2sil.j_real_estate
python src/reports/generate_report.py
```

## Điều hướng

- Nếu bạn mới vào repo: bắt đầu tại [docs/quickstart.md](docs/quickstart.md).
- Muốn đào sâu kỹ thuật: xem [docs/technical-guides.md](docs/technical-guides.md).
- Xem kết quả phân tích nhanh: mở [reports/](reports/) và [reports/output/malloy_result.html](reports/output/malloy_result.html).

## Lưu ý

- Airflow DAG hiện có một số đường dẫn script legacy cần đổi lại theo cấu trúc repo mới.
- Khuyến nghị tách secrets/credentials ra biến môi trường thay vì lưu cùng code.
