import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.face_embedding_model import FaceEmbedding
from app.models.persona_model import Persona
from app.models.recognition_log_model import RecognitionLog
from app.services.face_service import face_service
from app.services.probability_service import probability_service

DEFAULT_THRESHOLD = 0.75


def reconocer_persona(
    db: Session,
    image_bytes: bytes,
    threshold: float = DEFAULT_THRESHOLD
):

    # ---------------------------------------------------------
    # 1. Generar embedding de la imagen recibida
    # ---------------------------------------------------------

    result = face_service.generate_embedding(
        image_bytes
    )

    query = (
        select(
            FaceEmbedding,
            Persona
        )
        .join(
            Persona,
            Persona.id == FaceEmbedding.persona_id
        )
        .where(
            Persona.activo == True
        )
    )

    registros = db.execute(query).all()

    if not registros:
        raise ValueError(
            "No existen embeddings registrados"
        )

    mejor_resultado = None

    # ---------------------------------------------------------
    # 2. Comparar contra los embeddings registrados
    # ---------------------------------------------------------

    for face_embedding, persona in registros:

        embedding_registrado = json.loads(
            face_embedding.embedding
        )

        comparacion = face_service.compare_embeddings(
            result["embedding"],
            embedding_registrado
        )

        if (
            mejor_resultado is None
            or comparacion["similarity"]
            > mejor_resultado["similitud"]
        ):

            mejor_resultado = {
                "persona_id": persona.id,
                "nombre": persona.nombre,
                "similitud": comparacion["similarity"],
                "distancia": comparacion["distance"]
            }

    # ---------------------------------------------------------
    # 3. Aplicar umbral y registrar log
    # ---------------------------------------------------------

    coincide = (
        mejor_resultado["similitud"]
        >= threshold
    )

    # ---------------------------------------------------------
    # 4. Calibrar la probabilidad con el modelo de ML
    #    (sección 6 y 7 del documento técnico)
    # ---------------------------------------------------------

    probabilidad_calibrada = probability_service.predict(
        similitud=mejor_resultado["similitud"],
        distancia=mejor_resultado["distancia"],
        calidad_imagen=result["calidad_imagen"],
        iluminacion=result["iluminacion"]
    )

    log = RecognitionLog(
        persona_id=mejor_resultado["persona_id"] if coincide else None,
        similitud=mejor_resultado["similitud"],
        distancia=mejor_resultado["distancia"],
        umbral=threshold,
        coincide=coincide,
        probabilidad_calibrada=probabilidad_calibrada,
        calidad_imagen=result["calidad_imagen"],
        iluminacion=result["iluminacion"]
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return {
        "success": True,
        "log_id": log.id,
        "persona_id": (
            mejor_resultado["persona_id"]
            if coincide
            else None
        ),
        "nombre": (
            mejor_resultado["nombre"]
            if coincide
            else None
        ),
        "similitud": mejor_resultado["similitud"],
        "distancia": mejor_resultado["distancia"],
        "umbral": threshold,
        "coincide": coincide,
        "probabilidad_calibrada": probabilidad_calibrada,
        "calidad_imagen": result["calidad_imagen"],
        "iluminacion": result["iluminacion"],
        "det_score": result["det_score"]
    }