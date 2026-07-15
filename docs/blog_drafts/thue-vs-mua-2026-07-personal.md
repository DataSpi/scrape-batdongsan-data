Hẹn từ [bài chung cư update tháng 7/2026](chung-cu-update-2026-07-personal.md) là bài tiếp theo "có thể sẽ là bài về giá thuê, so sánh thuê và mua" — lần này giữ đúng lời hứa thật. Pipeline vừa crawl xong dữ liệu cho thuê căn hộ chung cư, đủ để trả lời câu hỏi mà chắc ai cũng từng tự hỏi ít nhất một lần: rốt cuộc thuê hay mua lợi hơn?

Bài này nhìn câu hỏi đó từ hai góc: người cần chỗ ở, và người mua để đầu tư cho thuê. Số thì không nhiều nhưng tính ra khá rõ ràng — mời mọi người soi cùng, biết đâu đọc xong lại đổi ý về kế hoạch mua nhà của mình.

# Khai báo kĩ thuật

- Nguồn dữ liệu: [https://batdongsan.com.vn/](https://batdongsan.com.vn/), loại hình `cho thuê căn hộ chung cư` — lần đầu tiên pipeline crawl loại này, chỉ có data của ngày **13/7/2026**. Tổng **11.093 tin** (HCM 7.674, HN 3.419), so với 53.713 tin chung cư bán đã crawl nhiều tuần — số thuê nên đọc như một lát cắt thăm dò, không chắc như bộ số bán.
- Đơn vị giá không giống nhau: giá bán là trọn gói (tỷ), giá thuê là theo tháng (triệu/tháng) — hai con số này **không so trực tiếp được**. Cả bài dùng 2 chỉ số quy đổi ở mục dưới để so cho đúng.
- Note quan trọng: bộ lọc outlier theo giá/m² mà bài chung cư update dùng (5-1000 triệu/m², đúc kết từ dữ liệu bán) **chưa có bản tương ứng cho data thuê** vì thuê mới crawl lần đầu, chưa đủ dữ liệu để đúc kết ngưỡng. Lúc tính số cho bài này, phát hiện 1 tin bị lỗi parse diện tích thành **76.000.000 m²** (một căn 2PN ở Masteri Lumiere) — kéo lệch hẳn trung bình theo phân khúc. Mình tự lọc thô diện tích 15-200m² và giá thuê 1-200 triệu/tháng trước khi tính lại, số trong bài là số đã lọc.
- Kỹ thuật & data viz: xem [Khai báo kĩ thuật ở bài chung cư update](chung-cu-update-2026-07-personal.md#khai-báo-kĩ-thuật) — không lặp lại ở đây. Riêng dashboard Looker Studio: mart dữ liệu thuê mới thêm hôm nay nên **chưa có trang riêng để lọc/so thuê vs bán** — phần này để sau.

# Framework: lấy gì làm thước đo?

Vì không so trực tiếp giá bán (tỷ) với giá thuê (triệu/tháng) được, bài dùng 2 chỉ số kinh điển trong tài chính bất động sản:

- **Price-to-Rent ratio (P/R)** = giá bán ÷ (giá thuê × 12 tháng). Đọc nôm na: mất bao nhiêu năm tiền thuê thì bằng tiền mua đứt căn nhà — chưa tính lãi vay hay biến động giá. Ngưỡng kinh điển ([nguồn](https://www.fool.com/investing/stock-market/market-sectors/real-estate-investing/basics/price-to-rent-ratio/)): **dưới 15 nên mua, 15-20 vùng xám, trên 20 nên thuê**.
- **Gross rental yield** = 1/P/R × 100%/năm — dùng cho góc nhìn nhà đầu tư, so với lãi suất gửi tiết kiệm.

Nói thẳng luôn hai giới hạn của cách tính này: (1) đây là công thức đơn giản hoá, chưa trừ lãi vay/thuế/phí quản lý, chưa cộng kỳ vọng tăng giá nhà — không phải mô hình tài chính đầy đủ; (2) ngưỡng 15/20 vốn đúc kết từ thị trường Mỹ, nơi không có thuế BĐS hàng năm và cấu trúc vay khác hẳn Việt Nam, nên chỉ nên đọc như tín hiệu định hướng, không phải luật bất di bất dịch.

# Góc nhìn người cần chỗ ở: thuê hay mua lợi hơn?

**Cả hai thành phố đều vượt xa ngưỡng "nên thuê" (20), và Hà Nội còn nghiêng về thuê mạnh hơn TP.HCM.**

- HCM: giá bán TB **8.22 tỷ / 86.73 tr/m²**, giá thuê TB **20.97 tr/tháng / 0.244 tr/m²/tháng** → P/R ratio **≈ 29.6 năm**.
- HN: giá bán TB **9.01 tỷ / 92.55 tr/m²**, giá thuê TB **16.8 tr/tháng / 0.193 tr/m²/tháng** → P/R ratio **≈ 40.0 năm**.

[Ảnh: bảng P/R ratio theo thành phố]

Tách theo phân khúc phòng ngủ, dùng lại 3 nhóm khách hàng điển hình từ bài chung cư update (độc thân/1PN, gia đình nhỏ/2PN, 3 thế hệ/3PN):

| TP / phân khúc | Giá bán TB (tr/m²) | Giá thuê TB (tr/m²/tháng) | P/R ratio |
|---|---|---|---|
| HN 1PN | 88.87 | 0.245 | **30.2 năm** |
| HN 2PN | 86.11 | 0.190 | **37.8 năm** |
| HN 3PN | 95.92 | 0.181 | **44.2 năm** |
| HCM 1PN | 90.66 | 0.278 | **27.2 năm** |
| HCM 2PN | 78.41 | 0.219 | **29.8 năm** |
| HCM 3PN | 94.38 | 0.267 | **29.5 năm** |

- Ở HN, P/R ratio tăng dần theo số phòng ngủ — 1PN 30.2 năm, 2PN 37.8 năm, 3PN lên tới 44.2 năm. Càng mua nhà to ở HN thì xét thuần kinh tế càng bất lợi so với thuê.
- Ở HCM thì ổn định hơn hẳn, quanh 27-30 năm ở cả 3 phân khúc — không có kiểu "nhà to thiệt hơn" rõ như HN.
- Cả 6 nhóm đều vượt xa ngưỡng 20 của framework — nghĩa là xét thuần kinh tế ngắn/trung hạn, **thuê đang lợi hơn mua rõ rệt ở cả hai thành phố, mọi phân khúc**. Tất nhiên đây chưa phải toàn bộ câu chuyện — mua nhà còn để an cư, tâm lý sở hữu, không chỉ là bài toán tiền.

# Góc nhìn nhà đầu tư: mua để cho thuê có lời không?

**Xét thuần dòng tiền cho thuê, gửi tiết kiệm ngân hàng hiện đang lời hơn mua chung cư cho thuê.**

- Gross rental yield tự tính: HCM **≈ 3.4%/năm** (quanh 3.3-3.7% ở mọi phân khúc), HN **≈ 2.5%/năm** (giảm dần từ 3.3% ở 1PN xuống 2.3% ở 3PN).
- Đối chiếu lãi suất tiết kiệm kỳ hạn 12 tháng hiện tại (7/2026): ngân hàng lớn (Vietcombank, BIDV, VietinBank) quanh **5.9-6%/năm**, ngân hàng nhỏ/gửi online cao nhất tới **7.3-7.4%/năm** ([Techcombank](https://techcombank.com/thong-tin/blog/lai-suat-tiet-kiem), [Cake](https://cake.vn/tin-tuc/tai-chinh/lai-suat-gui-tiet-kiem-ngan-hang-nao-cao-nhat)).
- Yield cho thuê tự tính (2.3-3.7%) **thấp hơn hẳn lãi suất tiết kiệm ở mọi kỳ hạn** — kể cả so với ngân hàng lớn rẻ nhất. Đối chiếu thêm với báo chí: VnExpress dẫn số liệu ngành cho rằng yield cho thuê chung cư HCM "phổ biến dưới 2%, thấp hơn lãi suất tiết kiệm" ([nguồn](https://vnexpress.net/ty-suat-loi-nhuan-cho-thue-chung-cu-pho-bien-duoi-2-4858772.html)) — số tự tính của mình (3.4%) cao hơn con số đó một chút, nhưng cùng chung một kết luận.

[Ảnh: bảng yield theo thành phố + phân khúc, đối chiếu lãi suất tiết kiệm]

*(Giới hạn cần nói rõ: đây là yield thuần túy dòng tiền cho thuê, chưa trừ chi phí quản lý/thuế/khấu hao, và quan trọng hơn — chưa cộng kỳ vọng tăng giá vốn của căn nhà. Bài chung cư update từng ghi nhận giá/m² ở một số quận lõi tăng gần 34% chỉ trong 10 tháng, nhưng đó là vài quận đặc biệt, không đại diện cho cả thị trường, nên mình không đủ cơ sở để bịa ra một con số "tổng lợi nhuận kỳ vọng" đáng tin. Nếu tin vào kịch bản tăng giá tương tự trên diện rộng thì bài toán đầu tư có thể khác hẳn — nhưng đó là một khoản cược, không phải con số đo được.)*

# Kết

Xét thuần túy con số: dù đứng ở góc người ở hay người đầu tư, dữ liệu hiện tại đều nghiêng về phía thuê (và với nhà đầu tư, nghiêng về gửi tiết kiệm) hơn là mua. Nhưng đây mới là bức tranh kinh tế ngắn hạn dựa trên đúng 1 ngày dữ liệu thuê — chưa tính an cư, tâm lý sở hữu, hay kỳ vọng tăng giá dài hạn mà bộ số này chưa đo được.

Câu hỏi cũ vẫn còn đó: anh em gom được mấy mét đất thành phố rồi nào? Hay là thôi, đi thuê rồi đem phần chênh lệch gửi tiết kiệm cho lành?

> P/S: Bài tiếp theo dự kiến quay lại với chủ đề nhà đất (nhà riêng, nhà mặt phố, biệt thự liền kề) — lần này chắc chắn không phải đợi 10 tháng nữa đâu, tin tôi lần thứ hai =)))
