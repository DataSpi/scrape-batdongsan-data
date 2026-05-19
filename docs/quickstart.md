# Quickstart

Tai lieu nay giup ban chay du an nhanh tren may local.

## 1) Prerequisites

- Python 3.10+ (khuyen nghi dung conda env rieng).
- Truy cap database Supabase/PostgreSQL.
- Tao file `.env` (hoac bien moi truong) voi cac bien toi thieu:
  - `DB_HOST`
  - `DB_PORT`
  - `DB_DB_NAME`
  - `DB_USER`
  - `DB_PASSWORD`

## 2) Cai dat

```bash
pip install -r requirements.txt
```

Neu ban dung conda:

```bash
conda create -n bds_scraper python=3.10 -y
conda activate bds_scraper
pip install -r requirements.txt
```

## 3) Chay pipeline co ban

### 3.1 Scrape listings

```bash
python -m src.web2br.j_real_estate
```

### 3.2 Scrape projects

```bash
python -m src.web2br.j_projects
```

### 3.3 Lay metadata

```bash
python -m src.web2br.j_metadata
```

### 3.4 Bronze -> Silver

```bash
python -m src.br2sil.j_real_estate
```

## 4) Tao report

```bash
python src/reports/generate_report.py
```

Output report duoc luu trong thu muc `reports/output/`.

## 5) Kiem tra nhanh

- Co du lieu trong schema Bronze/Silver tren database.
- Co file HTML report moi trong `reports/output/`.
- Doc report mau: [malloy_result.html](../reports/output/malloy_result.html)

## 6) Troubleshooting

- Loi ket noi DB: kiem tra lai `.env` va quyen truy cap Supabase.
- Loi package: chay lai `pip install -r requirements.txt` trong dung environment.
- Khong co listing: website nguon co the doi structure, can cap nhat scraper selectors.

## Dieu huong

- Ve [Trang chu du an](../readme.md)
- Ve [Docs Hub](README.md)
- Sang [Technical Guides](technical-guides.md)
