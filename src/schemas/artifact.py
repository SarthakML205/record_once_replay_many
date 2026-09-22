from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ActionType = Literal["CLICK", "TYPE", "NAVIGATE", "WAIT_FOR", "READ", "DONE"]
RiskLevel = Literal["SAFE", "RISKY"]
Reversibility = Literal["REVERSIBLE", "IRREVERSIBLE"]
OutcomeClass = Literal["SUCCESS", "BUSINESS", "RECOVERABLE", "HARD_FAILURE"]


class Locator(BaseModel):
    strategy: Literal[
        "visible_text",
        "nearby_label",
        "table_cell",
        "coordinates",
        "text_matches",
    ]
    text: str | None = None
    label: str | None = None
    column_header: str | None = None
    row_index: int | None = None
    pattern: str | None = None
    x: int | None = None
    y: int | None = None
    exact: bool = True


class Checkpoint(BaseModel):
    id: str
    kind: Literal["text_contains", "text_matches", "url_matches"]
    text: str | None = None
    pattern: str | None = None
    url_pattern: str | None = None
    optional: bool = False


class FieldSpec(BaseModel):
    type: Literal["string", "number", "boolean"]
    required: bool = True
    description: str = ""


class ActionStep(BaseModel):
    id: str
    action: ActionType
    risk: RiskLevel
    reversibility: Reversibility
    locator: Locator | None = None
    value: str | None = None
    url: str | None = None
    checkpoint: str | None = None
    extract_as: str | None = None
    notes: str = ""


class OutcomeRule(BaseModel):
    code: str
    when_text: str
    outcome_class: OutcomeClass


class CapabilityArtifact(BaseModel):
    schema_version: str = "1.0"
    id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    target: dict[str, Any] = Field(default_factory=dict)
    input_contract: dict[str, FieldSpec] = Field(default_factory=dict)
    output_contract: dict[str, FieldSpec] = Field(default_factory=dict)
    steps: list[ActionStep] = Field(default_factory=list)
    checkpoints: list[Checkpoint] = Field(default_factory=list)
    outcome_taxonomy: list[OutcomeRule] = Field(default_factory=list)

    def to_clean_json(self) -> str:
        return self.model_dump_json(indent=2, exclude_none=True)
