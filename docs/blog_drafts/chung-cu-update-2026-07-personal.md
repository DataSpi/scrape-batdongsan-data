Khởi động lại dự án phân tích giá bất động sản sau đúng 10 tháng, [bài phân tích giá chung cư đầu tiên](https://spyno.substack.com/p/i-xem-nha-cung-data-analyst-p1) đăng tháng 9/2025. Mình đã nâng cấp dự án sau một khoảng thời gian dùi mài kinh sử, học thêm nhiều kĩ năng mới. Bộ số được mở rộng từ vài trăm lên hơn 50 ngàn điểm dữ liệu. Chi tiết kĩ thuật của dự án cũng thú vị và cho mình nhiều bài học, nhưng có lẽ mình sẽ viết một bài riêng. 

Giờ thì mời mọi người lại soi giá chung cư cùng mình, vì thú thật là soi một mình thấy hơi choáng. 

# Khai báo kĩ thuật

- Nguồn dữ liệu: [https://batdongsan.com.vn/](https://batdongsan.com.vn/)
    - Hiện tại dự án đã update và crawl cả dữ liệu chưa-xác-thực, do mình thấy nếu chỉ lấy đã-xác-thực thì bộ số ít quá, bỏ sót rất nhiều. 
    - Mình có để slicer xác thực/không xác thực trong dashboard để bạn đọc tự mò số. 
- Kỹ thuật:
    - Tool cào Python: Selenium, BeautifulSoup
    - Github: [https://github.com/DataSpi/scrape-batdongsan-data](https://github.com/DataSpi/scrape-batdongsan-data)
    - Data visualization: [Google Looker Studio](https://lookerstudio.google.com/reporting/9e21618f-97dc-4480-b101-cbda26b9b2a5)
- Note:
	- Bài phân tích vẫn sử dụng địa giới hành chính cũ trước sáp nhập để phân tích dữ liệu. Đơn giản là vì mình quen, đọc địa giới hành chính mới mình chả biết đâu vào với đâu. 

# Nhận xét chung

### Nguồn cung

Nguồn cung tập trung ở phân khúc 3-10 tỷ ở cả HCM & HN (~60% tổng).

![[Pasted image 20260713140759.png]]

### Phân hóa theo vị trí

Các quận trung tâm ghi nhận mức giá/m² cao nhất, giảm dần khi dịch chuyển ra khu vực vùng ven.

Top 10 giá/m2 HCM *(Đơn vị: Triệu VND)*: 

![[Pasted image 20260713140935.png]]

Top 10 giá/m2 HN: 

![[Pasted image 20260713140954.png]]


### Giá nhà & giá/m² tỷ lệ thuận 

Giá bds & giá/m² tương quan thuận: nhà càng đắt thì đơn giá/m² càng cao.

- 80% nhà DƯỚI 2 tỷ giá DƯỚI 40tr/m².
- 95% nhà TRÊN 5 tỷ giá TRÊN 60tr/m².

![[Pasted image 20260713141600.png]]


# Hồ Chí Minh

- Tháng 9/2025: *"Số lượng căn hộ chung cư được rao bán nhiều nhất thuộc về các quận: Q9, Q2, Q7, Bình Thạnh, Tân Phú, Bình Tân, Bình Chánh. Tổng số 404/485 bài đăng, chiếm hơn 80%."*
	- Tháng 7/2026: Vẫn 7 quận trên, hiện chiếm **67.4%** (18.933/28.088). Không áp đảo tuyệt đối như trước, cung đã loang ra các quận vùng ven khác như Nhà Bè, Thủ Đức (mỗi quận 3-4%).
- Các quận trung tâm vẫn ghi nhận mức giá/m² cao nhất & tăng nhanh. 
	- Tháng 9/2025: Quận 1, **174 triệu/m²**. 
	- Tháng 7/2026: **233.5 triệu/m²** — tăng gần 34%



# Hà Nội

> Giá chung cư HN cao hơn HCM ở cả mức giá tổng và giá/m²

**Lần đầu có data Hà Nội** nên mình tò mò so thử — HN đắt hơn HCM cả giá lẫn giá/m² (9.15 tỷ / 94.1tr so với 8.22 tỷ / 86.8tr). Nhưng đào sâu hơn thì thấy không phải "cả HN đắt hơn" mà đúng hơn là HN có một cụm quận lõi (Hoàn Kiếm, Ba Đình, Tây Hồ...) đắt vượt trội kéo trung bình lên — Hoàn Kiếm đang là quận đắt nhất cả nước, 338tr/m², gần gấp rưỡi Quận 1 HCM. Còn lại phần đông tin ở HN thì giá cũng bình thường thôi, không đến mức khác biệt hẳn với HCM.



# 1 ngủ

Tháng 9/2025: 
- HCM: khả năng tìm được căn 1PN dưới 2 tỷ là 10/72 ≈ 14% (tổng dữ liệu 1PN lúc đó chỉ có 72 tin).

Tháng 7/2026: tỷ lệ 1 ngủ < 2 tỷ:  
- HCM: 198/3.358 ≈ **5.9%**. (đã lọc giá null)![[Pasted image 20260713152336.png]]
- HN: 39/1122 ≈ **3.5%**.![[Pasted image 20260713152302.png]]

# 2 ngủ

Tháng 9/2025:  dưới 2 tỷ là 5.3%, dưới 3 tỷ là 30%.

Tháng 7/2026:
- HCM: dưới 2 tỷ ≈ **3.0%** (435/14.622), dưới 3 tỷ ≈ **16.8%** (2.460/14.622) tức mất 13.2 điểm % trong 10 tháng.
	- Đây là phân khúc mình thấy đáng nói nhất — 2PN là phân khúc phổ thông nhất, đông người mua nhất, và cũng là phân khúc mất thị phần nhiều nhất. ![[Pasted image 20260713151923.png]]
- HN: dưới 2 tỷ ≈ **0.2%** (16/7475), dưới 3 tỷ ≈ **3%** (225/7475). OMG!![[Pasted image 20260713151959.png]]
# 3 ngủ

Tháng 9/2025: dưới 3 tỷ gần như không có — mình gọi vui là "đã tuyệt chủng".

Tháng 7/2026: tỷ lệ 3 ngủ < 3 tỷ:
- HCM: 106/6.567 ≈ **1.6%**. Nhích lên một chút so với gần-như-0, nhưng nói thật là vẫn tuyệt chủng, chỉ là giờ có bằng chứng số cụ thể hơn cho câu đùa đó thôi =))) *(dán ảnh dashboard 3PN HCM vào đây)*
- HN: 13/5.847 ≈ **0.2%**. Còn tuyệt chủng hơn cả HCM. *(dán ảnh dashboard 3PN HN vào đây)*

# Kết


Mình sẽ sớm lên bài tiếp theo về thị trường nhà đất. Lần này sớm thật, không ngâm thêm 10 tháng nữa đâu. Yên tâm =)), số tôi có đây hết rồi, anh em tin tôi. 

