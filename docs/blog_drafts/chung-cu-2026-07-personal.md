Khởi động lại dự án phân tích giá bất động sản sau đúng 10 tháng, [bài phân tích giá chung cư đầu tiên](https://spyno.substack.com/p/i-xem-nha-cung-data-analyst-p1) đăng tháng 9/2025. Mình đã nâng cấp dự án sau một khoảng thời gian dùi mài nhiều kĩ năng mới. Bộ số được mở rộng từ vài trăm lên hơn 50 ngàn điểm dữ liệu. Chi tiết kĩ thuật của dự án cũng thú vị và cho mình nhiều bài học, nhưng có lẽ mình sẽ viết một bài riêng.

Giờ thì mời mọi người lại soi giá chung cư cùng mình, vì thú thật là soi một mình thấy hơi choáng. 

# Khai báo kĩ thuật

- Nguồn dữ liệu: [https://batdongsan.com.vn/](https://batdongsan.com.vn/)
    - Hiện tại dự án đã update và crawl cả dữ liệu chưa-xác-thực, do mình thấy nếu chỉ lấy đã-xác-thực thì bộ số ít quá, bỏ sót rất nhiều. 
- Kỹ thuật:
    - Tool cào Python: HTTP Request, BeautifulSoup
    - Github: [https://github.com/DataSpi/scrape-batdongsan-data](https://github.com/DataSpi/scrape-batdongsan-data)
    - Data visualization: [Google Looker Studio](https://lookerstudio.google.com/reporting/9e21618f-97dc-4480-b101-cbda26b9b2a5)
- Note:
	- Bài phân tích vẫn sử dụng địa giới hành chính cũ trước sáp nhập để phân tích dữ liệu. Đơn giản là vì mình quen, đọc địa giới hành chính mới mình chả biết đâu vào với đâu. 

# Tổng quan

## Nguồn cung

Nguồn cung tập trung ở phân khúc 3-10 tỷ ở cả HCM & HN (~60% tổng).

![[Pasted image 20260713140759.png]]

Chung cư 2PN & 3PN chiếm 70% tổng cung. 

![[Pasted image 20260714112120.png]]

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

# Phương pháp phân tích

Khi phân tích giá nhà, mình tạm chia người mua chung cư thành 3 nhóm với nhu cầu và túi tiền như sau:
1. Người độc thân, hoặc vợ chồng chưa/không có con → thường tìm căn 1PN.
	- Ngân sách giả định: dưới 2 tỷ.
2. Gia đình nhỏ, vợ chồng và 1–2 con → thường tìm căn 2PN.
	- Ngân sách giả định: 2–3 tỷ.
3. Gia đình 3 thế hệ cùng sinh sống → thường tìm căn 3PN.
	- Ngân sách giả định: 3–5 tỷ.
  
Các mốc ngân sách trên là ước lượng dựa trên kinh nghiệm cá nhân của mình. Mục đích nhằm trả lời được câu hỏi của nhóm người mua điển hình: Với từng túi tiền và nhu cầu, tôi có những lựa chọn nào?.

# 1 phòng ngủ

> Khách hàng điển hình: 
> - Người độc thân, hoặc vợ chồng chưa/không có con
> - Ngân sách: 2 tỷ

Tháng 9/2025: 
- HCM: khả năng tìm được căn 1PN dưới 2 tỷ là 10/72 ≈ 14% (tổng 72 bài đăng 1PN).
Tháng 7/2026: tỷ lệ 1 ngủ < 2 tỷ:  
- HCM: 198/3.358 ≈ **5.9%**. (đã lọc giá null)![[Pasted image 20260713152336.png]]
- HN: 39/1122 ≈ **3.5%**.![[Pasted image 20260713152302.png]]

## Phân bổ

- HCM: nguồn cung 1PN tập trung ở Quận 2, Quận 9, Quận 7 (**57.4%**, 1.916/3.343). Cửa dưới 2 tỷ thì dạt hẳn ra Quận 9 (28.8%), Bình Chánh (13.1%), Bình Tân (12.6%) — ba quận vùng ven này gộp lại đã hơn nửa số tin rẻ.
- HN: cung 1PN dồn cực mạnh về Gia Lâm (35.8%) và Nam Từ Liêm (20.9%) — hai quận chiếm hơn nửa tổng cung toàn thành phố. Cửa dưới 2 tỷ gần như chỉ còn ở Gia Lâm: **56.4%** (22/39 tin).

# 2 phòng ngủ

> Khách hàng điển hình: 
> - Gia đình nhỏ, vợ chồng và 1–2 con
> - Ngân sách: 2–3 tỷ

## Tỷ lệ kiếm được nhà

Tháng 9/2025:  dưới 2 tỷ là 5.3%, dưới 3 tỷ là 30%.
Tháng 7/2026:
- HCM: dưới 2 tỷ ≈ **3.0%** (435/14.622), dưới 3 tỷ ≈ **16.8%** (2.460/14.622) tức mất 13.2 điểm % trong 10 tháng.![[Pasted image 20260713151923.png]]
- HN: dưới 2 tỷ ≈ **0.2%** (16/7475), dưới 3 tỷ ≈ **3%** (225/7475). OMG!![[Pasted image 20260713151959.png]]

## Phân bổ

Tách riêng 2PN thì cửa dưới 3 tỷ vẫn dồn về vùng ven, nhưng dàn trải hơn 1PN/3PN — không quận nào áp đảo tuyệt đối:
- HCM: 5 quận rẻ nhất — Bình Chánh, Thủ Đức, Quận 9, Bình Tân, Quận 12 — cộng lại chiếm **57.2%** số tin 2PN dưới 3 tỷ (1.407/2.460), quận cao nhất là Bình Chánh chiếm 15.5%.
- HN: **Hoàng Mai** dẫn đầu với 25.3%, cộng thêm Hà Đông là **41.3%** tin 2PN dưới 3 tỷ.
- Ngược lại, nguồn cung 2PN nói chung (không lọc giá) vẫn tập trung ở Quận 2/Quận 7/Quận 9 (HCM, 43.7%) và Nam Từ Liêm/Hà Đông/Hoàng Mai (HN, 43.1%) — quận có nhiều 2PN nhất chưa chắc là quận có 2PN rẻ nhất.

# 3 phòng ngủ

> Khách hàng điển hình: 
> - Gia đình 3 thế hệ cùng sinh sống
> - Ngân sách: 3–5 tỷ

- Tháng 9/2025: 3 ngủ dưới 5 tỷ 29/134 ≈ **22%** số căn 3PN.
- Tháng 7/2026: tỷ lệ 3 ngủ <5 tỷ:
	- HCM: 1260/6545 ≈ **19,2%**.![[Pasted image 20260713160127.png]]
	- HN: 292/5822 ≈ **5%**. Tệ hơn HCM rất nhiều.![[Pasted image 20260713155927.png]]

## Phân bổ

- HCM: Quận 7 và Quận 2 gánh gần một nửa tổng cung 3PN (**47.5%**, 3.113/6.545). Nhưng cửa dưới 5 tỷ thì Quận 9 dẫn đầu (25.8%), theo sau là Quận 8 và Tân Phú (~13% mỗi quận); Quận 7/Quận 2 tụt xuống chỉ còn 8.2%/4.2%.
- HN: Nam Từ Liêm, Cầu Giấy, Thanh Xuân, Hà Đông chiếm hơn nửa cung 3PN toàn thành (52%). Cửa dưới 5 tỷ lại trải khá đều: Gia Lâm (16.4%), Đông Anh & Long Biên (12.3% mỗi quận), Hoàng Mai (11.0%) — không quận nào áp đảo.

# Hướng dẫn sử dụng dashboard

Dashboard hiện tại gồm 3 trang: 
- Tổng quan
- Theo khoảng giá
- Theo dự án

Người dùng có thể tương tác với các bảng và đồ thị trong dashboard: 
- Các filters ở phần header để lọc dữ liệu
- Rà chuột qua để đọc thêm thông tin
- Click chọn các đối tượng để lọc thông tin theo đối tượng đó

Ví dụ, kiếm nhà dưới 3 tỷ. Làm theo các bước (1), (2), (3) trong hình: 

![[Pasted image 20260713163627.png]]

# Kết

Nhìn chung giá chung cư trên thị trường đắt lên so với hồi tháng 9 năm ngoái, và nguồn cung giá mềm đang dạt hẳn về vùng ven. Các quận trung tâm cả HN và HCM đã trắng dần phân khúc dễ tiếp cận. Người trẻ muốn mua nhà mà tài chính không quá dư giả gần như chắc chắn phải chấp nhận xa trung tâm. 

Lại câu hỏi từ bài viết trước, anh em gom được mấy mét đất thành phố rồi nào?

> P/S: Mình sẽ sớm lên bài tiếp theo về chủ đề này, có thể sẽ là bài về giá thuê, so sánh thuê và mua hoặc một phân tích như trên về thị trường nhà đất. Lần này sẽ sớm thật, không ngâm 10 tháng như lần trước nữa =))) anh em tin tôi. 

