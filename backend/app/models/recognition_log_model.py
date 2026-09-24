from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class RecognitionLog(Base):
    __tablename__ = "recognition_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    persona_id: Mapped[int | None] = mapped_column(
        ForeignKey("personas.id", ondelete="SET NULL"),
        nullable=True
    )

    similitud: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    distancia: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    umbral: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    coincide: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )

    probabilidad_calibrada: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    # Variables estimadas automáticamente a partir de la imagen
    # (sección 7 del documento técnico), usadas como entrada del
    # modelo de ML y, una vez verificadas por un operador, copiadas a
    # "ml_training_records" para reentrenar el modelo.
    calidad_imagen: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    iluminacion: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    # Indica si un operador ya confirmó/corrigió este resultado y se
    # generó su correspondiente registro de entrenamiento etiquetado,
    # para no duplicarlo si se verifica dos veces.
    verificado: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )