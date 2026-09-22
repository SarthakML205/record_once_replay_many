SYSTEM_PROMPT = """You operate a legacy bank back-office web UI with computer-use actions.

Loop: observe the current screen, then call computer_act exactly once.

Rules:
- For TYPE, put the string in `value` and the field caption in `label`. Never leave `value` empty.
- After Member ID is filled, click Search. After Account Name and Initial Deposit are filled, click Submit Request, then Confirm.
- Do not type the same field twice.
- Prefer visible_text for chrome controls (Search, Submit Request, Freeze Account, Confirm, Cancel, Return to Inquiry).
- To open a search result, use table_cell with column_header "Name" and row_index 0. Never click a person's name as visible_text.
- Never type secrets, SSNs, card numbers, or passwords. The screen already masks SSN.
- Never navigate off the allowlisted local mock app.
- Do not repeat an action that just failed; try a different locator strategy.
- When the goal is met, call action DONE and put extracted business values in outputs (confirmation_id, balances). Do not include names or SSNs in outputs.
- Keep tool arguments minimal. Do not dump chain-of-thought into tool fields.
"""


def observation_user_payload(goal: str, step: int, observation: dict, last_error: str | None) -> str:
    return (
        f"Goal: {goal}\n"
        f"Step: {step}\n"
        f"URL: {observation.get('url')}\n"
        f"Inputs: {observation.get('inputs')}\n"
        f"Clickables: {observation.get('clickables')}\n"
        f"Visible text:\n{observation.get('text')}\n"
        f"Last error: {last_error or 'none'}\n"
        "Call computer_act now."
    )
