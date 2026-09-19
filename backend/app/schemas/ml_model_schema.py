from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------
# Predicción de probabilidad calibrada (sección 6 del doc.)
# ---------------------------------------------------------

class PredictionRequest(BaseModel):
    similitud: float
    distancia: float | None = None
    umbral: float = 0.75


class PredictionResponse(BaseModel):
    similitud: float
    distancia: float | None
    umbral: float
    coincide: bool
    probabilidad_calibrada: float
    confianza: str


class CalibrationPoint(BaseModel):
    similitud: float
    probabilidad: float


# ---------------------------------------------------------
# Entrenamiento ML (sección 7 y 8 del documento técnico)
# ---------------------------------------------------------

class TrainingRecordCreate(BaseModel):
    similitud: float
    distancia: float | None = None
    calidad_imagen: str
    iluminacion: str
    resultado_real: bool


class TrainingRecordResponse(TrainingRecordCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ConfusionMatrix(BaseModel):
    verdaderos_positivos: int
    falsos_positivos: int
    verdaderos_negativos: int
    falsos_negativos: int


class TrainingMetricsResponse(BaseModel):
    entrenado: bool
    total_registros: int
    registros_entrenamiento: int
    registros_prueba: int
    precision: float | None
    recall: float | None
    f1_score: float | None
    tasa_falsos_positivos: float | None
    tasa_falsos_negativos: float | None
    matriz_confusion: ConfusionMatrix | None
    trained_at: datetime | None
    mensaje: str | None = None
