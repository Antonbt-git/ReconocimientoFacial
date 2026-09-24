"""
Servicio de Machine Learning para la calibración de probabilidades.

Corresponde a la sección 7 del documento técnico ("Machine Learning
aplicado al proyecto"): entrena un modelo sobre datos verificados de
`ml_training_records` para estimar una probabilidad calibrada de
coincidencia a partir de similitud, distancia, calidad de imagen e
iluminación, y expone las métricas de evaluación recomendadas
(precisión, recall, F1, matriz de confusión, tasa de falsos positivos
y tasa de falsos negativos).

A diferencia de una versión anterior de este servicio, la etiqueta de
entrenamiento ya NO es la propia decisión de umbral (`coincide`), sino
`resultado_real`: un valor confirmado por un operador humano desde el
Historial (sección 15: ninguna decisión importante debería basarse
únicamente en la similitud automática). Esto evita que el modelo
simplemente aprenda a reproducir el umbral que ya usa el sistema.
"""

import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ml_training_record_model import MLTrainingRecord

MIN_SAMPLES_TO_TRAIN = 6
MIN_SAMPLES_FOR_HOLDOUT = 10
DEFAULT_THRESHOLD = 0.75

# Codificación ordinal de las variables categóricas del documento
# (sección 7: "similitud, iluminación, calidad de imagen, distancia").
NIVELES = {"Baja": 0.0, "Media": 0.5, "Alta": 1.0}
NIVEL_POR_DEFECTO = "Media"

STORAGE_DIR = Path(__file__).resolve().parent.parent / "ml_models"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = STORAGE_DIR / "probability_model.joblib"
METRICS_PATH = STORAGE_DIR / "probability_metrics.json"


def _codificar_nivel(valor: str | None) -> float:
    return NIVELES.get(valor or NIVEL_POR_DEFECTO, NIVELES[NIVEL_POR_DEFECTO])


class ProbabilityService:
    def __init__(self) -> None:
        self.model: LogisticRegression | None = None
        self.metrics: dict[str, Any] | None = None
        self._load_from_disk()

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def _load_from_disk(self) -> None:
        if MODEL_PATH.exists():
            try:
                self.model = joblib.load(MODEL_PATH)
            except Exception:
                self.model = None

        if METRICS_PATH.exists():
            try:
                self.metrics = json.loads(METRICS_PATH.read_text())
            except Exception:
                self.metrics = None

    def _persist(self) -> None:
        if self.model is not None:
            joblib.dump(self.model, MODEL_PATH)
        if self.metrics is not None:
            METRICS_PATH.write_text(json.dumps(self.metrics))

    # ------------------------------------------------------------------
    # Entrenamiento
    # ------------------------------------------------------------------

    def _build_dataset(self, db: Session) -> tuple[np.ndarray, np.ndarray]:
        registros = db.execute(select(MLTrainingRecord)).scalars().all()

        X: list[list[float]] = []
        y: list[int] = []

        for r in registros:
            distancia = r.distancia if r.distancia is not None else (1 - r.similitud)

            X.append([
                r.similitud,
                distancia,
                _codificar_nivel(r.calidad_imagen),
                _codificar_nivel(r.iluminacion),
            ])
            y.append(1 if r.resultado_real else 0)

        return np.array(X, dtype=np.float64), np.array(y, dtype=np.int64)

    def train(self, db: Session) -> dict[str, Any]:
        X, y = self._build_dataset(db)
        total = len(y)

        if total < MIN_SAMPLES_TO_TRAIN:
            raise ValueError(
                f"Se necesitan al menos {MIN_SAMPLES_TO_TRAIN} reconocimientos "
                f"verificados para entrenar el modelo (hay {total}). Confirmá "
                f"resultados desde el Historial para generarlos."
            )

        if len(set(y.tolist())) < 2:
            raise ValueError(
                "Los registros verificados solo contienen un tipo de resultado "
                "(todo correcto o todo incorrecto). Se necesitan ejemplos de "
                "ambos casos para entrenar un clasificador."
            )

        usa_holdout = total >= MIN_SAMPLES_FOR_HOLDOUT

        if usa_holdout:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.25, random_state=42, stratify=y
            )
        else:
            # Dataset pequeño: se entrena y evalúa sobre el mismo conjunto,
            # dejando claro en la respuesta que las métricas son optimistas.
            X_train, X_test, y_train, y_test = X, X, y, y

        modelo = LogisticRegression(class_weight="balanced")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ConvergenceWarning)
            modelo.fit(X_train, y_train)

        y_pred = modelo.predict(X_test)

        tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()

        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        tasa_falsos_positivos = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        tasa_falsos_negativos = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        self.model = modelo
        self.metrics = {
            "algoritmo": "Regresión Logística",
            "variables": ["similitud", "distancia", "calidad_imagen", "iluminacion"],
            "muestras_totales": total,
            "muestras_evaluacion": len(y_test),
            "evaluado_con_conjunto_independiente": usa_holdout,
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "tasa_falsos_positivos": float(tasa_falsos_positivos),
            "tasa_falsos_negativos": float(tasa_falsos_negativos),
            "matriz_confusion": {
                "verdaderos_positivos": int(tp),
                "falsos_positivos": int(fp),
                "verdaderos_negativos": int(tn),
                "falsos_negativos": int(fn),
            },
            "entrenado_en": datetime.utcnow().isoformat() + "Z",
        }

        self._persist()

        return self.metrics

    # ------------------------------------------------------------------
    # Predicción
    # ------------------------------------------------------------------

    def predict(
        self,
        similitud: float,
        distancia: float | None = None,
        calidad_imagen: str | None = None,
        iluminacion: str | None = None,
    ) -> float:
        distancia_final = distancia if distancia is not None else (1 - similitud)

        if self.model is not None:
            vector = [[
                similitud,
                distancia_final,
                _codificar_nivel(calidad_imagen),
                _codificar_nivel(iluminacion),
            ]]
            proba = self.model.predict_proba(vector)[0][1]
            return float(proba)

        # Sin modelo entrenado aún: heurística de respaldo, una sigmoide
        # centrada en el umbral por defecto, para que el sistema siga
        # devolviendo una probabilidad calibrada razonable. Se ajusta
        # levemente según calidad/iluminación mientras no haya modelo.
        pendiente = 12.0
        ajuste = (
            (_codificar_nivel(calidad_imagen) - 0.5) * 0.05
            + (_codificar_nivel(iluminacion) - 0.5) * 0.05
        )
        proba = 1 / (1 + np.exp(-pendiente * (similitud - DEFAULT_THRESHOLD))) + ajuste
        return float(np.clip(proba, 0.01, 0.99))

    def get_metrics(self) -> dict[str, Any] | None:
        return self.metrics

    def is_trained(self) -> bool:
        return self.model is not None

    def get_calibration_curve(
        self,
        pasos: int = 50,
        calidad_imagen: str = "Alta",
        iluminacion: str = "Alta",
    ) -> list[dict[str, float]]:
        """Muestrea la función de calibración a lo largo de todo el rango
        de similitud, para poder graficarla (sección 6 del documento:
        relación entre similitud y probabilidad calibrada). Se fija
        calidad/iluminación en "Alta" (mejor caso) por defecto."""

        return [
            {
                "similitud": float(similitud),
                "probabilidad": self.predict(
                    float(similitud),
                    calidad_imagen=calidad_imagen,
                    iluminacion=iluminacion,
                ),
            }
            for similitud in np.linspace(0, 1, pasos)
        ]


probability_service = ProbabilityService()
