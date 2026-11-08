"""Federal RF five-day workweek estimates for a fully worked month."""
import calendar
import json
from datetime import date, timedelta
from pathlib import Path

CALENDAR=json.loads((Path(__file__).parent/'workdays.json').read_text())['years']
WORKDAYS={day for year in CALENDAR.values() for day in year}


def payment_date(year, month, day):
    result=date(year,month,min(day,calendar.monthrange(year,month)[1]))
    while result.isoformat() not in WORKDAYS:
        if str(result.year) not in CALENDAR:
            raise ValueError("Нет производственного календаря для даты выплаты")
        result-=timedelta(days=1)
    return result.isoformat()


def calculate(worker, year, month):
    if type(year) is not int or type(month) is not int or not 1<=month<=12 or not 2025<=year<=2027:
        raise ValueError("Доступен производственный календарь 2025–2027")
    days=[day for day in CALENDAR[str(year)] if day.startswith(f'{year}-{month:02d}-')]
    first=sum(int(day[-2:])<=15 for day in days)
    # Round half up in integer kopecks; the remainder goes to the final payment.
    advance=(worker['income']*first*2+len(days))//(2*len(days))
    next_year,next_month=(year+1,1) if month==12 else (year,month+1)
    final_date=payment_date(next_year,next_month,worker['salary_day'])
    return {'workdays':len(days),'first_workdays':first,'second_workdays':len(days)-first,
            'advance':advance,'salary':worker['income']-advance,
            'advance_date':payment_date(year,month,worker['advance_day']), 'salary_date':final_date}
