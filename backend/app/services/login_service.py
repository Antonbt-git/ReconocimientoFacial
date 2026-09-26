import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.face_embedding_model import FaceEmbedding
from app.models.persona_model import Persona
from app.models.recognition_log_model import RecognitionLog
from app.services.face_service import face_service
from app.services.persona_service import obtener_persona_por_dni
from app.services.probability_service import probability_service
from app.services.recognition_service import DEFAULT_THRESHOLD


def login_facial(
    db: Session,
    dni: str,
    image_bytes: bytes,
    threshold: float = DEFAULT_THRESHOLD
) -> dict:
    """
    Verificación facial 1:1 (a diferencia del reconocimiento abierto
    de /api/reconocimiento, que compara 1:N contra toda la base).

    El flujo es: la persona ingresa su DNI, el sistema recupera
    ÚNICAMENTE los embeddings registrados para ese DNI, y compara el
    rostro capturado solo contra esa identidad reclamada. Esto es más
    seguro y más rápido que comparar contra toda la base de personas.
    """

    persona = obtener_persona_por_dni(db, dni)

    if persona is None:
        raise ValueError(
            "No existe ninguna persona registrada con ese DNI."
        )

    if not persona.activo:
        raise ValueError(
            "Este registro se encuentra inactivo. "
            "Contacta al administrador."
        )

    embeddings_registrados = list(
        db.execute(
            select(FaceEmbedding)
            .where(FaceEmbedding.persona_id == persona.id)
        ).scalars().all()
    )

    if not embeddings_registrados:
        raise ValueError(
            "Esta persona todavía no tiene un rostro registrado "
            "en el sistema. Debe completar el Registro Facial primero."
        )

    # ---------------------------------------------------------
    # 1. Generar el embedding de la captura recibida
    # ---------------------------------------------------------

    result = face_service.generate_embedding(
        image_bytes
    )

    # ---------------------------------------------------------
    # 2. Comparar contra cada rostro registrado de ESA persona
    #    y quedarse con la mejor similitud
    # ---------------------------------------------------------

    mejor_similitud = None
    mejor_distancia = None

    for face_embedding in embeddings_registrados:

        embedding_registrado = json.loads(
            face_embedding.embedding
        )

        try:
            comparacion = face_service.compare_embeddings(
                result["embedding"],
                embedding_registrado
            )
        except ValueError:
            # Embedding generado con un modelo distinto (por
            # ejemplo, tras un cambio de INSIGHTFACE_MODEL_PACK).
            continue

        if (
            mejor_similitud is None
            or comparacion["similarity"] > mejor_similitud
        ):
            mejor_similitud = comparacion["similarity"]
            mejor_distancia = comparacion["distance"]

    if mejor_similitud is None:
        raise ValueError(
            "No se pudo comparar el rostro capturado con los "
            "datos biométricos registrados para este DNI."
        )

    coincide = mejor_similitud >= threshold

    # ---------------------------------------------------------
    # 3. Calibrar la probabilidad (secciones 6 y 7 del documento)
    # ---------------------------------------------------------

    probabilidad_calibrada = probability_service.predict(
        similitud=mejor_similitud,
        distancia=mejor_distancia,
        calidad_imagen=result["calidad_imagen"],
        iluminacion=result["iluminacion"]
    )

    # ---------------------------------------------------------
    # 4. Registrar el intento en el historial/auditoría
    # ---------------------------------------------------------

    log = RecognitionLog(
        persona_id=persona.id,
        similitud=mejor_similitud,
        distancia=mejor_distancia,
        umbral=threshold,
        coincide=coincide,
        probabilidad_calibrada=probabilidad_calibrada,
        calidad_imagen=result["calidad_imagen"],
        iluminacion=result["iluminacion"]
    )
    db.add(log)
    db.commit()

    return {
        "success": True,
        "coincide": coincide,
        "persona": persona if coincide else None,
        "similitud": mejor_similitud,
        "distancia": mejor_distancia,
        "umbral": threshold,
        "probabilidad_calibrada": probabilidad_calibrada,
        "calidad_imagen": result["calidad_imagen"],
        "iluminacion": result["iluminacion"],
        "mensaje": (
            f"Identidad verificada correctamente: {persona.nombre}."
            if coincide
            else "El rostro capturado no coincide con el DNI ingresado."
        )
    }
