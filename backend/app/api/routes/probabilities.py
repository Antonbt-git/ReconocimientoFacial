from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.recognition_log_model import RecognitionLog
from app.schemas.probability_schema import (
    PredictionRequest,
    PredictionResponse,
    ProbabilityStatsResponse,
)
from app.services.probability_service import probability_service


router = APIRouter(
    prefix="/api/probabilidades",
    tags=["Probabilidades"]
)


@router.get(
    "",
    response_model=ProbabilityStatsResponse
)
def get_probability_stats(
    db: Session = Depends(get_db)
):
    total = db.scalar(
        select(
            func.count(RecognitionLog.id)
        )
    ) or 0

    coincidencias = db.scalar(
        select(
            func.count(RecognitionLog.id)
        ).where(
            RecognitionLog.coincide.is_(True)
        )
    ) or 0

    no_coincidencias = total - coincidencias

    promedio = db.scalar(
        select(
            func.avg(RecognitionLog.similitud)
        )
    )

    maxima = db.scalar(
        select(
            func.max(RecognitionLog.similitud)
        )
    )

    minima = db.scalar(
        select(
            func.min(RecognitionLog.similitud)
        )
    )

    tasa_coincidencia = (
        coincidencias / total
        if total > 0
        else 0
    )

    return ProbabilityStatsResponse(
        total_reconocimientos=total,
        coincidencias=coincidencias,
        no_coincidencias=no_coincidencias,
        tasa_coincidencia=tasa_coincidencia,
        similitud_promedio=float(promedio or 0),
        similitud_maxima=(
            float(maxima)
            if maxima is not None
            else None
        ),
        similitud_minima=(
            float(minima)
            if minima is not None
            else None
        ),
    )


@router.post(
    "/prediccion",
    response_model=PredictionResponse
)
def calcular_prediccion(
    payload: PredictionRequest
):
    distancia = (
        payload.distancia
        if payload.distancia is not None
        else 1 - payload.similitud
    )

    probabilidad = probability_service.predict(
        similitud=payload.similitud,
        distancia=payload.distancia
    )

    return PredictionResponse(
        similitud=payload.similitud,
        distancia=distancia,
        probabilidad_calibrada=probabilidad,
        modelo_entrenado=probability_service.is_trained()
    )
