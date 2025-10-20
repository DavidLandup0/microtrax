
from typing import List, Optional
from pydantic import BaseModel

class PlotRequest(BaseModel):
    experiments: List[str]
    metric: str
    x_axis: Optional[str] = 'step'
    y_axis_scale: Optional[str] = 'linear'

class ImagesRequest(BaseModel):
    experiment: str

class TextRequest(BaseModel):
    experiment: str

class RenameExperimentRequest(BaseModel):
    name: str

class DeleteExperimentRequest(BaseModel):
    confirm: bool = False
