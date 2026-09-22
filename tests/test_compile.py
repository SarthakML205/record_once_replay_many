from src.agent.compile import compile_artifact
from src.agent.normalize import locator_from_tool
from src.schemas.artifact import Locator


def test_name_click_becomes_table_cell():
    locator = locator_from_tool(
        {"action": "CLICK", "strategy": "visible_text", "text": "Chen, Ava"},
        {"clickables": [], "inputs": []},
    )
    assert locator.strategy == "table_cell"
    assert locator.column_header == "Name"


def test_compile_uses_parameters_not_literals():
    trajectory = [
        {
            "action": "TYPE",
            "locator": Locator(strategy="nearby_label", label="Member ID"),
            "value": "M10005",
        },
        {
            "action": "CLICK",
            "locator": Locator(strategy="visible_text", text="Search"),
            "value": None,
        },
        {
            "action": "CLICK",
            "locator": Locator(strategy="visible_text", text="Rossi, Elena"),
            "value": None,
        },
        {
            "action": "TYPE",
            "locator": Locator(strategy="nearby_label", label="Account Name"),
            "value": "Secret Family Trust",
        },
        {
            "action": "TYPE",
            "locator": Locator(strategy="nearby_label", label="Initial Deposit"),
            "value": "40",
        },
        {
            "action": "CLICK",
            "locator": Locator(strategy="visible_text", text="Submit Request"),
            "value": None,
        },
        {
            "action": "CLICK",
            "locator": Locator(strategy="visible_text", text="Confirm"),
            "value": None,
        },
    ]
    artifact = compile_artifact("open savings for Elena", "http://localhost:5173", trajectory, "Transaction complete. Confirmation ID CNF-TEST-1")
    dumped = artifact.to_clean_json()
    assert "M10005" not in dumped
    assert "Secret Family Trust" not in dumped
    assert "Elena" not in dumped
    assert "${input.member_id}" in dumped
    assert "${input.account_name}" in dumped
    assert "${input.initial_deposit}" in dumped
    confirm = next(step for step in artifact.steps if step.locator and step.locator.text == "Confirm")
    assert confirm.risk == "RISKY"
    assert confirm.reversibility == "IRREVERSIBLE"
    search = next(step for step in artifact.steps if step.locator and step.locator.text == "Search")
    assert search.risk == "SAFE"
    assert "member_id" in artifact.input_contract
    assert "confirmation_id" in artifact.output_contract
