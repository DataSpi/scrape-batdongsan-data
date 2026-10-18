Bài thứ ba trong series, sau [chung cư update tháng 7/2026](chung-cu-update-2026-07-personal.md) và [chung cư mini](chung-cu-mini-2026-07-personal.md). Lần này pipeline đã crawl xong nhóm **nhà đất**: nhà riêng, nhà mặt phố, biệt thự liền kề, shophouse nhà phố thương mại — loại hình mà bài P1 hồi Sept 2025 chưa từng đụng tới.

Spoiler trước: nếu 2 bài kia làm mọi người hơi nản vì cửa chung cư giá mềm đang hẹp lại, thì bài này sẽ nản hơn. Vào việc luôn.

# Khai báo kĩ thuật

- Nguồn dữ liệu: [https://batdongsan.com.vn/](https://batdongsan.com.vn/), 4 loại hình `nhà riêng`, `nhà mặt phố`, `nhà biệt thự liền kề`, `shophouse nhà phố thương mại` — lần đầu tiên pipeline crawl nhóm này, tất cả cùng ngày **13/7/2026** (giống chung cư mini), nên chưa có baseline cũ để so trước-sau.
- Cỡ mẫu: 48.606 tin, khá lớn — không phải data mỏng như bài chung cư mini. Chi tiết: nhà riêng 27.973, nhà mặt phố 11.440, biệt thự liền kề 7.857, shophouse 1.336.
- Note quan trọng: nhà đất có đuôi giá siêu cao (mặt phố cao nhất tới 999.000 triệu = **999 tỷ**, diện tích tới hơn 12.000m²) — đây là nhà/đất thương mại/mặt tiền lớn thật, không hẳn là lỗi parse, nhưng nó kéo **số trung bình (mean)** lệch hẳn lên. Bài này dùng mean cho nhất quán với 2 bài trước, nhưng có ghi kèm median ở phần có outlier rõ — đọc kỹ trước khi trích dẫn lại số trung bình.
- Kỹ thuật & data viz: xem [Khai báo kĩ thuật ở bài chung cư update](chung-cu-update-2026-07-personal.md#khai-báo-kĩ-thuật).

# Tổng quan

## Giá theo loại hình — đắt hơn chung cư một bậc, không phải một chút

| Loại hình | TP | Giá TB | Giá/m² TB | Diện tích TB |
|---|---|---|---|---|
| Nhà riêng | HCM | 9.20 tỷ | 129.2 tr/m² | 77.3m² |
| Nhà riêng | HN | 16.32 tỷ | 269.3 tr/m² | 59.3m² |
| Nhà mặt phố | HCM | 44.91 tỷ | 249.8 tr/m² | 196.5m² |
| Nhà mặt phố | HN | 70.85 tỷ | 531.0 tr/m² | 153.5m² |
| Biệt thự liền kề | HCM | 41.00 tỷ | 187.2 tr/m² | 214.0m² |
| Biệt thự liền kề | HN | 46.16 tỷ | 290.4 tr/m² | 164.4m² |
| Shophouse | HCM | 27.77 tỷ | 186.1 tr/m² | 158.8m² |
| Shophouse | HN | 26.84 tỷ | 228.9 tr/m² | 133.7m² |

So với chung cư thường (HCM 8.22 tỷ / 86.7 tr/m², HN 9.01 tỷ / 92.5 tr/m²) — **ngay cả loại nhà đất "rẻ" nhất (nhà riêng) cũng đã đắt hơn chung cư 1.1-1.8 lần về tổng giá, và 1.5-2.9 lần về giá/m²**. Ba loại còn lại (mặt phố, biệt thự, shophouse) đắt gấp 3-8 lần chung cư. Đây không phải chênh lệch nhỏ như giữa HCM và HN ở 2 bài trước — đây là một bậc giá hoàn toàn khác.

Một điều lặp lại từ 2 bài trước: **Hà Nội đắt hơn HCM ở mọi loại hình trừ shophouse** — đúng pattern đã thấy ở chung cư.

[Ảnh: bảng so sánh giá theo loại hình]

## Diện tích to hơn hẳn — nhưng giá/m² cũng cao hơn hẳn

Nhà đất to hơn chung cư nhiều lần (biệt thự/mặt phố trung bình 150-215m², so với chung cư 86m²) — dễ hiểu vì có đất. Nhưng đơn giá/m² cũng cao hơn 1.5-6 lần (`nhà riêng` 164 tr/m² vs chung cư 84 tr/m² tính gộp cả nước; `nhà mặt phố` lên tới 303 tr/m²). Tức là nhà đất không "rẻ hơn tính theo m²" như trực giác thường nghĩ (mua đất to sẽ được giá tốt hơn) — thực ra đắt hơn hẳn trên từng m², cộng thêm việc phải mua nhiều m² hơn.

## Phân hóa theo vị trí — các khu đô thị mới lặp lại

Một pattern lặp đi lặp lại ở cả 4 loại hình, trùng khớp với phát hiện ở bài chung cư: **Quận 2, Quận 9 (HCM) và Hà Đông, Nam Từ Liêm (HN)** liên tục xuất hiện ở top nguồn cung — đây đều là các khu đô thị mới quy mô lớn (Vinhomes, Ecopark, Geleximco...), không phải khu dân cư truyền thống.

Điểm đắt nhất tìm được trong toàn bộ 3 bài series: **nhà mặt phố Hoàn Kiếm, TB 133.66 tỷ / 768.1 tr/m²** — hơn gấp đôi giá/m² của chung cư đắt nhất từng ghi nhận (338 tr/m², cũng ở Hoàn Kiếm).

[Ảnh: bản đồ/bảng phân bổ theo quận, 4 loại hình]

# Phương pháp phân tích

Giống bài chung cư, mình gán mỗi loại hình cho một nhóm người mua và một ngân sách kỳ vọng — vẫn là ước lượng chủ quan, không phải khảo sát:

1. **Nhà riêng** → gia đình phổ thông muốn có đất riêng để ở, không kinh doanh mặt tiền.
   - Ngân sách giả định: **5 tỷ** (tương đương mốc "gia đình 3 thế hệ" ở bài chung cư).
2. **Nhà mặt phố** → hộ kinh doanh nhỏ, vừa ở vừa buôn bán mặt tiền.
   - Ngân sách giả định: **10 tỷ**.
3. **Biệt thự liền kề** → gia đình khá giả, muốn không gian sống riêng biệt cao cấp hơn.
   - Ngân sách giả định: **20 tỷ**.
4. **Shophouse nhà phố thương mại** → nhà đầu tư, mua để cho thuê mặt bằng trong khu đô thị mới.
   - Ngân sách giả định: **20 tỷ**.

# Nhà riêng

> Khách hàng điển hình:
> - Gia đình phổ thông, muốn đất riêng để ở
> - Ngân sách: 5 tỷ

- HCM: **20.8%** tin dưới 5 tỷ (4.181/20.103), dưới 10 tỷ thì khá hơn hẳn — **78.3%**.
- HN: chỉ **5.4%** dưới 5 tỷ (364/6.748), dưới 10 tỷ cũng mới **38.0%** — đắt hơn HCM rất nhiều ở đúng phân khúc "rẻ nhất" của nhà đất.

## Phân bổ

- HCM: cung nhà riêng dồn về Gò Vấp (9.9%), Bình Tân (9.7%), Bình Thạnh (9.1%), Thủ Đức (8.3%), Quận 12 (8.0%), Tân Phú (7.9%) — toàn quận cận trung tâm/vùng ven, giá/m² 83-157 tr.
- HN: dồn về Cầu Giấy (13.1%), Đống Đa (12.8%), Long Biên (10.9%), Hà Đông (8.9%) — nội thành/cận nội thành, giá/m² cao hơn hẳn HCM (223-336 tr/m²).

[Ảnh: phân bổ quận nhà riêng]

# Nhà mặt phố

> Khách hàng điển hình:
> - Hộ kinh doanh nhỏ, vừa ở vừa buôn bán mặt tiền
> - Ngân sách: 10 tỷ

- HCM: chỉ **19.8%** tin dưới 10 tỷ (1.779/8.981).
- HN: gần như không có — **1.8%** dưới 10 tỷ (37/2.083). Muốn mặt phố Hà Nội với 10 tỷ gần như là nhiệm vụ bất khả thi.

## Phân bổ

- HCM: Quận 1 dẫn đầu (9.8%, TB 83.79 tỷ) rồi mới đến Tân Bình, Tân Phú, Thủ Đức, Bình Thạnh, Quận 7.
- HN: Cầu Giấy (16.1%), Hai Bà Trưng (10.0%), Đống Đa (9.8%) dẫn đầu về số lượng, nhưng **Hoàn Kiếm mới là đắt nhất dù chỉ chiếm 9.0% nguồn cung** — TB 133.66 tỷ, gần gấp đôi Cầu Giấy.

[Ảnh: phân bổ quận nhà mặt phố]

# Biệt thự liền kề

> Khách hàng điển hình:
> - Gia đình khá giả, muốn không gian sống cao cấp hơn
> - Ngân sách: 20 tỷ

- HCM: **37.4%** tin dưới 20 tỷ (1.206/3.222).
- HN: chỉ **21.7%** dưới 20 tỷ (804/3.706).

## Phân bổ

- HCM: Quận 9 (19.8%) và Quận 2 (17.4%) cộng lại gần 40% tổng cung — đúng hai quận cũng dẫn đầu nguồn cung chung cư ở bài trước, cùng là khu vực đại đô thị mới.
- HN: Hà Đông áp đảo với **24.1%** — khu đô thị mới kiểu Geleximco/An Khánh, giá TB "mềm" nhất trong các quận top (30.16 tỷ) so với Tây Hồ (100.39 tỷ, đắt nhất) hay Nam Từ Liêm (49.10 tỷ).

[Ảnh: phân bổ quận biệt thự liền kề]

# Shophouse nhà phố thương mại

> Khách hàng điển hình:
> - Nhà đầu tư, mua để cho thuê mặt bằng kinh doanh trong khu đô thị mới
> - Ngân sách: 20 tỷ

- HCM: **55.0%** tin dưới 20 tỷ (334/607) — loại hình duy nhất trong nhóm nhà đất mà quá nửa nguồn cung nằm trong tầm ngân sách giả định.
- HN: **50.1%** dưới 20 tỷ (269/537) — tương đương HCM, khác với 3 loại hình trên đều có HN đắt hơn hẳn.

## Phân bổ

- HCM: Quận 2 áp đảo — **30.2%** tổng cung shophouse toàn thành phố.
- HN: Nam Từ Liêm dẫn đầu — **26.9%**.

> Cả hai quận dẫn đầu đều là đúng những cái tên đã lặp lại xuyên suốt bài này (và cả bài chung cư): Quận 2 và Nam Từ Liêm — nơi các đại đô thị xây nguyên khu shophouse đồng bộ, khác hẳn kiểu nhà mặt phố tự phát ở khu dân cư cũ.

[Ảnh: phân bổ quận shophouse]

# Cửa giá mềm: nhà đất có còn không?

Ghép cả 3 bài trong series lại, nhìn theo đúng một câu hỏi xuyên suốt — "với ngân sách khiêm tốn, tôi còn lựa chọn nào":

| Loại hình | Ngưỡng "giá mềm" | HCM | HN |
|---|---|---|---|
| Chung cư mini | dưới 3 tỷ | 92.9% | 98.6% |
| Chung cư thường | dưới 3 tỷ | 15.2% | 4.3% |
| Nhà riêng (rẻ nhất nhóm nhà đất) | dưới 5 tỷ | 20.8% | 5.4% |
| Nhà mặt phố / Biệt thự / Shophouse | dưới 10-20 tỷ | 19.8-55.0% | 1.8-50.1% |

Nhìn cả bảng thì thấy rõ: **chung cư mini là ngoại lệ duy nhất còn giữ giá mềm**. Mọi loại hình còn lại — kể cả khi mình đã nới ngân sách giả định lên gấp 2-7 lần so với chung cư (5-20 tỷ thay vì 2-3 tỷ) — tỷ lệ "vừa túi tiền" vẫn thấp hơn hẳn chung cư mini, và ở Hà Nội thì hầu hết còn thấp hơn cả chung cư thường.

# Kết

Túm lại: nhà đất là một bậc giá hoàn toàn khác so với chung cư, không phải chênh lệch vài chục phần trăm. Muốn có đất riêng ở hai thành phố này bây giờ, ngân sách phải tính bằng chục tỷ chứ không phải vài tỷ — và Hà Nội, một lần nữa, đắt hơn HCM ở gần như mọi mặt.

Ba bài, ba lát cắt: chung cư đang đóng cửa giá mềm, chung cư mini là lối thoát hiếm hoi còn sót lại, còn nhà đất thì gần như chưa bao giờ mở cửa đó cho ngân sách khiêm tốn.

> P/S: Bài tiếp theo trong series, mình định làm so sánh thuê vs mua — dữ liệu giá thuê cũng vừa crawl xong. Hẹn gặp lại, và như mọi lần, anh em tin tôi đi =)))
