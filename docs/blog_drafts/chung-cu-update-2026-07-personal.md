Khởi động lại dự án phân tích giá bất động sản sau đúng 10 tháng, [bài phân tích giá chung cư đầu tiên](https://spyno.substack.com/p/i-xem-nha-cung-data-analyst-p1) đăng tháng 9/2025. Mình đã nâng cấp dự án sau một khoảng thời gian dùi mài kinh sử, học thêm nhiều kĩ năng mới. Bộ số được mở rộng từ vài trăm lên hơn 50 ngàn điểm dữ liệu. Chi tiết kĩ thuật của dự án cũng thú vị và cho mình nhiều bài học, nhưng có lẽ mình sẽ viết một bài riêng. 

Giờ thì mời mọi người lại soi giá chung cư cùng mình, vì thú thật là soi một mình thấy hơi choáng. 

# Khai báo kĩ thuật

- Nguồn dữ liệu: [https://batdongsan.com.vn/](https://batdongsan.com.vn/)
    - Hiện tại dự án đã update và crawl cả dữ liệu chưa-xác-thực, do mình thấy nếu chỉ lấy đã-xác-thực thì bộ số ít quá, bỏ sót rất nhiều. 
- Kỹ thuật:
    - Tool cào Python: Selenium, BeautifulSoup
    - Github: [https://github.com/DataSpi/scrape-batdongsan-data](https://github.com/DataSpi/scrape-batdongsan-data)
    - Data visualization: [Google Looker Studio](https://lookerstudio.google.com/reporting/9e21618f-97dc-4480-b101-cbda26b9b2a5)
- Note:
	- Bài phân tích vẫn sử dụng địa giới hành chính cũ trước sáp nhập để phân tích dữ liệu. Đơn giản là vì mình quen, đọc địa giới hành chính mới mình chả biết đâu vào với đâu. 

# Tổng quan

## Nguồn cung

Nguồn cung tập trung ở phân khúc 3-10 tỷ ở cả HCM & HN (~60% tổng).

![[Pasted image 20260713140759.png]]

## Giá 

**HCM vs HN: chênh giá trung bình nhỏ, nhưng cửa giá mềm chênh rất xa.**
- Giá TB chung cư hai bên chỉ chênh khoảng 11% (HCM 8.22 tỷ / 86.8tr/m², HN 9.15 tỷ / 94.1tr/m²).
- Nhưng tỷ lệ tin dưới 3 tỷ thì chênh gần 4 lần: HCM 15.2%, HN chỉ 4.3%.
- Nhìn riêng giá trung bình sẽ đánh giá thấp khoảng cách thật giữa hai thị trường — HN không chỉ đắt hơn một chút, mà cửa giá mềm gần như đã đóng, trong khi HCM vẫn còn giữ được một phần đáng kể.

## Phân hóa theo vị trí

Các quận trung tâm ghi nhận mức giá/m² cao nhất, giảm dần khi dịch chuyển ra khu vực vùng ven.
### Hồ Chí Minh

- Tháng 9/2025: *"Số lượng căn hộ chung cư được rao bán nhiều nhất thuộc về các quận: Q9, Q2, Q7, Bình Thạnh, Tân Phú, Bình Tân, Bình Chánh. Tổng số 404/485 bài đăng, chiếm hơn 80%."*
	- Tháng 7/2026: Vẫn 7 quận trên, hiện chiếm **67.4%** (18.933/28.088). Không áp đảo tuyệt đối như trước, cung đã loang ra các quận vùng ven khác như Nhà Bè, Thủ Đức (mỗi quận 3-4%).
- Các quận trung tâm vẫn ghi nhận mức giá/m² cao nhất & tăng nhanh. 
	- Tháng 9/2025: Quận 1, **174 triệu/m²**. 
	- Tháng 7/2026: **233.5 triệu/m²** — tăng gần 34%

Top 10 giá/m² HCM *(Đơn vị: Triệu VND)*: 
![[Pasted image 20260713140935.png]]

### Hà Nội

- Lần đầu có data Hà Nội trong series — chưa có baseline Tháng 9/2025 để so trước-sau.
- Giá TB & giá/m² TB cao hơn HCM: **9 tỷ / 92.5 triệu/m²** so với **8.22 tỷ / 86.8 triệu/m²**.
- Đặc biết, các cụm lõi (Hoàn Kiếm, Ba Đình, Tây Hồ...) đắt vượt trội:
	- Hoàn Kiếm: **338 triệu/m²** — quận đắt nhất cả nước, gần gấp rưỡi Quận 1 HCM (233.5 triệu/m²).

Top 10 giá/m² HN *(Đơn vị: Triệu VND)*: 
![[Pasted image 20260713140954.png]]

## Giá nhà & giá/m² tỷ lệ thuận 

Giá bds & giá/m² tương quan thuận: nhà càng đắt thì đơn giá/m² càng cao.

- 80% nhà DƯỚI 2 tỷ giá DƯỚI 40tr/m².
- 95% nhà TRÊN 5 tỷ giá TRÊN 60tr/m².

![[Pasted image 20260713141600.png]]

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

- Tháng 9/2025: dưới 3 tỷ gần như không có.
- Tháng 7/2026: tỷ lệ 3 ngủ < 3 tỷ:
	- HCM: 106/6.545 ≈ **1.6%**. Vẫn là tuyệt chủng. ![[Pasted image 20260713160127.png]]
	- HN: 11/5.822 ≈ **0.2%**. Còn tệ hơn cả HCM.![[Pasted image 20260713155927.png]]

# Nhà dưới 3 tỷ

Cửa dưới 3 tỷ gần như chỉ còn nằm ở vùng ven.
- HCM: 5 quận Quận 9, Bình Chánh, Quận 8, Bình Tân, Thủ Đức cộng lại đã chiếm **56.5%** tổng số tin dưới 3 tỷ (2.296/4.067) — toàn quận vùng ven, không quận nào trong nhóm này là trung tâm.
- HN còn lệch hơn: riêng **Gia Lâm** đã chiếm **38.2%** tin dưới 3 tỷ toàn thành phố, cộng thêm Nam Từ Liêm (17.6%) và Hoàng Mai (10.6%) là gần **66%**.
- Ở chiều ngược lại, các quận trung tâm gần như trắng phân khúc này: Quận 1/Quận 3 (HCM) và Hoàn Kiếm/Tây Hồ/Đống Đa (HN) mỗi nơi chưa tới 0.5% tổng số tin dưới 3 tỷ.

Hướng dẫn sử dụng daskboard kiếm nhà dưới 3 tỷ: 

![[Pasted image 20260713163627.png]]

# Kết

Túm lại, series này giờ đủ số để nói chắc hơn hồi tháng 9 năm ngoái: thị trường chung cư không chỉ đắt lên — nguồn cung giá mềm đang co cụm hẳn về vùng ven, trung tâm gần như trắng phân khúc dưới 3 tỷ ở cả hai thành phố. Ai đang tìm nhà dưới 3 tỷ, gần như chắc chắn sẽ phải chấp nhận đi xa trung tâm.

Lại câu hỏi từ bài trước, anh em gom được mấy mét đất thành phố rồi nào? 

> P/S: Mình sẽ sớm lên bài tiếp theo về thị trường nhà đất. Lần này sớm thật, không ngâm thêm 10 tháng nữa đâu. Yên tâm =)), số tôi có đây hết rồi, anh em tin tôi.

