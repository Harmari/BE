import logging

from bson import ObjectId

from app.schemas.test_schema import TestResponse, TestRequest, TestList
from app.db.session import get_database

db = get_database()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def TestListService(request: TestRequest) -> TestResponse:

    test_insert = await db["test"].insert_one(request.model_dump())
    test_key = str(test_insert.inserted_id)

    test_result = await db["test"].find_one({"_id": ObjectId(test_key)})

    result_list = [
        TestList(
            listItem1=str("할머리"),
            listItem2=str("해커톤"),
            listItem3=str("머리할"),
            listItem4=str("할머리"),
        )
        for _ in range(3)
    ]

    return TestResponse(
        test1= test_result["test1"],
        test2= test_result["test2"],
        test3= test_result["test3"],
        result=result_list
    )
