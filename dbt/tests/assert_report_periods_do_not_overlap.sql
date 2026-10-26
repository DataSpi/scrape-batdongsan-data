-- Fails if two report windows overlap: a bronze row would land in both periods.
select a.period, b.period as overlaps_with
from {{ ref('dim_report_period') }} a
inner join {{ ref('dim_report_period') }} b
    on a.period < b.period
    and a.start_date <= b.end_date
    and a.end_date >= b.start_date
