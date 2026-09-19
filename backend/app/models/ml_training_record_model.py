from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class MLTrainingRecord(Base):
    """
    Conjunto de datos etiquetado para entrenar el clasificador
    de Machine Learning descrito en el documento técnico
    (sección 7: "Machine Learning aplicado al proyecto").

    Cada fila representa una comparación facial ya evaluada,
    con su resultado real conocido (verdadero/falso), para que
    scikit-learn pueda aprender a estimar una probabilidad
    calibrada de coincidencia.
    """

    __tablename__ = "ml_training_records"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    similitud: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    distancia: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    calidad_imagen: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    iluminacion: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    resultado_real: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
