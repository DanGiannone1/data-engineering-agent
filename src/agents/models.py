"""Pydantic models for structured agent outputs."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Structured Pseudocode - matches frontend types
# =============================================================================

class FieldMapping(BaseModel):
    """A single field mapping from source to target."""
    source: str = Field(description="Source column name")
    target: str = Field(description="Target DNAV field name")
    transform: Literal["direct", "rename", "formula", "lookup"] = Field(
        description="Type of transformation"
    )
    formula: Optional[str] = Field(default=None, description="Formula if transform=formula")


class JoinKey(BaseModel):
    """Join key specification for lookup joins."""
    source: str = Field(description="Source column to join on")
    lookup: str = Field(description="Lookup table column to join on")


class SampleMapping(BaseModel):
    """Example of a lookup mapping."""
    from_value: str = Field(alias="from", description="Source value")
    to_value: str = Field(alias="to", description="Mapped value")

    class Config:
        populate_by_name = True


class BusinessRule(BaseModel):
    """A conditional business rule."""
    condition: str = Field(description="Condition to check")
    action: str = Field(description="Action to take when condition is true")


class FieldMappingStep(BaseModel):
    """Step for direct field mappings."""
    id: str
    type: Literal["field_mapping"] = "field_mapping"
    title: str
    description: Optional[str] = None
    mappings: list[FieldMapping]


class LookupJoinStep(BaseModel):
    """Step for joining with lookup tables."""
    id: str
    type: Literal["lookup_join"] = "lookup_join"
    title: str
    description: Optional[str] = None
    join_key: JoinKey
    output_field: str
    filter: Optional[str] = None
    sample_mappings: Optional[list[SampleMapping]] = None


class BusinessRuleStep(BaseModel):
    """Step for applying business rules."""
    id: str
    type: Literal["business_rule"] = "business_rule"
    title: str
    description: Optional[str] = None
    rules: list[BusinessRule]


class FilterStep(BaseModel):
    """Step for filtering rows."""
    id: str
    type: Literal["filter"] = "filter"
    title: str
    description: Optional[str] = None
    condition: str
    exclude: bool = False


class CalculationStep(BaseModel):
    """Step for calculated/derived fields."""
    id: str
    type: Literal["calculation"] = "calculation"
    title: str
    description: Optional[str] = None
    output_field: str
    formula: str


class OutputStep(BaseModel):
    """Step for output specification."""
    id: str
    type: Literal["output"] = "output"
    title: str
    description: Optional[str] = None
    format: str
    destination: str


# Union type for all step types
PseudocodeStep = (
    FieldMappingStep
    | LookupJoinStep
    | BusinessRuleStep
    | FilterStep
    | CalculationStep
    | OutputStep
)


class StructuredPseudocode(BaseModel):
    """Complete structured pseudocode for auditor review."""
    version: int = Field(default=1, description="Version number, increment on revision")
    summary: str = Field(description="Brief summary of the transformation")
    steps: list[PseudocodeStep] = Field(description="Ordered list of transformation steps")

    class Config:
        json_schema_extra = {
            "example": {
                "version": 1,
                "summary": "Transform Effective_Transactions to DNAV Fund Transactions",
                "steps": [
                    {
                        "id": "1",
                        "type": "field_mapping",
                        "title": "Map source columns to DNAV fields",
                        "mappings": [
                            {"source": "Trade Date", "target": "T_DATE", "transform": "direct"}
                        ],
                    }
                ],
            }
        }


# =============================================================================
# Code Generation Output
# =============================================================================

class GeneratedCode(BaseModel):
    """Generated PySpark transformation code."""
    code: str = Field(description="Complete PySpark code")
    description: str = Field(description="Brief description of what the code does")
