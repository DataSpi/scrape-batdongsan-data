---
name: real_estate_analyzer
description: Viết/nâng cấp bài blog phân tích dữ liệu bất động sản cho series Substack của DataSpi (spyno), theo đúng cấu trúc và giọng văn đã chốt ở bài "chung cư update tháng 7/2026". Dùng khi viết bài mới trong series (nhà đất, kỹ thuật, update định kỳ) hoặc khi chỉnh sửa draft trong docs/blog_drafts/.
---

# Blog writer — series phân tích BĐS của DataSpi

Skill này đúc kết cấu trúc và giọng văn đã ổn định qua nhiều vòng chỉnh sửa ở
`docs/blog_drafts/chung-cu-update-2026-07-personal.md` — coi bài đó là **bản mẫu tham
chiếu**, đọc lại nó nếu cần ví dụ cụ thể cho bất kỳ mục nào dưới đây.

Đây không phải giọng "tự sự" (xem `writer_personal`/`writer_serious` nếu có trong máy
— hai skill đó KHÔNG áp dụng cho series này). Đây là giọng phân tích dữ liệu thân mật,
tối giản kể chuyện, ưu tiên bullet + số liệu + insight rút gọn.

## Khi nào dùng

- Viết bài mới trong series (đã có: chung cư update; sắp có: nhà đất, kỹ thuật).
- Chỉnh sửa/mở rộng draft có sẵn trong `docs/blog_drafts/`.
- Viết phần "Phân bổ theo quận" hoặc bất kỳ phần so sánh theo thời gian nào cho bài
  mới, khi tác giả đã đưa số liệu nhưng chưa có văn bản.

## Cấu trúc bài — theo đúng thứ tự này

1. **Mở bài (không heading)** — 2 đoạn ngắn:
   - Đoạn 1: nhắc bối cảnh — bài trước (link + tháng/năm đăng), tóm tắt đã nâng cấp gì
     (bộ số lớn hơn bao nhiêu lần, kỹ năng mới), và một câu teaser bài khác sắp viết
     (không lan man giải thích, chỉ nêu sẽ có bài riêng).
   - Đoạn 2: câu mời độc giả xem cùng, ngắn, có thể tự giễu nhẹ ("soi một mình thấy
     hơi choáng").

2. **`# Khai báo kĩ thuật`** — bullet, không phải văn xuôi:
   - Nguồn dữ liệu (link) + note phương pháp thu thập (cái gì được include/exclude
     và lý do thật, không màu mè — vd "lấy cả tin chưa xác thực vì chỉ lấy xác thực
     thì bộ số ít quá").
   - Kỹ thuật: liệt kê tool, link GitHub, link data viz.
   - Note: caveat phương pháp quan trọng nhất của bài (vd địa giới hành chính cũ vs
     mới) — nêu lý do thật của tác giả, kể cả lý do "cá nhân" hơi buồn cười ("vì mình
     quen, đọc địa giới mới chả biết đâu vào với đâu"). Không né tránh caveat, đưa
     ngay từ đầu.

3. **`# Tổng quan`** — các nhận xét tổng thể *trước khi* đi vào từng phân khúc, mỗi
   nhận xét một `##` sub-heading riêng:
   - Nguồn cung (phân bổ theo khoảng giá)
   - Giá (so sánh giữa các thành phố/vùng nếu có nhiều hơn 1)
   - Phân hóa theo vị trí (theo từng thành phố, `###` riêng — nếu có baseline cũ thì
     trích nguyên văn bài cũ bằng *in nghiêng trong ngoặc kép*, rồi mới đưa số mới đối
     chiếu ngay bên dưới, thụt lề)
   - Bất kỳ tương quan nào đáng chú ý tìm thấy (giá vs giá/m², v.v.)
   - Mỗi mục: 1 câu nhận xét đứng đầu, bullet số liệu bên dưới, ảnh dashboard ngay sau
     (`![[Pasted image ...]]` nếu đã có, `[Ảnh: mô tả ngắn]` nếu chưa).

4. **`# Phương pháp phân tích`** — bắt buộc có nếu bài chia dữ liệu theo persona/nhóm
   người dùng (như số phòng ngủ → nhóm người mua). Format:
   - Liệt kê từng nhóm bằng số thứ tự, mỗi nhóm: mô tả persona (1 câu) + "Ngân sách
     giả định: X".
   - Đóng bằng 1 câu nói thẳng đây là ước lượng chủ quan của tác giả, không phải khảo
     sát/nghiên cứu, và nêu mục đích (trả lời "với túi tiền này, tôi có lựa chọn nào").
   - Không giấu tính chủ quan của mốc số — nói huỵch toẹt, kể cả nếu tác giả còn phân
     vân giữa hai mốc (giữ nguyên phân vân đó trong text thay vì giả vờ chắc chắn).

5. **Từng phân khúc (`# 1 phòng ngủ`, `# 2 phòng ngủ`, ...)** — lặp lại cùng khuôn cho
   mỗi phân khúc:
   - Mở bằng blockquote:
     ```
     > Khách hàng điển hình:
     > - <mô tả persona>
     > - Ngân sách: <X>
     ```
   - So sánh theo thời gian nếu có baseline: "Tháng X/2025: ..." rồi "Tháng Y/2026:"
     — mỗi mốc thời gian đưa số tuyệt đối lẫn %, format bắt buộc `x/y ≈ z%`, số % bold.
     Tách riêng theo từng thành phố/vùng nếu có nhiều hơn 1, mỗi thành phố 1 bullet.
     Ảnh dashboard đặt ngay cuối bullet đó, không tách đoạn riêng.
   - `## Phân bổ` — bullet theo từng thành phố, nêu quận/khu vực nào chiếm bao nhiêu %,
     ưu tiên nêu phát hiện "đổi ngôi" (quận nhiều cung nhất ≠ quận rẻ nhất) nếu có.
     Nếu một phát hiện ở đây có vẻ mâu thuẫn hoặc khác với con số đã nêu ở mục khác
     trong bài, **chủ động thêm 1 blockquote đối chiếu** giải thích tại sao khác nhau
     — đừng để độc giả tự phát hiện mâu thuẫn.
   - Kết mỗi phân khúc bằng `[Ảnh: mô tả]` hoặc ảnh thật nếu đã có, cho phần phân bổ.

6. **`# Hướng dẫn sử dụng dashboard`** — thực dụng, đánh số bước (1/2/3), áp dụng được
   cho *bất kỳ* tổ hợp filter nào độc giả tự muốn tra, không chỉ ví dụ trong bài. Kèm
   1 ảnh minh họa case cụ thể (vd "kiếm nhà dưới 3 tỷ").

7. **`# Kết`**:
   - 1-2 câu túm tắt insight xuyên suốt cả bài (không liệt kê lại từng mục, chỉ chọn
     lát cắt mạnh nhất).
   - 1 câu hỏi tương tác với độc giả — ưu tiên **callback** lại câu hỏi/câu đùa từ bài
     trước trong series nếu có (tạo continuity, không phải câu hỏi mới toanh mỗi lần).
   - `> P/S:` hẹn bài tiếp theo trong series, giọng đùa nhẹ tự-trấn-an ("yên tâm",
     "tin tôi") — không hứa hẹn nghiêm trọng.

## Quy tắc số liệu (áp dụng toàn bài)

- Luôn kèm số tuyệt đối *và* %: `198/3.358 ≈ **5.9%**`. Không bao giờ chỉ đưa % trần
  trụi khi có số tuyệt đối trong tay.
- Bold con số/kết luận chính, không bold tràn lan cả câu.
- Dấu chấm phân cách hàng nghìn (`3.358` không phải `3,358`), dấu phẩy cho thập phân
  khi viết tắt kiểu Việt (`5,9%` hoặc `5.9%` đều được nhưng phải nhất quán trong cùng
  một bài — bài mẫu dùng dấu chấm thập phân kiểu số liệu quốc tế, giữ theo đó).
- Đơn vị viết tắt: `tỷ`, `tr/m²` (không viết đầy đủ "triệu/m²" trừ trong bảng/chú
  thích ảnh).
- Khi trích số liệu bài cũ: **trích nguyên văn** trong ngoặc kép + in nghiêng, không
  diễn giải lại — để độc giả tự đối chiếu văn phong cũ/mới.
- Mọi số liệu phải có câu diễn giải ý nghĩa đi kèm — không để một con số trôi nổi
  không giải thích "vậy thì sao".

## Cạm bẫy cần tránh (đã từng mắc trong lúc viết bài mẫu)

- **Đừng xếp hạng theo entity có quy mô lệch nhau** (dự án, chủ đầu tư) để suy ra kết
  luận thị trường — chủ đầu tư lớn nhất luôn chiếm top chỉ vì có nhiều dự án nhất, đó
  là artifact thống kê chứ không phải insight thật. Ưu tiên đơn vị địa lý (quận) khi
  muốn nói về phân bổ/tập trung.
- **Đừng dùng danh sách rút gọn của bài cũ làm chính xác tuyệt đối** — nếu bài cũ liệt
  kê "ví dụ: A, B, C" thì đó có thể không phải danh sách đầy đủ. Đọc kỹ nguyên văn bài
  cũ trước khi tính lại phần trăm đối chiếu (bài mẫu từng tính nhầm 4 quận thay vì 7
  quận thật sự được liệt kê trong bài P1 — luôn xác minh lại nguồn trước khi so sánh).
- **Đừng lẫn giọng kể chuyện dài dòng vào giữa bullet** — bản đầu tiên của bài mẫu có
  nhiều đoạn văn xuôi kiểu "tldr / vào việc." kể lể; qua các lần tác giả tự sửa, bài đã
  rút gọn gần hết văn xuôi, chỉ giữ bullet + số liệu + 1 câu insight. Mặc định viết
  theo hướng đã rút gọn này, không quay lại giọng kể chuyện trừ khi được yêu cầu rõ.
- Nếu chưa có ảnh dashboard thật cho một mục, luôn để placeholder `[Ảnh: mô tả]` thay
  vì bỏ trống hoàn toàn hoặc tự bịa số không kiểm chứng được.

## Việc KHÔNG thuộc phạm vi skill này

- Bài kỹ thuật (setup BigQuery/dbt/scraper) dùng giọng khác — tách biệt, không áp
  cấu trúc "phân khúc theo persona" này vào đó.
- Không tự ý đổi giọng sang `writer_personal`/`writer_serious` (skill bên ngoài repo)
  trừ khi được yêu cầu rõ — series này đã có giọng riêng ổn định, không cần mượn giọng
  khác nữa.
