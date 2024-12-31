from pydantic import BaseModel
from typing import List

class QueryInfoRequest(BaseModel):
    text: str
    kdb_id: str


class DocInfoRequest(BaseModel):
    id: str
    kdb_id: str

class ContentRequest(BaseModel):
    text:str
