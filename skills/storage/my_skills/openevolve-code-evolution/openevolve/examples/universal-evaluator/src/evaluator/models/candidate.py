from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field

class Candidate(BaseModel):
    model_config=ConfigDict(frozen=True)
    candidate_id:str=Field(min_length=1); root:Path; entrypoint:str=Field(min_length=1); language:str=Field(min_length=1); version:str|None=None; metadata:dict[str,str]=Field(default_factory=dict)
    def entrypoint_path(self)->Path:
        root=self.root.resolve(); path=(root/self.entrypoint).resolve()
        if root not in path.parents and path!=root: raise ValueError("entrypoint escapes candidate root")
        return path
