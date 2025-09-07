
from typing import List
from pydantic import BaseModel

class PlotRequest(BaseModel):
    experiments: List[str]
    metric: str

class ImagesRequest(BaseModel):
    experiment: str

class RenameExperimentRequest(BaseModel):
    name: str

class DeleteExperimentRequest(BaseModel):
    confirm: bool = False
