-- Ports src/_br2sil/j_projects.py to SQL: full outer join of the legacy (v1) and
-- active (v2) project reference tables on projectId.

with p1 as (
    select * from {{ source('bronze', 'm_projects') }}
),

p2 as (
    select projectId, wardId from {{ source('bronze', 'm_projects_v2') }}
)

select
    projectId,
    p1.name,
    p1.districtId,
    p2.wardId as wardId_v2
from p1
full outer join p2 using (projectId)
