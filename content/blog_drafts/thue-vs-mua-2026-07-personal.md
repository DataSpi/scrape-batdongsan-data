Đây là bài tiếp theo trong chuỗi bài phân tích giá bds của DataSpy:  
- Đi xem chung cư cùng thợ số - P1 (Tháng 9/2025)
- Đi xem chung cư cùng thợ số - P2 (Tháng 7/2026)

Hai bài viết trước đã đăng trong chuỗi đã tập trung vào phân tích giá bán căn hộ chung cư, bài viết này sẽ đi sâu vào trả lời một câu hỏi có lẽ rất nhiều người quan tâm: Với giá nhà hiện tại thì nên thuê hay nên mua. 


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

# Khung lý thuyết: vì sao "nên mua nhà" chưa bao giờ là một kết luận kinh tế thuần túy

Ngày 1 tháng 7 năm 1947, William Levitt, khi đó 40 tuổi, động thổ ngôi nhà đầu tiên trên 1.000 mẫu đất khoai tây cũ ở Long Island, cách Manhattan 25 dặm về phía đông. Ông sẽ xây 17.000 căn giống hệt nhau trong vài năm sau đó — khu dân cư sẽ mang tên "Levittown", nguyên mẫu cho toàn bộ mô hình ngoại ô Mỹ hậu chiến[1]. Nhưng câu nói khiến Levitt được nhớ tới không phải là một câu về kỹ thuật xây dựng hàng loạt. Năm 1948, ông tuyên bố: *"Không người đàn ông nào sở hữu nhà và đất của chính mình có thể là một người Cộng sản. Anh ta có quá nhiều việc phải làm."*[2]

Đọc lại câu này 78 năm sau, ở một đất nước chưa từng có Levittown, điều đáng chú ý không phải tính hài của nó, mà là việc nó lộ ra một sự thật ít ai để ý: "nên mua nhà" chưa bao giờ chỉ là một kết luận rút ra từ bài toán tài chính. Nó là một chính sách — vay thế chấp được chính phủ Mỹ bảo lãnh qua FHA/VA, bán cho một xã hội đang cần một câu trả lời ý thức hệ cho Chiến tranh Lạnh, rồi mới được đóng gói lại thành "lẽ thường" hai thế hệ sau. Câu hỏi đặt ra cho phần này: nếu tước bỏ lớp vỏ ý thức hệ đó, phần lõi kinh tế còn lại thực sự nói gì — và các thành phố khác nhau trên thế giới, với các lựa chọn chính sách khác nhau, đã kiểm định giả thuyết "mua tốt hơn thuê" theo cách nào?

## Framework: từ P/R ratio tới "user cost of capital"

Phần trên đã dùng P/R ratio — chỉ số kinh điển, dễ tính, dễ hiểu. Nhưng giới kinh tế học đô thị coi đây là một phép xấp xỉ thô, vì nó bỏ qua thời điểm: hai thị trường có cùng P/R ratio vẫn có thể có "giá trị hợp lý" rất khác nhau, tùy vào lãi suất thực dài hạn đang ở đâu trong chu kỳ và kỳ vọng tăng giá nhà dài hạn của từng thị trường cụ thể.

Framework đầy đủ hơn — gọi là **user cost of capital**, do James Poterba đề xuất năm 1984[3] và được Himmelberg, Mayer & Sinai hệ thống hóa lại năm 2005[4] — tính "chi phí quy đổi hàng năm của việc sở hữu nhà" bằng:

> lãi suất thế chấp + thuế bất động sản + chi phí bảo trì/khấu hao − ưu đãi thuế − kỳ vọng tăng giá thực + phần bù rủi ro (cho tính kém thanh khoản và biến động của một tài sản không đa dạng hóa được)

So với P/R ratio, framework này trả lời được câu hỏi P/R ratio không trả lời nổi: tại sao cùng một tỷ lệ giá/thuê, có thị trường vẫn "hợp lý" trong khi thị trường khác đã là bong bóng. Himmelberg và cộng sự dùng chính công thức này để lập luận rằng phần lớn các thị trường Mỹ bị coi là "bong bóng" đầu những năm 2000 thực ra không bất hợp lý đến vậy, một khi tính đúng lãi suất thực đang ở mức thấp lịch sử. IMF và OECD hiện dùng logic họ hàng với công thức này để theo dõi định kỳ tỷ lệ giá/thuê và giá/thu nhập ở các nước thành viên, gắn cờ "định giá cao" khi tỷ lệ vượt trung bình lịch sử dài hạn của chính thị trường đó[5] — nghĩa là ngay cả các định chế quốc tế cũng không dùng một ngưỡng tuyệt đối kiểu "15/20" cho mọi nơi, mà so mỗi thị trường với chính lịch sử của nó.

Có một lớp lập luận thứ hai, thuộc về tâm lý học hành vi hơn là tài chính thuần túy: mua nhà trả góp hoạt động như một cơ chế "tiết kiệm cưỡng bức" — trả nợ gốc hàng tháng là một hình thức tiết kiệm có kỷ luật mà rất ít người tự giác làm nếu chỉ đi thuê và "định sẽ để dành phần chênh lệch". Lập luận phản biện chuẩn: nó bỏ qua chi phí cơ hội của khoản trả trước và phần chênh lệch đó, nếu đem đầu tư vào một danh mục đa dạng hóa thay vì dồn hết vào một bất động sản duy nhất[6]. Đây chính xác là cách công cụ tính thuê-vs-mua của New York Times mô phỏng: kịch bản đối chứng của "mua" không phải là "thuê rồi tiêu hết phần chênh lệch", mà là "thuê, rồi đầu tư đúng phần chênh lệch đó"[7] — càng làm rõ: câu hỏi thuê hay mua, xét đến cùng, luôn là một câu hỏi về việc bạn có kỷ luật tài chính đủ để tận dụng phần vốn không bị chôn vào nhà hay không, chứ không đơn thuần là thuê "mất tiền" còn mua "giữ được tiền".

## Case study: 6 thành phố, 6 câu trả lời khác nhau cho cùng một bài toán

Nếu "mua nhà" là một kết luận kinh tế phổ quát, tỷ lệ sở hữu nhà phải hội tụ về một mức tương tự ở các nước giàu có hạ tầng tài chính tương đương. Thực tế lại cho một bức tranh phân tán đến bất ngờ — chính sự phân tán này mới là dữ liệu thú vị, vì nó cho thấy tỷ lệ sở hữu nhà là sản phẩm của chính sách và luật lệ, không phải một hằng số kinh tế.

- **Thụy Sĩ** — tỷ lệ sở hữu nhà thấp nhất châu Âu, chỉ khoảng **42%**[8], dù là một trong những nước giàu nhất thế giới. Cơ chế: chủ nhà bị đánh thuế trên "giá trị cho thuê quy đổi" (imputed rental value) của chính căn nhà họ đang ở, luật bảo vệ người thuê buộc chủ nhà phải chứng minh lý do tăng giá thuê, và ngân hàng áp quy tắc trả trước rất chặt. Giàu không đồng nghĩa với thích mua nhà — khi chính sách thuế và luật thuê chống lại việc mua, người ta thuê.
- **Đức, đặc biệt Berlin** — tỷ lệ sở hữu quốc gia quanh 42-48%[9], riêng Berlin khoảng **83%** hộ gia đình đi thuê. Cơ chế tương tự Thụy Sĩ: luật bảo vệ người thuê mạnh, nguồn cung nhà thuê dồi dào trong lịch sử, và một chuẩn văn hóa coi thuê nhà dài hạn là bình thường, không phải một trạm dừng tạm thời trước khi "lên đời".
- **Tokyo** — tỷ lệ sở hữu thấp nhất trong các tỉnh của Nhật, khoảng **44,6%**[10]. Khác biệt cơ bản với phương Tây: nhà ở Nhật khấu hao gần về 0 sau 20-30 năm dù đất vẫn còn giá trị — nghĩa là động lực "mua để giữ tài sản" yếu hơn hẳn, vì căn nhà tự nó không phải là kho lưu trữ giá trị dài hạn.
- **Hồng Kông và Singapore** — hai thái cực đối lập nhau dù cùng chịu ràng buộc khan hiếm đất khắc nghiệt như nhau. Hồng Kông duy trì thị trường tư nhân đắt đỏ, tỷ lệ sở hữu quanh **50%**[11]. Singapore đi ngược lại hoàn toàn: nhà nước xây và bán căn hộ HDB thấp hơn giá thị trường 20-30%, cho phép dùng quỹ hưu trí bắt buộc (CPF) để trả góp — kết quả khoảng **90%** cư dân HDB sở hữu nhà[12]. Đây là phản chứng rõ nhất trong cả bộ: tỷ lệ sở hữu nhà ở Singapore không phải kết quả tự nhiên của thị trường, mà là một con số được nhà nước *thiết kế* ra bằng chính sách.
- **New York City và London** — cả hai đều cho thấy xu hướng giảm sở hữu nhà ở đô thị lõi giàu có: NYC chỉ **32,7%**[13], London giảm từ đỉnh 57,2% năm 1991 xuống còn **46,7%** năm 2021[14], khu vực thuê tư nhân tăng hơn gấp đôi trong hai thập kỷ — hiện tượng báo chí Anh gọi là "Generation Rent".

Đặt cạnh nhau, sáu trường hợp này kiểm định cùng một giả thuyết ngầm định trong tâm lý "phải mua nhà" — rằng người ta mua nhà vì mua nhà *tốt hơn về kinh tế* — và giả thuyết đó không đứng vững. Thụy Sĩ giàu nhưng thuê. Singapore không giàu hơn Hồng Kông bao nhiêu, nhưng gần như toàn dân sở hữu nhà, vì nhà nước quyết định vậy. Cơ chế thực sự quyết định một xã hội nghiêng về thuê hay mua không phải là "kinh tế học thuần túy", mà là ba đòn bẩy chính sách cụ thể: cách đánh thuế nhà ở, mức độ bảo vệ người thuê, và cấu trúc thị trường vay thế chấp. Đây là lằn ranh cần tách rõ: phê phán kiểu "người Việt bị ám ảnh mua nhà là vì tư duy lạc hậu" là một phán xét đạo đức, gần như vô hại vì không chỉ ra được đòn bẩy nào để can thiệp. Phê phán đúng chỗ phải hỏi: Việt Nam hiện có luật bảo vệ người thuê dài hạn nào đáng kể không? Có đánh thuế bất động sản hàng năm để san bằng phần nào lợi thế "giữ giá" của việc sở hữu không? Câu trả lời cho cả hai, ở thời điểm bài viết này, gần như là không — và đó mới là cơ chế thực sự đẩy tâm lý thị trường Việt Nam nghiêng hẳn về phía mua, bất kể bài toán thuần túy P/R ratio nói gì.

## Kết quả tài chính cho chủ sở hữu: nhà có thực sự là một khoản đầu tư tốt?

Trước khi trả lời, cần một sự thật ít được nhắc tới: theo Robert Shiller, người tạo ra chỉ số Case-Shiller, giá nhà thực (đã trừ lạm phát) ở Mỹ gần như đi ngang suốt 100 năm trước khi cơn sốt giá bắt đầu vào cuối thập niên 1990[15] — phần lớn vì năng suất xây dựng tăng đủ nhanh để bù lại chi phí đất và nhân công tăng. Nhà, xét trên chu kỳ dài, không mặc định là một tài sản tăng giá.

Nghiên cứu quy mô lớn nhất trả lời câu hỏi này là của Jordà, Knoll, Kuvshinov, Schularick và Taylor, công bố trên Quarterly Journal of Economics năm 2019, tổng hợp lợi suất thực của nhà ở, cổ phiếu, trái phiếu tại 16 nền kinh tế phát triển từ năm 1870 đến 2015[16]. Kết quả gây ngạc nhiên: lợi suất thực trung bình của nhà ở (chưa vay đòn bẩy) gần bằng lợi suất thực của cổ phiếu — khoảng **7%/năm** cho cả hai — nhưng độ biến động của nhà ở chỉ bằng **một nửa** cổ phiếu. Đây gần như là một nghịch lý với lý thuyết rủi ro-lợi nhuận chuẩn, một phần vì nhà không bị định giá lại hàng ngày như cổ phiếu trên sàn, phần khác vì tính kém thanh khoản khiến biến động đo được bị làm mượt đi.

Nhưng có hai điều khoản phải đọc kèm con số 7% đó, nếu không sẽ hiểu sai hoàn toàn ý nghĩa của nó:

- **Đó là lợi suất chưa vay đòn bẩy.** Người mua nhà thực tế hầu như luôn vay thế chấp — trả trước 20%, vay 80% — nghĩa là một biến động giá nhà được khuếch đại gần 5 lần trên phần vốn tự có thực sự bỏ ra. Điều này khuếch đại cả hai chiều: lời nhiều hơn khi thị trường lên, nhưng cũng có thể mất trắng vốn tự có (âm vốn chủ sở hữu) khi thị trường xuống — đây chính là cơ chế đứng sau khủng hoảng 2008.
- **Con số 7% là trung bình 145 năm, không phải cam kết cho từng thị trường/thời điểm cụ thể.** Ngay ở Mỹ hiện tại, các phân tích 2024-2025 (Bank of America, các công cụ tính thuê-vs-mua của báo chí tài chính) cho thấy thuê đang rẻ hơn mua ở **82/97 đô thị lớn** khi so sánh dòng tiền hàng tháng ở mức lãi suất thế chấp hiện hành[17] — tức là ngay cả một thị trường có lợi suất dài hạn tốt như Mỹ, tại một thời điểm cụ thể, phép tính vẫn có thể nghiêng hẳn về phía thuê.

Nói cách khác: nhà ở, không vay nợ, trong lịch sử là một tài sản tốt gần ngang cổ phiếu. Nhưng "mua nhà bằng vay thế chấp, tại đúng thời điểm này, tại đúng thị trường này" là một câu hỏi hoàn toàn khác — và không có câu trả lời phổ quát nào đúng ở mọi nơi, mọi lúc.

## Tự phản tư: framework này cũng có điểm mù

Nói thẳng luôn: gần như toàn bộ nghiên cứu học thuật trích dẫn ở trên — Poterba, Himmelberg-Mayer-Sinai, Jordà và cộng sự — đến từ dữ liệu Mỹ/châu Âu, nơi có thị trường vay thế chấp thanh khoản, thuế bất động sản hàng năm, và một hệ thống dữ liệu giá nhà minh bạch kéo dài cả thế kỷ. Việt Nam không có thuế bất động sản hàng năm đáng kể, không có luật bảo vệ người thuê dài hạn tương đương Đức/Thụy Sĩ, và chưa có bộ dữ liệu giá nhà đủ dài để biết liệu giá chung cư Việt Nam có đi ngang trong dài hạn như Mỹ trước 1990, hay sẽ tiếp tục tăng vì đang ở giai đoạn đô thị hóa khác hẳn. Toàn bộ sáu case study ở trên nên được đọc như bằng chứng cho một *cơ chế tổng quát* — chính sách và luật lệ định hình hành vi thuê/mua nhiều hơn bản năng kinh tế cá nhân — chứ không phải như một dự báo trực tiếp cho việc P/R ratio 29,6 năm ở TP.HCM "nên" hội tụ về đâu.

## Kết đoạn

Quay lại Levitt. Người đàn ông biến "sở hữu nhà" thành một bài kiểm tra lòng trung thành ý thức hệ cho cả một thế hệ người Mỹ, cuối đời phải bán sạch tài sản để trả nợ, chết gần như trắng tay năm 1994[18]. Mười ba năm sau, công ty còn mang tên ông — Levitt & Sons, khi đó đã qua tay chủ khác — nộp đơn phá sản giữa cơn sụp đổ nhà đất tồi tệ nhất lịch sử hiện đại nước Mỹ[19]. Ý thức hệ "mua nhà = trưởng thành, = yêu nước, = an toàn" sống lâu hơn cả người tạo ra nó lẫn công ty mang tên ông.

Vậy khi một người ở TP.HCM hay Hà Nội năm 2026 nói "phải cố mua bằng được một căn hộ", họ đang trả lời một bài toán tài chính, hay đang trả một khoản nợ tâm lý cho một câu chuyện được kể từ rất lâu, ở một nơi rất xa, vì những lý do chẳng liên quan gì đến P/R ratio của chính họ? Và nếu đúng là vế sau, thì câu hỏi tiếp theo đáng ra phải là gì — không phải "tôi có nên mua nhà không", mà là "câu chuyện nào đang khiến tôi tin rằng tôi phải mua"?

./.

**Tài liệu tham khảo**

[1] Time Magazine. "Suburban Legend: William Levitt." *Time*, 1997 (archive). https://time.com/archive/6598189/suburban-legend-william-levitt/
[2] Levitt, William J. Phát biểu năm 1948, trích trong nhiều nguồn sử liệu về Levittown, bao gồm Kenneth T. Jackson, *Crabgrass Frontier: The Suburbanization of the United States* (Oxford University Press, 1985).
[3] Poterba, James M. "Tax Subsidies to Owner-Occupied Housing: An Asset-Market Approach." *Quarterly Journal of Economics* 99, no. 4 (1984): 729-752.
[4] Himmelberg, Charles, Christopher Mayer, and Todd Sinai. "Assessing High House Prices: Bubbles, Fundamentals and Misperceptions." *Journal of Economic Perspectives* 19, no. 4 (2005): 67-92. NBER Working Paper No. 11643. https://www.nber.org/papers/w11643
[5] IMF Global Housing Watch. https://www.imf.org/external/research/housing ; OECD Affordable Housing Database. https://www.oecd.org/en/data/datasets/oecd-affordable-housing-database.html
[6] AFCPE. "Is Buying a House a Good Investment? Not Compared to Buying Stocks — But That Doesn't Mean You Shouldn't Do It." https://www.afcpe.org/news-and-publications/the-standard/2017-2/is-buying-a-house-a-good-investment-not-compared-to-buying-stocks-but-that-doesnt-mean-you-shouldnt-do-it/
[7] New York Times. "Is It Better to Rent or Buy?" (công cụ và phương pháp tính rent-vs-buy).
[8] The Local Switzerland. "Content to Rent: Why Do So Few People in Switzerland Own Their Home?" https://www.thelocal.ch/20210804/content-to-rent-why-do-so-few-people-in-switzerland-own-their-home ; Visual Capitalist, "Mapped: Europe's Homeownership Divide." https://www.visualcapitalist.com/mapped-europes-homeownership-divide/
[9] Brookings Institution. "Germany's Rental Housing Markets." https://www.brookings.edu/essay/Germany-rental-housing-markets
[10] Demographia. "Japan Metropolitan Housing." https://demographia.com/db-japanmethousing.htm ; Brookings Institution, "Japan's Rental Housing Markets." https://www.brookings.edu/articles/japan-rental-housing-markets
[11] Hong Kong Government Information Services, 9/7/2025. https://www.info.gov.hk/gia/general/202507/09/P2025070900439.htm
[12] SDG16.plus. "Singapore's Housing Development Board Provides Housing to 80 Percent of Residents." https://www.sdg16.plus/policies/singapores-housing-development-board-provides-housing-to-80-percent-of-residents/
[13] NYU Furman Center. "State of Homeowners and Their Homes 2025." https://www.furmancenter.org/soc-report/state-of-the-city-2025/state-of-homeowners-and-their-homes-2025/
[14] Trust for London. "Housing Tenure Over Time." https://trustforlondon.org.uk/data/housing-tenure-over-time/
[15] Shiller, Robert J. *Irrational Exuberance*. Princeton University Press, 2000 (các bản tái bản sau có cập nhật chỉ số Case-Shiller).
[16] Jordà, Òscar, Katharina Knoll, Dmitry Kuvshinov, Moritz Schularick, and Alan M. Taylor. "The Rate of Return on Everything, 1870-2015." *Quarterly Journal of Economics* 134, no. 3 (2019): 1225-1298. NBER Working Paper No. 24112. https://www.nber.org/papers/w24112
[17] Benzinga, dẫn phân tích Bank of America, 2024/2025. https://www.benzinga.com/economics/macro-economic-events/24/12/42558766/mortgage-applications-dip-as-rates-climb-it-is-still-cheaper-to-rent-than-purchase-for-82-out-of-97-major-cities
[18] The Real Deal. "William Levitt: The King of Suburbia." https://therealdeal.com/magazine/new-york-may-2008/william-levitt-the-king-of-suburbia/
[19] Wikipedia. "Levitt & Sons." https://en.wikipedia.org/wiki/Levitt_%26_Sons

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
