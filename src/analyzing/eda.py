from pathlib import Path
import os
script_dir = Path(__file__).resolve().parent
os.chdir(script_dir.parent)
import pandas as pd
from utils import dbConnector as db
from IPython.display import display




sb_conn = db.spyno_sb_conn()
df = db.fetch_to_dataframe(
    sb_conn, 
    """--sql
    SELECT re.*, rp.project_name, rret.real_estate_type  FROM real_estate.re_real_estate re
    LEFT JOIN real_estate.re_project rp 
    ON re.project_id = rp.id 
    LEFT JOIN real_estate.re_real_estate_type rret 
    ON rret.id  = re.re_type_id 
    """
)
df.groupby(['project_name', 'real_estate_type']).size().unstack(fill_value=0)

df['real_estate_type'].value_counts()
df['project_name'].nunique()

cc = df[df['real_estate_type'] == 'căn hộ chung cư'].copy()

cc['project_name'].value_counts()

# number of apartment bedrooms distribution per project
prj_bed = cc.groupby(['project_name', 'bedrooms']).size().unstack(fill_value=0)
heatmap = prj_bed.style.background_gradient(cmap="YlOrRd").format(precision=0)
display(heatmap)


prj_toilet = cc.groupby(['project_name', 'toilets']).size().unstack(fill_value=0)
heatmap = prj_toilet.style.background_gradient(cmap="YlOrRd").format(precision=0)
display(heatmap)
"""  
as expected, Phần lớn thuộc phân khúc 2-3 phòng ngủ và 2 toilet
"""
print((cc['bedrooms'].astype(str) + "-" + cc['toilets'].astype(str)).value_counts().sort_index())



""" 
interestingly, only penthouse apartments have more toilets than bedrooms. 
I guess rich people shit more than normal =)))
"""
a=cc.query("toilets > bedrooms")
a.to_clipboard(index=False)

cc.groupby('location').size().sort_values(ascending=False)



