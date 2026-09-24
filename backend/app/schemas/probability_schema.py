from pydantic import BaseModel, ConfigDict, Field


class ProbabilityStatsResponse(BaseModel):
    total_reconocimientos: int
    coincidencias: int
    no_coincidencias: int
    tasa_coincidencia: float
    similitud_promedio: float
    similitud_maxima: float | None
    similitud_minima: float | None


class PredictionRequest(BaseModel):
    similitud: float = Field(..., ge=0, le=1)
    distancia: float | None = Field(None, ge=0, le=1)
    calidad_imagen: str | None = None
    iluminacion: str | None = None


class PredictionResponse(BaseModel):
    similitud: float
    distancia: float
    probabilidad_calibrada: float
    modelo_entrenado: bool


class CalibrationPointResponse(BaseModel):
    similitud: float
    probabilidad: float


class CalibrationCurveResponse(BaseModel):
    puntos: list[CalibrationPointResponse]
    umbral: float
    modelo_entrenado: bool


class ConfusionMatrix(BaseModel):
    verdaderos_positivos: int
    falsos_positivos: int
    verdaderos_negativos: int
    falsos_negativos: int


class ModelMetricsResponse(BaseModel):
    algoritmo: str
    variables: list[str]
    muestras_totales: int
    muestras_evaluacion: int
    evaluado_con_conjunto_independiente: bool
    precision: float
    recall: float
    f1: float
    tasa_falsos_positivos: float
    tasa_falsos_negativos: float
    matriz_confusion: ConfusionMatrix
    entrenado_en: str


class VerificacionCreate(BaseModel):
    log_id: int
    resultado_real: bool


class TrainingRecordResponse(BaseModel):
    id: int
    similitud: float
    distancia: float | None
    calidad_imagen: str
    iluminacion: str
    resultado_real: bool

    model_config = ConfigDict(
        from_attributes=True
    )
