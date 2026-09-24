from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RecognitionHistoryResponse(BaseModel):
    id: int
    persona_id: int | None
    persona_nombre: str | None
    similitud: float
    distancia: float | None
    umbral: float
    coincide: bool
    probabilidad_calibrada: float | None
    calidad_imagen: str | None
    iluminacion: str | None
    verificado: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
