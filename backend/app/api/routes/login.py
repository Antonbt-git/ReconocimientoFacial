from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.login_schema import LoginFacialResponse
from app.services.login_service import login_facial


router = APIRouter(
    prefix="/api",
    tags=["Login Facial"]
)


@router.post(
    "/login-facial",
    response_model=LoginFacialResponse
)
async def login_facial_endpoint(
    dni: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    if not file.content_type or not file.content_type.startswith(
        "image/"
    ):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser una imagen"
        )

    image_bytes = await file.read()

    try:

        resultado = login_facial(
            db,
            dni=dni,
            image_bytes=image_bytes
        )

        return resultado

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
