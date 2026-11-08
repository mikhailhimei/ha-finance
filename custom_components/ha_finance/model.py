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
    if action == "budget_create":
        data.setdefault("budgets", []).append({"id":uuid4().hex,"name":label(payload["name"]),"expenses":[]})
        return
    if action in ("budget_expense_save", "budget_expense_delete"):
        budget = next((b for b in data.get("budgets", []) if b["id"] == payload["budget_id"]), None)
        if budget is None:
            raise ValueError("Бюджет не найден")
        expense = next((e for e in budget["expenses"] if e["id"] == payload.get("expense_id")), None)
        if action == "budget_expense_delete":
            if expense is None:
                raise ValueError("Трата не найдена")
            budget["expenses"].remove(expense)
            return
        if payload.get("expense_id") and expense is None:
            raise ValueError("Трата не найдена")
        month = payload["month"]
        if not isinstance(month, str) or not re.fullmatch(r"202[5-7]-(0[1-9]|1[0-2])", month):
            raise ValueError("Некорректный месяц бюджета")
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
