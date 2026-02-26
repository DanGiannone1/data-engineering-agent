from pydantic import BaseModel


class CheckResult(BaseModel):
    name: str
    passed: bool
    message: str
    details: dict | None = None


class IntegrityReport(BaseModel):
    checks: list[CheckResult]
    overall_pass: bool
    errors: list[str] = []
