from __future__ import annotations

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

from src.schemas.artifact import Locator

PERCEPTION_JS = """
() => {
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    return r.width > 1 && r.height > 1 && st.visibility !== "hidden" && st.display !== "none" && st.opacity !== "0";
  };
  const nearbyLabel = (el) => {
    const td = el.closest("td");
    if (td && td.previousElementSibling) {
      return (td.previousElementSibling.innerText || "").trim();
    }
    return "";
  };
  const clickables = [];
  for (const el of document.querySelectorAll("span")) {
    if (!visible(el)) continue;
    const st = getComputedStyle(el);
    const clickable =
      st.cursor === "pointer" ||
      (st.textDecorationLine && st.textDecorationLine.includes("underline")) ||
      (st.borderTopWidth && st.borderTopWidth !== "0px");
    if (!clickable) continue;
    const r = el.getBoundingClientRect();
    const text = (el.innerText || "").trim();
    if (!text) continue;
    clickables.push({
      text,
      x: Math.round(r.x + r.width / 2),
      y: Math.round(r.y + r.height / 2),
    });
  }
  const inputs = [];
  for (const el of document.querySelectorAll("input")) {
    if (!visible(el)) continue;
    const r = el.getBoundingClientRect();
    inputs.push({
      label: nearbyLabel(el),
      value: el.value || "",
      x: Math.round(r.x + r.width / 2),
      y: Math.round(r.y + r.height / 2),
    });
  }
  return {
    url: location.href,
    title: document.title,
    text: (document.body.innerText || "").slice(0, 5000),
    inputs,
    clickables,
  };
}
"""


def observe(page: Page) -> dict:
    snapshot = page.evaluate(PERCEPTION_JS)
    screenshot = page.screenshot(type="jpeg", quality=40)
    snapshot["screenshot_jpeg"] = screenshot
    return snapshot


def resolve_locator(page: Page, locator: Locator):
    if locator.strategy == "nearby_label":
        label = locator.label or ""
        return page.locator("tr").filter(has=page.get_by_text(label, exact=True)).locator("input").first
    if locator.strategy == "visible_text":
        text = locator.text or ""
        return page.get_by_text(text, exact=locator.exact).first
    if locator.strategy == "table_cell":
        header = locator.column_header or "Name"
        row_index = locator.row_index or 0
        table = page.locator("table").filter(has=page.get_by_text(header, exact=True)).last
        body_rows = table.locator("tr")
        return body_rows.nth(row_index + 1).locator("td").first.locator("span").first
    if locator.strategy == "text_matches":
        return page.get_by_text(locator.pattern or locator.text or "", exact=False)
    if locator.strategy == "coordinates":
        return None
    raise ValueError(f"Unknown locator strategy: {locator.strategy}")


def perform(page: Page, action: str, locator: Locator | None, value: str | None, url: str | None) -> str:
    if action == "NAVIGATE":
        page.goto(url or "", wait_until="domcontentloaded")
        return f"navigated:{page.url}"
    if action == "WAIT_FOR":
        needle = (locator.text if locator else None) or (locator.pattern if locator else None) or ""
        page.get_by_text(needle, exact=False).first.wait_for(state="visible", timeout=10000)
        return f"waited:{needle}"
    if action == "CLICK":
        if locator and locator.strategy == "coordinates":
            page.mouse.click(locator.x or 0, locator.y or 0)
            return f"clicked:coords:{locator.x},{locator.y}"
        handle = resolve_locator(page, locator)
        handle.click(timeout=8000)
        return f"clicked:{locator.strategy}"
    if action == "TYPE":
        handle = resolve_locator(page, locator)
        handle.fill(value or "", timeout=8000)
        return f"typed:{locator.label or locator.strategy}"
    if action == "READ":
        if locator and locator.strategy == "text_matches":
            text = page.locator("body").inner_text()
            return text
        handle = resolve_locator(page, locator)
        return handle.inner_text(timeout=8000)
    raise ValueError(f"Unsupported action {action}")


def wait_quiet(page: Page, ms: int = 250) -> None:
    try:
        page.wait_for_timeout(ms)
    except PlaywrightTimeout:
        return
