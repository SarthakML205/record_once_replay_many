from src.guardrails.redact import redact_obj, redact_text


def test_redact_ssn_name_and_card():
    raw = "Chen, Ava SSN 123-45-6789 card 4111111111111111 ***-**-4412"
    out = redact_text(raw)
    assert "123-45-6789" not in out
    assert "4111111111111111" not in out
    assert "Chen, Ava" not in out
    assert "[REDACTED_NAME]" in out
    assert "***-**-XXXX" in out


def test_redact_does_not_mask_token_counts():
    usage = redact_obj({"usage": {"input_tokens": 123, "output_tokens": 9}})
    assert usage["usage"]["input_tokens"] == 123
