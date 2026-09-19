from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.probability_schema import ModelMetricsResponse
from app.services.probability_service import probability_service


router = APIRouter(
    prefix="/api/modelos",
    tags=["Machine Learning"]
)


@router.post(
    "/entrenar",
    response_model=ModelMetricsResponse
)
def entrenar_modelo(
    db: Session = Depends(get_db)
):
    try:
        metricas = probability_service.train(db)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    return metricas


@router.get(
    "/metricas",
    response_model=ModelMetricsResponse | None
)
def obtener_metricas():
    metricas = probability_service.get_metrics()

    if metricas is None:
        raise HTTPException(
            status_code=404,
            detail="El modelo aún no ha sido entrenado"
        )

    return metricas
