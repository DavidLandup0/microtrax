
from typing import List, Optional
from pydantic import BaseModel

class PlotRequest(BaseModel):
    experiments: List[str]
    metric: str
    x_axis_mode: Optional[str] = 'step'

class ImagesRequest(BaseModel):
    experiment: str

class RenameExperimentRequest(BaseModel):
    name: str

class DeleteExperimentRequest(BaseModel):
    confirm: bool = False
