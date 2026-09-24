from sqlalchemy.orm import Session

from app.models.ml_training_record_model import MLTrainingRecord
from app.models.recognition_log_model import RecognitionLog


def verificar_reconocimiento(
    db: Session,
    log_id: int,
    resultado_real: bool
) -> MLTrainingRecord:
    """Convierte un intento de reconocimiento ya registrado en un dato
    de entrenamiento etiquetado, a partir de la confirmación de un
    operador (sección 15 del documento: ninguna decisión importante
    debería basarse únicamente en la similitud automática).

    Es la pieza que conecta el Historial con `ml_training_records`:
    sin esto, esa tabla existía en el modelo de datos pero nunca se
    llenaba.
    """

    log = db.get(RecognitionLog, log_id)

    if log is None:
        raise ValueError("El reconocimiento indicado no existe")

    if log.verificado:
        raise ValueError("Este reconocimiento ya fue verificado antes")

    registro = MLTrainingRecord(
        similitud=log.similitud,
        distancia=log.distancia,
        calidad_imagen=log.calidad_imagen or "Media",
        iluminacion=log.iluminacion or "Media",
        resultado_real=resultado_real
    )

    log.verificado = True

    db.add(registro)
    db.add(log)
    db.commit()
    db.refresh(registro)

    return registro


def contar_verificados(db: Session) -> int:
    return db.query(MLTrainingRecord).count()
