from typing import Optional
from pydantic import BaseModel, Field

class AdCopyInput(BaseModel):
    """Structured input for the ad copy generation service."""
    targets: list[str] = Field(description="A list of targeting keywords or phrases.")
    product: str = Field(description="The product name or a brief description.")
    context: Optional[str] = Field(description="Optional additional context for generation.")

class AdCopyOutput(BaseModel):
    """Structured output from the ad copy generation service."""
    targets: list[str] = Field(description="The list of targeting keywords or phrases from the input.")
    product: str = Field(description="The product name or description from the input.")
    plan: list[str] = Field(description="The edit plan candidates to make the image fit the targets.")
