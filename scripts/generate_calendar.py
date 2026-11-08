"""Regenerate bundled federal five-day calendars: pip install holidays==0.108."""
import json
from datetime import date,timedelta
from pathlib import Path
import holidays
result={"source":"python-holidays 0.108, Russia, federal five-day workweek", "years":{}}
for year in range(2024,2028):
    calendar=holidays.RU(years=year)
    day=date(year,1,1)
    working=[]
    while day.year==year:
        if calendar.is_working_day(day):working.append(day.isoformat())
        day+=timedelta(days=1)
    result["years"][str(year)]=working
Path('custom_components/ha_finance/workdays.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
