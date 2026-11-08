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
    if type(year) is not int or type(month) is not int or not 1<=month<=12 or not 2025<=year<=2100:
        raise ValueError("Доступен производственный календарь 2025–2100")
    if worker.get('employment') == 'fixed':
        return {'calendar_provisional':year>2027,'kind':'fixed', 'payment':worker['income'],
                'payment_date':payment_date(year,month,worker['fixed_day'])}
    def split(y, m):
        days=[day for day in CALENDAR[str(y)] if day.startswith(f'{y}-{m:02d}-')]
        first=sum(int(day[-2:])<=15 for day in days)
        advance=(worker['income']*first*2+len(days))//(2*len(days))
        return len(days), first, advance
    previous_year,previous_month=(year-1,12) if month==1 else (year,month-1)
    count,first,advance=split(year,month)
    previous_count,previous_first,previous_advance=split(previous_year,previous_month)
    return {'calendar_provisional':year>2027,'workdays':count,'first_workdays':first,
            'second_workdays':previous_count-previous_first,
            'salary_workdays':previous_count,'salary_first_workdays':previous_first,
            'advance':advance,'salary':worker['income']-previous_advance,
            'advance_period':f'{year}-{month:02d}', 'salary_period':f'{previous_year}-{previous_month:02d}',
            'advance_date':payment_date(year,month,worker['advance_day']),
            'salary_date':payment_date(year,month,worker['salary_day'])}


def migrate_worker_days(data):
    """v0.2.0 called the first (salary) field advance_day; retain entered order."""
    if data.get('payroll_day_schema') == 2:
        return False
    for worker in data.get('workers', []):
        if worker.get('employment') != 'fixed':
            worker['salary_day'], worker['advance_day'] = worker['advance_day'], worker['salary_day']
    data['payroll_day_schema'] = 2
    return True


def budget_schedule(workers, year, month):
    result=[]
    for worker in workers:
        estimate=calculate(worker,year,month)
        if estimate.get('kind') == 'fixed':
            result.append({'id':f"{worker['id']}:fixed",'name':worker['name'], 'date':estimate['payment_date'],'amount':estimate['payment']})
        else:
            for kind, label in [('salary','Зарплата'),('advance','Аванс')]:
                result.append({'id':f"{worker['id']}:{kind}",'name':f"{worker['name']} · {label}",'date':estimate[f'{kind}_date'],'amount':estimate[kind]})
    return sorted(result,key=lambda payment:(payment['date'],payment['id']))
