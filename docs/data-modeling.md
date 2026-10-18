# Data Modeling & Architecture

Tài liệu ngắn để dùng làm script thuyết trình về cách domain bất động sản được model qua 3
layer BigQuery (`re_bronze` → `re_silver` → `re_gold`). Chi tiết vận hành xem
[technical-guides.md](technical-guides.md); tài liệu này chỉ nói về **shape của model**, không
nói về orchestration.

## 1. Silver — star schema (logical model)

`re_silver` là nơi domain thực tế được model lại: `Listing` là fact, `Project` và `Location`
là dimension xoay quanh.

```mermaid
erDiagram
    fct_real_estate }o--|| dim_project : "projectId"
    fct_real_estate_rent }o--|| dim_project : "projectId"
    fct_real_estate }o--o| dim_location_v1 : "districtId (direct, ưu tiên)"
    fct_real_estate_rent }o--o| dim_location_v1 : "districtId (direct, ưu tiên)"
    dim_project }o--|| dim_location_v1 : "districtId (fallback khi listing thiếu)"
    dim_project }o--|| dim_location_v2 : "wardId (active, chưa wired vào gold)"
    fct_real_estate }o--|| dim_real_estate_type_mapping : "matched_token → real_estate_type"
    fct_real_estate_rent }o--|| dim_real_estate_type_mapping : "matched_token → real_estate_type"

    fct_real_estate {
        string product_id PK
        string projectId FK
        int districtId FK
        float price_num
        float price_1m2
    }
    fct_real_estate_rent {
        string product_id PK
        string projectId FK
        int districtId FK
        float price_per_month
    }
    dim_project {
        string projectId PK
        string name
        string districtId FK
    }
    dim_location_v1 {
        string districtId PK
        string name_district
        string name_city
    }
    dim_location_v2 {
        string wardId PK
        string name_ward
        string name_city
    }
    dim_real_estate_type_mapping {
        string raw_token PK
        string real_estate_type
    }
```

**Điểm nói khi thuyết trình:**
- 2 fact riêng (`fct_real_estate` bán, `fct_real_estate_rent` thuê) — giá thuê là giá/tháng,
  không cùng thang với giá bán nên không gộp chung 1 fact.
- `Location` có **2 version tường minh** (v1 = địa giới cũ, v2 = sau sáp nhập hành chính) thay
  vì SCD tổng quát (`valid_from`/`valid_to`) — vì biết trước domain chỉ đổi đúng 1 lần, build
  engine SCD generic là over-engineering.
- Chi tiết thực tế hay: listing **join thẳng** vào `Location` bằng `districtId` của chính nó
  (ưu tiên), chỉ fallback qua `Project` (`projectId` → `Project.districtId`) khi `districtId`
  trên listing là `0`/null. FK trực tiếp đáng tin được là nhờ một fix ở tầng scrape: site trả
  `districtId=0` (sentinel "chưa resolve địa giới cũ") cho **mọi** listing — kể cả nhà đất
  không có `projectId` — nếu crawl bằng URL cấp thành phố; crawl riêng từng quận
  (`src/scrapers/real_estate.py:crawl_city_by_district`) mới ép site trả `districtId`/`wardId`
  thật. Trước fix đó, FK trực tiếp trên listing đúng là thiếu dữ liệu hơn FK qua project — giờ
  thì ngược lại.
- `real_estate_type` cũng đi qua 1 dimension lookup nhỏ — `dim_real_estate_type_mapping` (seed,
  không phải bảng scrape) — resolve từ token match trong URL slug, dùng chung cho cả 2 fact.
  Không persist `raw_token`/FK trong `fct_*` (chỉ giữ `real_estate_type` đã resolve), nên đây là
  lookup áp dụng lúc build silver, không phải quan hệ để downstream tự join.

## 2. Gold — One Big Table (physical/serving model)

`re_gold` **không model lại domain** — nó chỉ pre-join star schema ở silver thành 1 bảng phẳng
cho đúng nhu cầu của BI tool đang dùng.

```mermaid
flowchart LR
    subgraph Silver["re_silver — star schema"]
        F[fct_real_estate]
        P[dim_project]
        L1["dim_location_v1<br/>(legacy district)"]
        L2["dim_location_v2<br/>(active ward)"]
    end

    subgraph Gold["re_gold — OBT"]
        M[mart_real_estate<br/>1 row / listing, đã denormalize]
    end

    F -->|projectId| M
    F -->|"districtId (ưu tiên)"| M
    P -->|"districtId (fallback)"| M
    L1 -->|district_name, city_name, lat/lng| M
    L2 -.chưa wired.-> M
```

**Vì sao OBT, không phải star tiếp ở gold:** Looker Studio (free tier) join kém — nếu đưa
fact + dimension riêng vào BI, vẫn phải tự join ở đó, chỉ đổi *nơi* join, không giảm việc join.
Nên pre-join sẵn trong dbt (có test), gold chỉ là **physicalize lại model đã có ở silver**,
không phải model mới.

## 3. Trade-off của OBT ở serving layer

| | Star (silver) | OBT (gold) |
|---|---|---|
| Update 1 attribute (VD: đổi tên project) | Update 1 row dimension | Rebuild lại mart |
| Reuse dimension cho fact mới | `dim_location` dùng lại được ngay | Phải build OBT riêng, lặp lại join logic |

Chấp nhận được ở scale hiện tại (data nhỏ, pipeline chạy weekly) — nhưng là cost thực sự, không
phải free lunch.

## 4. Khi nào cần revisit

Quay lại re-project silver thành star schema thật ở gold (thay vì tiếp tục mở rộng OBT) khi:
volume tăng mạnh, có thêm BI tool/consumer khác ngoài Looker Studio, thêm fact mới
(`price_history`, ...), `Location` đổi version lần 3, hoặc cần phân tích lịch sử thay vì
current-state.
