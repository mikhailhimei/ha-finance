"""Shared Home Assistant finance panel and authenticated websocket API."""
import asyncio
from copy import deepcopy
from datetime import timedelta
from pathlib import Path

import voluptuous as vol
from homeassistant.components import frontend, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .model import apply, due_events

DOMAIN = "ha_finance"


async def async_setup_entry(hass, entry):
    store = Store(hass, 1, DOMAIN)
    data = await store.async_load() or {"deposits": []}
    lock = asyncio.Lock()
    listeners = set()

    def publish():
        for callback in list(listeners):
            callback(deepcopy(data))

    async def remind(now=None):
        async with lock:
            events = due_events(data, dt_util.now().date().isoformat())
            if events:
                await store.async_save(data)
                for event in events:
                    hass.bus.async_fire("ha_finance_expense_due", event)
                publish()

    hass.data[DOMAIN] = {"data": data, "store": store, "lock": lock,
                         "listeners": listeners, "publish": publish, "remind": remind}
    if not hass.data.get("ha_finance_registered"):
        await hass.http.async_register_static_paths([
            StaticPathConfig("/ha_finance_static", str(Path(__file__).parent / "frontend"), False)
        ])
        websocket_api.async_register_command(hass, ws_get)
        websocket_api.async_register_command(hass, ws_mutate)
        websocket_api.async_register_command(hass, ws_subscribe)
        hass.data["ha_finance_registered"] = True
    frontend.async_register_built_in_panel(
        hass, component_name="custom", sidebar_title="Финансы", sidebar_icon="mdi:wallet",
        frontend_url_path="ha-finance", require_admin=False,
        config={"_panel_custom": {"name": "ha-finance-panel", "module_url": "/ha_finance_static/finance.js?v=0.1.3"}},
    )
    entry.async_on_unload(async_track_time_interval(hass, remind, timedelta(minutes=1)))
    await remind()
    return True


async def async_unload_entry(hass, entry):
    frontend.async_remove_panel(hass, "ha-finance")
    hass.data.pop(DOMAIN, None)
    return True


@websocket_api.websocket_command({vol.Required("type"): "ha_finance/get"})
@websocket_api.async_response
async def ws_get(hass, connection, msg):
    if DOMAIN not in hass.data:
        connection.send_error(msg["id"], "not_loaded", "Интеграция не загружена")
        return
    connection.send_result(msg["id"], hass.data[DOMAIN]["data"])


@websocket_api.websocket_command({vol.Required("type"): "ha_finance/subscribe"})
@websocket_api.async_response
async def ws_subscribe(hass, connection, msg):
    if DOMAIN not in hass.data:
        connection.send_error(msg["id"], "not_loaded", "Интеграция не загружена")
        return
    state = hass.data[DOMAIN]
    def callback(data):
        connection.send_event(msg["id"], data)
    state["listeners"].add(callback)
    connection.subscriptions[msg["id"]] = lambda: state["listeners"].discard(callback)
    connection.send_result(msg["id"])
    callback(state["data"])


@websocket_api.websocket_command({vol.Required("type"): "ha_finance/mutate", vol.Required("action"): str,
                                  vol.Required("payload"): dict})
@websocket_api.async_response
async def ws_mutate(hass, connection, msg):
    if DOMAIN not in hass.data:
        connection.send_error(msg["id"], "not_loaded", "Интеграция не загружена")
        return
    state = hass.data[DOMAIN]
    async with state["lock"]:
        updated = deepcopy(state["data"])
        try:
            apply(updated, msg["action"], msg["payload"])
        except (KeyError, ValueError, TypeError) as err:
            connection.send_error(msg["id"], "invalid_input", str(err))
            return
        await state["store"].async_save(updated)
        state["data"].clear()
        state["data"].update(updated)
        state["publish"]()
        connection.send_result(msg["id"], updated)
    await state["remind"]()
