# Overview
This project uses Python for scraping real estate listings from from [batdongsan.com.vn](https://batdongsan.com.vn). The flow of the project:

![Data Pipeline](figs/project-flow2.png)

* Scraping data from batdongsan.com
* Storing on Supabase
* Visualizing & analysing on [Google Locker Studio](https://lookerstudio.google.com/reporting/9e21618f-97dc-4480-b101-cbda26b9b2a5)
    ![alt text](figs/dashboard-preview.png)

Tech stack:
- Database: PostgreSQL, DuckDB
- Semantic model: Malloy
- Programming language: Python

# Coding instructions
## Malloy Modeling Rules
- **No Redundant Dimensions:** Do NOT redefine a dimension if it has the same name as the underlying table column (e.g., avoid `dimension: field_name is field_name`).
- **Implicit Dimensions:** All columns from the source table are automatically available as dimensions. Only define a `dimension` block when:
    1. The name in the database is not clear for the user like `bought_ccy` and  `sold_ccy`: 
      - Change to `bought_currency` and `sold_currency` 
    2. Creating calculated fields. Prioritize clear name for user because this is analysis for business users. 
- **Joining**: Identify the id columns in the source table and join it with the dimension source to get the descriptive infor. If lacking context, and can not idenify the dimension source, note it as a comment in the code and the chat response and ask for clarification.
- `query:` can be used for create calculated tables just like CTE in SQL. 

## Joins Syntax
join_one: source name [is source] on boolean expression
join_one: source name [is source] with foreign key expression
join_many: source name [is source] on boolean expression
join_cross: source name [is source] [on boolean expression]

## Malloy Documentation
- `count(distinct expression)` deprecated, use `count(expression)` instead.
- to see a selection of a table we can use `run:` or `query:` block. For example:
    ```malloy
    run: source -> {
        select:
            col1, col2
        where:
            col3 > 100
    }
    ```
# Naming convention in database 
## Tables Name

