from datetime import datetime
from pydantic import BaseModel


class ApprovedCodeMetadata(BaseModel):
    client_id: str
    approved_by: str
    approved_at: datetime
    last_run_at: datetime | None = None
    run_count: int = 0
