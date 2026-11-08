"""Pure finance rules. All amounts are integer kopecks, never floats."""
from datetime import date
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
    actual = sum(e["amount"] for e in deposit["expenses"] if e["paid"])
    expected = sum(e["amount"] for e in deposit["expenses"] if not e["paid"])
    return {"principal": deposit["principal"], "actual": actual, "expected": expected,
            "balance": deposit["principal"] - actual,
            "available": deposit["principal"] - actual - expected}


def apply(data, action, payload):
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
        expense.update(name=label(payload["name"]), amount=amount(payload["amount"]), date=due, paid=payload["paid"])
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
            if not expense["paid"] and expense["date"] <= today and expense.get("notified_date") != expense["date"]:
                events.append({"deposit_id": deposit["id"], "deposit_name": deposit["name"],
                               "expense_id": expense["id"], "expense_name": expense["name"],
                               "amount": expense["amount"] / 100, "currency": "RUB", "due_date": expense["date"]})
                expense["notified_date"] = expense["date"]
    return events
