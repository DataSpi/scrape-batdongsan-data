# Overview

This project uses Python for scraping real estate listings from from [batdongsan.com.vn](https://batdongsan.com.vn). The flow of the project:

![Data Pipeline](readme_figs/project-flow2.png)

* Scraping data from batdongsan.com
* Storing on Supabase
* Visualizing & analysing on [Google Locker Studio](https://lookerstudio.google.com/reporting/9e21618f-97dc-4480-b101-cbda26b9b2a5)
    ![alt text](image.png)

# Quick Start

## 1. Set Up a Python Environment

It is recommended to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure Environment Variables

Create a `.env` file in the project root with your Supabase credentials and any other required settings. Example:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## 4. Run the Scraper

```bash
python main.py
```
