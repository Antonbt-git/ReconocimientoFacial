from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.probability_schema import (
    ModelMetricsResponse,
    TrainingRecordResponse,
    VerificacionCreate,
)
from app.services.probability_service import probability_service
from app.services.training_record_service import verificar_reconocimiento


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


@router.post(
    "/verificaciones",
    response_model=TrainingRecordResponse,
    status_code=201
)
def crear_verificacion(
    payload: VerificacionCreate,
    db: Session = Depends(get_db)
):
    try:
        registro = verificar_reconocimiento(
            db,
            log_id=payload.log_id,
            resultado_real=payload.resultado_real
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    return registro
