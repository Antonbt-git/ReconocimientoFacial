from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.persona_model import Persona
from app.schemas.persona_schema import PersonaCreate, PersonaUpdate


def crear_persona(
    db: Session,
    datos: PersonaCreate
) -> Persona:

    persona = Persona(
        nombre=datos.nombre,
        dni=datos.dni,
        email=datos.email
    )

    db.add(persona)
    db.commit()
    db.refresh(persona)

    return persona


def obtener_personas(
    db: Session
) -> list[Persona]:

    resultado = db.execute(
        select(Persona)
        .order_by(Persona.id)
    )

    return list(resultado.scalars().all())


def obtener_persona(
    db: Session,
    persona_id: int
) -> Persona | None:

    return db.get(Persona, persona_id)


def obtener_persona_por_dni(
    db: Session,
    dni: str
) -> Persona | None:

    resultado = db.execute(
        select(Persona)
        .where(Persona.dni == dni.strip())
    )

    return resultado.scalars().first()


def actualizar_persona(
    db: Session,
    persona: Persona,
    datos: PersonaUpdate
) -> Persona:

    datos_actualizados = datos.model_dump(
        exclude_unset=True
    )

    for campo, valor in datos_actualizados.items():
        setattr(persona, campo, valor)

    db.commit()
    db.refresh(persona)

    return persona


def eliminar_persona(
    db: Session,
    persona: Persona
) -> None:

    db.delete(persona)
    db.commit()