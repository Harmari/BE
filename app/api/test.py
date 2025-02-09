from fastapi import APIRouter, HTTPException, status, Request
from app.schemas.test_schema import (
    TestRequest, TestResponse
)
from app.services.test_service import (
    TestListService
)

router = APIRouter()

@router.post("", response_model=TestResponse)
async def harmari_test_endpoint(request: TestRequest):
    try:
        test_list = await TestListService(request)
        return test_list
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오류 : {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오류 : {str(e)}"
        )