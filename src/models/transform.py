from pydantic import BaseModel


class TransformRequest(BaseModel):
    client_id: str
    mapping_path: str  # ADLS path to mapping spreadsheet
    data_path: str  # ADLS path to source data


class TransformStatus(BaseModel):
    instance_id: str
    client_id: str
    phase: int  # 1-6
    phase_name: str
    pending_review: bool = False
    pseudocode: str | None = None
    integrity_report: dict | None = None
    output_path: str | None = None
    error: str | None = None
