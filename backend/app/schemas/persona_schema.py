from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class PersonaCreate(BaseModel):
    nombre: str
    dni: str
    email: EmailStr | None = None

    @field_validator("dni")
    @classmethod
    def validar_dni(cls, valor: str) -> str:
        valor = valor.strip()

        if not valor.isdigit() or not (8 <= len(valor) <= 12):
            raise ValueError(
                "El DNI debe contener solo números "
                "(entre 8 y 12 dígitos)."
            )

        return valor


class PersonaUpdate(BaseModel):
    nombre: str | None = None
    dni: str | None = None
    email: EmailStr | None = None
    activo: bool | None = None


class PersonaResponse(BaseModel):
    id: int
    nombre: str
    dni: str | None
    email: str | None
    activo: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )