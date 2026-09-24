from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.persona_model import Persona
from app.models.recognition_log_model import RecognitionLog
from app.schemas.history_schema import RecognitionHistoryResponse


router = APIRouter(
    prefix="/api/historial",
    tags=["Historial"]
)


@router.get(
    "",
    response_model=list[RecognitionHistoryResponse]
)
def get_historial(
    db: Session = Depends(get_db)
):
    query = (
        select(
            RecognitionLog.id,
            RecognitionLog.persona_id,
            Persona.nombre.label("persona_nombre"),
            RecognitionLog.similitud,
            RecognitionLog.distancia,
            RecognitionLog.umbral,
            RecognitionLog.coincide,
            RecognitionLog.probabilidad_calibrada,
            RecognitionLog.calidad_imagen,
            RecognitionLog.iluminacion,
            RecognitionLog.verificado,
            RecognitionLog.created_at,
        )
        .outerjoin(
            Persona,
            Persona.id == RecognitionLog.persona_id
        )
        .order_by(
            RecognitionLog.created_at.desc()
        )
    )

    resultado = db.execute(query).mappings().all()

    return list(resultado)

