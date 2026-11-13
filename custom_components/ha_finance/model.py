"""Pure finance rules. All amounts are integer kopecks, never floats."""
from datetime import date
import re
from uuid import uuid4


def amount(value):
    if type(value) is not int or not 0 <= value <= 10**14:
        raise ValueError("Сумма должна быть целым числом копеек от 0 до 10¹⁴")
    return value


def label(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 150:
        raise ValueError("Укажите название до 150 символов")
    return value.strip()


def totals(deposit):
    income = sum(e["amount"] for e in deposit["expenses"] if e.get("kind") == "income" and e["paid"])
    principal = deposit["principal"] + income
    actual = sum(e["amount"] for e in deposit["expenses"] if e.get("kind", "expense") == "expense" and e["paid"])
    expected = sum(e["amount"] for e in deposit["expenses"] if e.get("kind", "expense") == "expense" and not e["paid"])
    return {"principal": principal, "actual": actual, "expected": expected,
            "balance": principal - actual, "available": principal - actual - expected}


def apply(data, action, payload):
    if action == "calendar_import":
        calendar_data = payload["calendar"]
        if not isinstance(calendar_data, dict):
            raise ValueError("Календарь должен быть объектом JSON")
        year = calendar_data.get("year")
        if type(year) is not int or not 2024 <= year <= 2100:
            raise ValueError("Год должен быть от 2024 до 2100")
        fields = {}
        for field in ("days_off", "working_days"):
            values = calendar_data.get(field)
            if not isinstance(values, list) or len(values) > 366:
                raise ValueError(f"{field}: укажите массив дат")
            for value in values:
                if not isinstance(value, str) or date.fromisoformat(value).year != year or date.fromisoformat(value).isoformat() != value:
                    raise ValueError("Даты должны быть в формате ГГГГ-ММ-ДД выбранного года")
            if len(set(values)) != len(values):
                raise ValueError("Даты не должны повторяться")
            fields[field] = sorted(values)
        if set(fields["days_off"]) & set(fields["working_days"]):
            raise ValueError("Дата не может быть одновременно рабочей и выходной")
        statutory = {f"{year}-01-{day:02d}" for day in range(1,9)} | {f"{year}-{day}" for day in ("02-23","03-08","05-01","05-09","06-12","11-04")}
        if not statutory.issubset(set(fields["days_off"])):
            raise ValueError("В days_off должны быть все федеральные праздники, включая 1–8 января")
        if type(calendar_data.get("confirmed", False)) is not bool:
            raise ValueError("confirmed должен быть true или false")
        import calendar as month_calendar
        for month in range(1,13):
            if not any((date(year,month,day).weekday()<5 and date(year,month,day).isoformat() not in fields["days_off"]) or date(year,month,day).isoformat() in fields["working_days"] for day in range(1,month_calendar.monthrange(year,month)[1]+1)):
                raise ValueError("В каждом месяце должен быть хотя бы один рабочий день")
        data.setdefault("calendar_overrides", {})[str(year)] = {"year":year,**fields,"confirmed":calendar_data.get("confirmed",False)}
        return
    if action == "calendar_reset":
        year = payload["year"]
        if type(year) is not int or not 2024 <= year <= 2100:
            raise ValueError("Некорректный год")
        data.get("calendar_overrides", {}).pop(str(year),None)
        return
    if action == "debt_create":
        name = label(payload["name"])
        principal, remaining = amount(payload["principal"]), amount(payload.get("remaining",payload["principal"]))
        if remaining > principal:
            raise ValueError("Остаток не может превышать первоначальную сумму")
        data.setdefault("debts", []).append({"id":uuid4().hex,"name":name,"principal":principal,"remaining":remaining,"payments":[]})
        return
    if action in ("debt_update", "debt_delete", "debt_payment_delete"):
        debts = data.get("debts", [])
        debt = next((d for d in debts if d["id"] == payload["debt_id"]), None)
        if debt is None:
            raise ValueError("Долг не найден")
        if action == "debt_delete":
            debts.remove(debt)
        elif action == "debt_update":
            name, principal = label(payload["name"]), amount(payload["principal"])
            paid = debt["principal"] - debt["remaining"]
            if principal < paid:
                raise ValueError("Изначальная сумма не может быть меньше уже внесённой")
            debt.update(name=name,principal=principal,remaining=principal-paid)
        else:
            payment = next((p for p in debt["payments"] if p["id"] == payload["payment_id"]), None)
            if payment is None:
                raise ValueError("Платёж не найден")
            debt["payments"].remove(payment)
            debt["remaining"] += payment["amount"]
        return
    if action == "debt_payment":
        debt = next((d for d in data.get("debts", []) if d["id"] == payload["debt_id"]), None)
        if debt is None:
            raise ValueError("Долг не найден")
        payment = amount(payload["amount"])
        if payment == 0 or payment > debt["remaining"]:
            raise ValueError("Сумма платежа должна быть больше нуля и не превышать остаток")
        paid_date = date.fromisoformat(payload["date"]).isoformat()
        debt["payments"].append({"id":uuid4().hex,"amount":payment,"date":paid_date})
        debt["remaining"] -= payment
        return
    if action == "budget_clone":
        source = next((b for b in data.get("budgets", []) if b["id"] == payload["budget_id"]), None)
        if source is None:
            raise ValueError("Бюджет не найден")
        month = payload["month"]
        if not isinstance(month, str) or not re.fullmatch(r"(202[5-9]|20[3-9][0-9]|2100)-(0[1-9]|1[0-2])", month):
            raise ValueError("Выберите месяц бюджета")
        data["budgets"].append({"id":uuid4().hex,"name":budget_name(month),"month":month,
                                "expenses":[{**e,"id":uuid4().hex,"month":month,"transferred":False,"children":[{**child,"id":uuid4().hex} for child in e.get("children",[])]} for e in source["expenses"]]})
        return
    if action == "budget_delete":
        budgets = data.get("budgets", [])
        budget = next((b for b in budgets if b["id"] == payload["budget_id"]), None)
        if budget is None:
            raise ValueError("Бюджет не найден")
        budgets.remove(budget)
        return
    if action == "budget_create":
        month = payload["month"]
        if not isinstance(month, str) or not re.fullmatch(r"(202[5-9]|20[3-9][0-9]|2100)-(0[1-9]|1[0-2])", month):
            raise ValueError("Выберите месяц бюджета")
        data.setdefault("budgets", []).append({"id":uuid4().hex,"name":budget_name(month),"month":month,"expenses":[]})
        return
    if action in ("budget_part_save", "budget_part_delete"):
        budget = next((b for b in data.get("budgets", []) if b["id"] == payload["budget_id"]), None)
        if budget is None:
            raise ValueError("Бюджет не найден")
        expense = next((e for e in budget["expenses"] if e["id"] == payload["expense_id"]), None)
        if expense is None:
            raise ValueError("Категория не найдена")
        parts = expense.get("children", [])
        part = next((p for p in parts if p["id"] == payload.get("part_id")), None)
        if action == "budget_part_delete":
            if part is None:
                raise ValueError("Подтип не найден")
            parts.remove(part)
            return
        if payload.get("part_id") and part is None:
            raise ValueError("Подтип не найден")
        comment = payload.get("comment", "")
        if not isinstance(comment, str) or len(comment)>1000:
            raise ValueError("Комментарий должен быть до 1000 символов")
        fields = {"name":label(payload["name"]),"amount":amount(payload["amount"]),"comment":comment.strip()}
        if part is None:
            part = {"id":uuid4().hex}
            expense.setdefault("children", []).append(part)
        part.update(fields)
        return
    if action in ("budget_expense_save", "budget_expense_delete", "budget_expense_transferred"):
        budget = next((b for b in data.get("budgets", []) if b["id"] == payload["budget_id"]), None)
        if budget is None:
            raise ValueError("Бюджет не найден")
        expense = next((e for e in budget["expenses"] if e["id"] == payload.get("expense_id")), None)
        if action == "budget_expense_transferred":
            if expense is None:
                raise ValueError("Трата не найдена")
            transferred = payload.get("transferred")
            if not isinstance(transferred, bool):
                raise ValueError("Отметка перевода должна быть логическим значением")
            expense["transferred"] = transferred
            return
        if action == "budget_expense_delete":
            if expense is None:
                raise ValueError("Трата не найдена")
            budget["expenses"].remove(expense)
            return
        if payload.get("expense_id") and expense is None:
            raise ValueError("Трата не найдена")
        month = payload["month"]
        if not isinstance(month, str) or not re.fullmatch(r"(202[5-9]|20[3-9][0-9]|2100)-(0[1-9]|1[0-2])", month):
            raise ValueError("Некорректный месяц бюджета")
        if budget.get("month") and budget["month"] != month:
            raise ValueError("Трата должна относиться к месяцу бюджета")
        comment = payload.get("comment", "")
        if not isinstance(comment, str) or len(comment) > 1000:
            raise ValueError("Комментарий должен быть до 1000 символов")
        payment_id = payload["payment_id"]
        valid_sources = {f"{w['id']}:{kind}" for w in data.get("workers", []) for kind in (["fixed"] if w.get("employment") == "fixed" else ["salary", "advance"])}
        if payment_id not in valid_sources and not (expense and expense["payment_id"] == payment_id):
            raise ValueError("Выберите источник дохода")
        fields = {"name":label(payload["name"]),"amount":amount(payload["amount"]),"comment":comment.strip(),"month":month,"payment_id":payment_id}
        if expense is None:
            expense = {"id":uuid4().hex}
            budget["expenses"].append(expense)
        expense.update(fields)
        return
    if action == "worker_delete":
        workers = data.get("workers", [])
        worker = next((w for w in workers if w["id"] == payload["worker_id"]), None)
        if worker is None:
            raise ValueError("Работник не найден")
        workers.remove(worker)
        return
    if action == "worker_save":
        name = label(payload["name"])
        income = amount(payload["income"])
        employment = payload.get("employment")
        if employment not in ("TK", "fixed"):
            raise ValueError("Неизвестный тип дохода")
        days = [payload.get("fixed_day")] if employment == "fixed" else [payload.get("advance_day"), payload.get("salary_day")]
        if any(type(day) is not int or not 1 <= day <= 31 for day in days):
            raise ValueError("День выплаты должен быть от 1 до 31")
        workers = data.setdefault("workers", [])
        worker = next((w for w in workers if w["id"] == payload.get("worker_id")), None)
        if payload.get("worker_id") and worker is None:
            raise ValueError("Работник не найден")
        if worker is None:
            worker = {"id": uuid4().hex}
            workers.append(worker)
        worker.update(name=name, income=income, employment=employment)
        if employment == "fixed":
            worker.update(fixed_day=days[0])
            worker.pop("advance_day", None)
            worker.pop("salary_day", None)
        else:
            worker.update(advance_day=days[0], salary_day=days[1])
            worker.pop("fixed_day", None)
        return
    deposits = data["deposits"]
    if action == "create":
        deposits.append({"id": uuid4().hex, "name": label(payload["name"]),
                         "principal": amount(payload["principal"]), "expenses": []})
        return
    deposit = next((d for d in deposits if d["id"] == payload["deposit_id"]), None)
    if deposit is None:
        raise ValueError("Вклад не найден")
    if action == "update":
        deposit.update(name=label(payload["name"]), principal=amount(payload["principal"]))
    elif action == "top_up":
        deposit["principal"] = amount(deposit["principal"] + amount(payload["amount"]))
    elif action == "delete":
        deposits.remove(deposit)
    elif action == "expense_save":
        kind = payload.get("kind", "expense")
        if kind not in ("expense", "income"):
            raise ValueError("Неизвестный тип операции")
        due = date.fromisoformat(payload["date"]).isoformat()
        if type(payload["paid"]) is not bool:
            raise ValueError("Некорректный статус платежа")
        expense = next((e for e in deposit["expenses"] if e["id"] == payload.get("expense_id")), None)
        if payload.get("expense_id") and expense is None:
            raise ValueError("Расход не найден")
        if expense is None:
            expense = {"id": uuid4().hex, "notified_date": None}
            deposit["expenses"].append(expense)
        if expense.get("date") != due:
            expense["notified_date"] = None
        expense.update(kind=kind, name=label(payload["name"]), amount=amount(payload["amount"]), date=due, paid=payload["paid"])
    elif action in ("expense_paid", "expense_delete"):
        expense = next((e for e in deposit["expenses"] if e["id"] == payload["expense_id"]), None)
        if expense is None:
            raise ValueError("Расход не найден")
        if action == "expense_delete":
            deposit["expenses"].remove(expense)
        else:
            if type(payload["paid"]) is not bool:
                raise ValueError("Некорректный статус платежа")
            expense["paid"] = payload["paid"]
    else:
        raise ValueError("Неизвестное действие")


def due_events(data, today):
    events = []
    for deposit in data["deposits"]:
        for expense in deposit["expenses"]:
            if expense.get("kind", "expense") == "expense" and not expense["paid"] and expense["date"] <= today and expense.get("notified_date") != expense["date"]:
                events.append({"deposit_id": deposit["id"], "deposit_name": deposit["name"],
                               "expense_id": expense["id"], "expense_name": expense["name"],
                               "amount": expense["amount"] / 100, "currency": "RUB", "due_date": expense["date"]})
                expense["notified_date"] = expense["date"]
    return events


MONTHS = ("Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь")

def budget_name(month):
    year, number = month.split("-")
    return f"{MONTHS[int(number)-1]} {year}"


def migrate_budget_months(data, default_month):
    changed = False
    budgets = []
    for budget in data.get("budgets", []):
        if budget.get("month"):
            budgets.append(budget)
            continue
        changed = True
        months = sorted({e["month"] for e in budget["expenses"]}) or [default_month]
        for index, month in enumerate(months):
            budgets.append({"id":budget["id"] if index == 0 else uuid4().hex,
                            "name":budget_name(month),"month":month,
                            "expenses":[e for e in budget["expenses"] if e["month"] == month]})
    if changed:
        data["budgets"] = budgets
    return changed
