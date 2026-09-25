from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class JudgeQuestion(BaseModel):
    model_config=ConfigDict(extra="forbid")
    id:str=Field(min_length=1); proposition:str=Field(min_length=1); response_type:Literal["choice","score","probability"]; choices:list[str]|None=None; rubric:str|None=None

class Judgment(BaseModel):
    model_config=ConfigDict(extra="forbid")
    question_id:str; response_type:Literal["choice","score","probability"]; value:float|str; confidence:float=Field(ge=0,le=1); evidence_ids:list[str]=Field(default_factory=list); metadata:dict[str,str]=Field(default_factory=dict)
