Đang ngồi viết tiếp bài [chung cư update tháng 7/2026](chung-cu-update-2026-07-personal.md) thì phát hiện pipeline vừa thêm được một loại hình mới: **chung cư mini**. Tò mò quá nên tách riêng ra một bài ngắn, tranh thủ đối chiếu luôn với bức tranh "cửa giá mềm đang đóng" ở bài kia.

Bài này ngắn hơn bài chung cư thường nhiều — vì data còn rất mới, mới crawl được đúng 1 ngày.

# Khai báo kĩ thuật

- Nguồn dữ liệu: [https://batdongsan.com.vn/](https://batdongsan.com.vn/), loại hình `căn hộ chung cư mini` — lần đầu tiên pipeline crawl loại này, chỉ có data của ngày **13/7/2026** (so với chung cư thường đã crawl nhiều tuần).
- Cỡ mẫu rất nhỏ so với phần còn lại: 347 tin chung cư mini, so với 53.713 tin chung cư thường — chưa bằng 1%. Số ở bài này nên đọc như một lát cắt thăm dò, không chắc như bài chung cư thường.
- Note quan trọng: data thô có một số tin rõ ràng bị gắn nhầm loại hình hoặc lỗi parse (vd tin ghi "27 phòng ngủ" giá 82 tỷ, "80 phòng ngủ" — không hợp lý cho một căn chung cư mini thật). Mình lọc lại còn `bedrooms` từ 1-3 và diện tích ≤100m² cho khớp với định nghĩa thực tế của chung cư mini (căn nhỏ, thường 1-2 phòng ngủ) — sau lọc còn 151/189 tin ở HN (mất 20%) và 100/158 tin ở HCM (mất 37%). HCM mất nhiều hơn vì có vẻ nhiễu nặng hơn.
- Kỹ thuật & data viz: xem [Khai báo kĩ thuật ở bài chung cư update](chung-cu-update-2026-07-personal.md#khai-báo-kĩ-thuật) — không lặp lại ở đây.

# Tổng quan

## Giá & diện tích, so với chung cư thường

**Chung cư mini rẻ hơn hẳn, nhưng mức độ "rẻ" khác nhau giữa hai thành phố.**

- HN: chung cư mini TB **2.06 tỷ / 42.6 tr/m² / 47.6m²** — so với chung cư thường **9.01 tỷ / 92.5 tr/m² / 93.1m²**. Giá/m² chỉ bằng **46%** chung cư thường.
- HCM: chung cư mini TB **1.95 tỷ / 53.0 tr/m² / 38.8m²** — so với chung cư thường **8.22 tỷ / 86.7 tr/m² / 85.7m²**. Giá/m² bằng **61%** chung cư thường.
- Tổng giá hai thành phố gần bằng nhau (~2 tỷ), nhưng HCM đắt hơn HN tính theo m² — vì căn HCM nhỏ hơn hẳn (38.8m² so với 47.6m²). Cùng khoảng 2 tỷ, mua chung cư mini ở HN được nhiều diện tích hơn ở HCM.

[Ảnh: bảng so sánh chung cư mini vs chung cư thường]

## Phân bổ theo quận — khác hẳn pattern chung cư thường

Bài chung cư update chỉ ra chung cư thường dồn về các quận **vùng ven** (HCM: Q9/Q2/Q7...; HN: Nam Từ Liêm/Hà Đông...). Chung cư mini thì ngược lại:

- HN: tập trung ở các quận nội thành cũ — **Thanh Xuân** (33 tin, 22%), **Đống Đa** (29 tin, 19%), Nam Từ Liêm (19 tin, 13%), Hai Bà Trưng (14 tin, 9%), Cầu Giấy (14 tin, 9%). Đây toàn là khu dân cư lâu đời, không phải vùng ven mới phát triển.
- HCM: dàn trải hơn, không quận nào áp đảo — Bình Chánh (19 tin, 19%), Quận 3 (14 tin, 14%), Bình Tân (10 tin, 10%), Thủ Đức/Quận 5/Tân Bình (8 tin mỗi quận, ~8%). Có cả quận trung tâm (Quận 3, Quận 5) lẫn vùng ven (Bình Chánh, Bình Tân) — không rõ pattern như HN.

> Đối chiếu với bài trước: chung cư thường "né" trung tâm vì quỹ đất dự án lớn chỉ còn ở vùng ven. Chung cư mini thì ngược lại — nó *là* cách lách quỹ đất nhỏ lẻ trong khu dân cư cũ (nhà riêng cải tạo lên vài tầng, chia thành nhiều căn), nên xuất hiện đúng ở những nơi chung cư thường không xây được.

[Ảnh: phân bổ quận chung cư mini HCM & HN]

# Cửa giá mềm: chung cư mini có phải lối thoát?

Bài chung cư update tính được: chung cư thường dưới 3 tỷ hiện chỉ còn **15.2%** ở HCM, **4.3%** ở HN. Với đúng mốc ngân sách "gia đình nhỏ" (2-3 tỷ) mà bài đó đặt ra, cửa gần như đã đóng.

Chung cư mini thì khác hẳn:

- HN: **98.6%** tin chung cư mini có giá dưới 3 tỷ (136/138).
- HCM: **92.9%** tin chung cư mini có giá dưới 3 tỷ (91/98).

So với chung cư thường, tỷ lệ "vừa túi tiền 3 tỷ" của chung cư mini cao hơn **20-23 lần**. Đúng như tên gọi — đây gần như là loại hình duy nhất còn giữ được mức giá của phân khúc "gia đình nhỏ" mà bài trước mô tả là đang biến mất.

*(Chưa bàn tới rủi ro pháp lý/an toàn cháy nổ vốn gắn liền với chung cư mini ở Việt Nam — đó là câu chuyện khác, ngoài phạm vi phân tích giá của bài này, nhưng chắc chắn là một phần lý do giá rẻ hơn hẳn.)*

# Kết

Túm lại: khi cửa giá mềm của chung cư thường đang đóng dần (bài trước), chung cư mini là loại hình gần như duy nhất vẫn giữ được mức giá dưới 3 tỷ ở cả hai thành phố — đổi lại là diện tích nhỏ hơn nhiều (dưới 50m²) và nằm ở những khu vực khác hẳn (nội thành cũ ở HN, dàn trải ở HCM). Data còn mỏng nên đây mới là lát cắt thăm dò, không phải kết luận chắc.

> P/S: Nếu data chung cư mini dày thêm ở các lần crawl sau, mình sẽ quay lại bài này với bộ số lớn hơn — và nói thêm về khía cạnh pháp lý mà bài này cố tình bỏ qua.
