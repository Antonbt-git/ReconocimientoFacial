from pydantic import BaseModel, ConfigDict


class PersonaIdentificada(BaseModel):
    id: int
    nombre: str
    dni: str | None
    email: str | None

    model_config = ConfigDict(
        from_attributes=True
    )


class LoginFacialResponse(BaseModel):
    success: bool
    coincide: bool
    persona: PersonaIdentificada | None
    similitud: float | None
    distancia: float | None
    umbral: float
    probabilidad_calibrada: float | None
    calidad_imagen: str | None
    iluminacion: str | None
    mensaje: str
