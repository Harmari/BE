from pydantic import BaseModel
from typing import List


class TestList(BaseModel):
    listItem1: str
    listItem2: str
    listItem3: str
    listItem4: str

class TestRequest(BaseModel):
    test1: str
    test2: str
    test3: str

class TestResponse(BaseModel):
    test1: str
    test2: str
    test3: str
    result: List[TestList]

