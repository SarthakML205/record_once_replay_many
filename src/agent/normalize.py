from __future__ import annotations

from src.guardrails.policy import CHROME_CLICK_TEXTS
from src.schemas.artifact import Locator


def _nearest(items: list[dict], x: int, y: int) -> dict | None:
    if not items:
        return None
    return min(items, key=lambda item: (item["x"] - x) ** 2 + (item["y"] - y) ** 2)


def locator_from_tool(payload: dict, observation: dict) -> Locator | None:
    action = payload.get("action")
    if action in {"DONE", "NAVIGATE"}:
        return None
    strategy = payload.get("strategy")
    text = payload.get("text") or payload.get("label")
    label = payload.get("label")
    x = payload.get("x")
    y = payload.get("y")

    if action == "TYPE":
        if not label and strategy == "coordinates" and x is not None and y is not None:
            nearest = _nearest(observation.get("inputs") or [], int(x), int(y))
            label = (nearest or {}).get("label")
        if not label:
            label = payload.get("label")
        if label:
            return Locator(strategy="nearby_label", label=label)
        return Locator(
            strategy=strategy or "nearby_label",
            label=label,
            text=text,
            x=x,
            y=y,
        )

    if action == "CLICK":
        if (not text or "," in (text or "")) and strategy == "coordinates" and x is not None and y is not None:
            nearest = _nearest(observation.get("clickables") or [], int(x), int(y))
            text = (nearest or {}).get("text") or text
        if text in CHROME_CLICK_TEXTS:
            return Locator(strategy="visible_text", text=text, exact=True)
        if text and "," in text:
            return Locator(strategy="table_cell", column_header="Name", row_index=0)
        if strategy == "table_cell" or payload.get("column_header"):
            return Locator(
                strategy="table_cell",
                column_header=payload.get("column_header") or "Name",
                row_index=int(payload.get("row_index") or 0),
            )
        if text:
            return Locator(strategy="visible_text", text=text, exact=True)
        if strategy == "coordinates":
            return Locator(strategy="coordinates", x=x, y=y)

    if action in {"WAIT_FOR", "READ"}:
        return Locator(
            strategy=strategy or "text_matches",
            text=text,
            pattern=payload.get("pattern") or text,
        )
    if strategy:
        return Locator(
            strategy=strategy,
            text=text,
            label=label,
            column_header=payload.get("column_header"),
            row_index=payload.get("row_index"),
            pattern=payload.get("pattern"),
            x=x,
            y=y,
        )
    return None
