"""Schemi Pydantic di request/response dell'API. Nessuna logica qui."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    plan: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProviderOut(BaseModel):
    id: str
    label: str
    models: list[str]
    default_model: str


class ParseLogsIn(BaseModel):
    log_content: str
    severities: list[str]
    search_query: str = ""
    max_lines: int = 200
    slice_from_end: bool = True
    dedupe: bool = True


class ParseLogsOut(BaseModel):
    total_lines: int
    filtered_count: int
    severity_counts: dict[str, int]
    logs_to_send: list[str]
    colorized_preview: str


class AnalyzeLogsIn(BaseModel):
    provider: str
    model: str
    logs_payload: str
    filename: str = "log.txt"
    temperature: float = 0.2


class CostBreakdownOut(BaseModel):
    input_cost: float
    output_cost: float
    total_cost: float
    output_tokens_est: int


class SuggestionOut(BaseModel):
    model: str
    total_cost: float
    savings_pct: float


class EstimateOut(BaseModel):
    token_count: int
    is_real_token_count: bool
    cost_breakdown: CostBreakdownOut
    suggestion: SuggestionOut | None = None


class AnalyzeLogsOut(EstimateOut):
    report: dict


class AnalysisSummaryOut(BaseModel):
    id: int
    filename: str
    provider: str
    model_used: str
    token_count: int
    cost_estimate: float
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisDetailOut(AnalysisSummaryOut):
    report_json: dict


class UsageOut(BaseModel):
    plan: str
    period: str
    used: int
    limit: int
    remaining: int
