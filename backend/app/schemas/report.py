"""Daily report schemas."""

from datetime import date

from app.schemas.common import ORMModel


class ReportRowResponse(ORMModel):
    id: int
    section: str
    label: str
    value: str
    numeric_value: float | None


class DailyReportResponse(ORMModel):
    id: int
    portfolio_id: int
    report_date: date
    csv_path: str | None
    summary: dict
    narrative: str | None
    rows: list[ReportRowResponse]
