from src.engine.substitute import substitute
from src.schemas.artifact import OutcomeRule
from src.engine.substitute import classify_text


def test_substitute_parameters():
    assert substitute("id=${input.member_id}", {"member_id": "M10002"}) == "id=M10002"


def test_business_outcome_is_not_failure():
    rules = [OutcomeRule(code="MEMBER_NOT_FOUND", when_text="No matching member found", outcome_class="BUSINESS")]
    rule = classify_text("Alert: No matching member found", rules)
    assert rule is not None
    assert rule.outcome_class == "BUSINESS"
