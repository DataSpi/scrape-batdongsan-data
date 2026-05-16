# Overview

This project builds a repeatable real estate data pipeline for [batdongsan.com.vn](https://batdongsan.com.vn):

1. Scrape listings, projects, and location metadata.
2. Store raw and cleaned data in Supabase/PostgreSQL.
3. Model data for analytics (Malloy + dbt).
4. Explore and visualize for market insights (Looker Studio dashboard).

![Data Pipeline](figs/project-flow2.png)
![Dashboard Preview](figs/dashboard-preview.png)

```mermaid
subgraph B[Web Scraping Layer]
    B1[j_real_estate.py<br/>Listings crawler + tracking JSON merge]
    B2[j_projects.py<br/>Projects crawler]
    B3[j_metadata.py<br/>Cities, wards, streets, projects metadata APIs]
end

B --> C[(Supabase PostgreSQL<br/>re_bronze)]

C --> D[br2sil/j_real_estate.py<br/>Cleaning + normalization]
D --> E[(Supabase PostgreSQL<br/>re_silver.real_estate)]

E --> F[Malloy Semantic Model<br/>models/real_estate.malloy]
C --> F

C --> G[dbt Mart Model<br/>dbt/models/marts/fct_real_estate.sql]
E --> G

F --> H[Analytical Queries<br/>models/materialize.malloysql]
G --> H

H --> I[Looker Studio Dashboard]

J[APScheduler local jobs] -. schedules .-> B
K[Airflow DAG scaffold] -. orchestrates .-> B
K -. orchestrates .-> D
```

# Problems This Project Solves

- Turns unstructured marketplace pages into queryable tabular datasets.
- Reduces manual market scanning by centralizing listings and project context.
- Fixes key data quality issues for analysis (price/area parsing, type normalization, location hierarchy joins).
- Provides an analytics-ready semantic layer so business users can answer pricing and supply questions faster.

# Features Developed

- Asynchronous, batched scraper for listing pages with browser impersonation to improve request success rate.
- Listing extraction includes core fields plus `verify` flag from listing card HTML.
- Tracking metadata extraction from embedded `window.pageTrackingData` JSON and merge by `product_id`.
- Project crawler with project metadata extraction across paginated pages.
- Metadata ingestion for cities/wards/streets/projects via batdongsan API endpoints.
- Bronze -> Silver transformation pipeline:
    - Parse Vietnamese price text into numeric values.
    - Parse area into numeric square meters.
    - Normalize property type labels.
    - Recalculate price per m2.
    - Add scrape date and duplicate checks.
- SQLAlchemy-based DB utilities for write/upsert/query workflows.
- Semantic model in Malloy with joins across city/district/ward/street/project.
- dbt mart model (`fct_real_estate`) for integrated analytical view.
- Scheduling/orchestration:
    - Local APScheduler job runner.
    - Airflow DAG scaffold for periodic pipelines.

# Technologies Applied

- Language: Python.
- Scraping: `curl_cffi`, `BeautifulSoup4`, `asyncio`.
- Data processing: `pandas`, `numpy`.
- Storage & DB access: Supabase/PostgreSQL, `sqlalchemy`, `psycopg2`.
- Modeling: Malloy semantic layer, dbt SQL modeling.
- Orchestration: APScheduler, Apache Airflow.
- Analytics/visualization: Looker Studio, exploratory scripts with `matplotlib` and `seaborn`.

# Current Run Commands (Windows/Conda)

Install dependencies:

```bash
pip install -r requirements.txt
```

Run listing scraper:

```bash
python -m src.web2br.j_real_estate
```

Run project scraper:

```bash
python -m src.web2br.j_projects
```

Run metadata ingestion:

```bash
python -m src.web2br.j_metadata
```

Run bronze-to-silver transformation:

```bash
python -m src.br2sil.j_real_estate
```

# Notes

- Existing Airflow DAG task script paths reference legacy files that are not present in this repo snapshot.
- Sensitive credentials should be moved out of tracked config files into environment variables/secrets.




