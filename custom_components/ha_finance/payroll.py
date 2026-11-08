"""Federal RF five-day workweek estimates for a fully worked month."""
import calendar
import json
from datetime import date, timedelta
from pathlib import Path

CALENDAR=json.loads((Path(__file__).parent/'workdays.json').read_text())['years']
WORKDAYS={day for year in CALENDAR.values() for day in year}


def workdays_for_year(year, overrides=None):
    rule=(overrides or {}).get(str(year))
    if rule is None:
        return set(CALENDAR.get(str(year), []))
    days_off=set(rule['days_off'])
    working=set(rule['working_days'])
    current=date(year,1,1)
    while current.year == year:
        if current.weekday()<5 and current.isoformat() not in days_off:
            working.add(current.isoformat())
        current+=timedelta(days=1)
    return working


def calendar_confirmed(year, overrides=None):
    rule=(overrides or {}).get(str(year))
    return rule.get('confirmed',False) if rule else year<=2027


def export_calendar(year, overrides=None):
    if type(year) is not int or not 2024<=year<=2100:
        raise ValueError("Год должен быть от 2024 до 2100")
    if str(year) in (overrides or {}):
        return overrides[str(year)]
    working=workdays_for_year(year)
    days_off=[];weekend_workdays=[]
    current=date(year,1,1)
    while current.year == year:
        if current.isoformat() not in working:days_off.append(current.isoformat())
        elif current.weekday()>=5:weekend_workdays.append(current.isoformat())
        current+=timedelta(days=1)
    return {'year':year,'confirmed':calendar_confirmed(year),'days_off':days_off,'working_days':weekend_workdays}


def payment_date(year, month, day, overrides=None):
    result=date(year,month,min(day,calendar.monthrange(year,month)[1]))
    while result.isoformat() not in workdays_for_year(result.year,overrides):
        if str(result.year) not in CALENDAR:
            raise ValueError("Нет производственного календаря для даты выплаты")
        result-=timedelta(days=1)
    return result.isoformat()


def calculate(worker, year, month, overrides=None):
    if type(year) is not int or type(month) is not int or not 1<=month<=12 or not 2025<=year<=2100:
        raise ValueError("Доступен производственный календарь 2025–2100")
    if worker.get('employment') == 'fixed':
        paid_date=payment_date(year,month,worker['fixed_day'],overrides)
        return {'calendar_provisional':not (calendar_confirmed(year,overrides) and calendar_confirmed(int(paid_date[:4]),overrides)),'kind':'fixed', 'payment':worker['income'],
                'payment_date':paid_date}
    def split(y, m):
        days=[day for day in workdays_for_year(y,overrides) if day.startswith(f'{y}-{m:02d}-')]
        first=sum(int(day[-2:])<=15 for day in days)
        advance=(worker['income']*first*2+len(days))//(2*len(days))
        return len(days), first, advance
    previous_year,previous_month=(year-1,12) if month==1 else (year,month-1)
    count,first,advance=split(year,month)
    previous_count,previous_first,previous_advance=split(previous_year,previous_month)
    return {'calendar_provisional':not (calendar_confirmed(year,overrides) and calendar_confirmed(previous_year,overrides)),'workdays':count,'first_workdays':first,
            'second_workdays':previous_count-previous_first,
            'salary_workdays':previous_count,'salary_first_workdays':previous_first,
            'advance':advance,'salary':worker['income']-previous_advance,
            'advance_period':f'{year}-{month:02d}', 'salary_period':f'{previous_year}-{previous_month:02d}',
            'advance_date':payment_date(year,month,worker['advance_day'],overrides),
            'salary_date':payment_date(year,month,worker['salary_day'],overrides)}


def migrate_worker_days(data):
    """v0.2.0 called the first (salary) field advance_day; retain entered order."""
    if data.get('payroll_day_schema') == 2:
        return False
    for worker in data.get('workers', []):
        if worker.get('employment') != 'fixed':
            worker['salary_day'], worker['advance_day'] = worker['advance_day'], worker['salary_day']
    data['payroll_day_schema'] = 2
    return True


def budget_schedule(workers, year, month, overrides=None):
    result=[]
    for worker in workers:
        estimate=calculate(worker,year,month,overrides)
        if estimate.get('kind') == 'fixed':
            result.append({'id':f"{worker['id']}:fixed",'name':worker['name'], 'date':estimate['payment_date'],'amount':estimate['payment']})
        else:
            for kind, label in [('salary','Зарплата'),('advance','Аванс')]:
                result.append({'id':f"{worker['id']}:{kind}",'name':f"{worker['name']} · {label}",'date':estimate[f'{kind}_date'],'amount':estimate[kind]})
    return sorted(result,key=lambda payment:(payment['date'],payment['id']))
