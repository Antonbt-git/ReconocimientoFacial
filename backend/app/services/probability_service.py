"""
Servicio de Machine Learning para la calibración de probabilidades.

Corresponde a la sección 7 del documento técnico ("Machine Learning
aplicado al proyecto"): entrena un modelo sobre las comparaciones
históricas almacenadas en `recognition_logs` para estimar una
probabilidad calibrada de coincidencia, y expone las métricas de
evaluación recomendadas (precisión, recall, F1, matriz de confusión,
tasa de falsos positivos y tasa de falsos negativos).

Nota de diseño: como el esquema actual no registra una verificación
humana independiente ("resultado_real"), el modelo se entrena usando
`coincide` (la decisión del propio umbral) como etiqueta. Esto permite
demostrar el flujo completo de entrenamiento/calibración/evaluación
descrito en el documento. Para un entorno de producción real se
recomienda sustituir esa etiqueta por retroalimentación verificada
(por ejemplo, un campo de confirmación manual por un operador).
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

from app.models.recognition_log_model import RecognitionLog

MIN_SAMPLES_TO_TRAIN = 6
MIN_SAMPLES_FOR_HOLDOUT = 10
DEFAULT_THRESHOLD = 0.75

STORAGE_DIR = Path(__file__).resolve().parent.parent / "ml_models"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = STORAGE_DIR / "probability_model.joblib"
METRICS_PATH = STORAGE_DIR / "probability_metrics.json"


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
        registros = db.execute(select(RecognitionLog)).scalars().all()

        X: list[list[float]] = []
        y: list[int] = []

        for r in registros:
            distancia = r.distancia if r.distancia is not None else (1 - r.similitud)
            X.append([r.similitud, distancia])
            y.append(1 if r.coincide else 0)

        return np.array(X, dtype=np.float64), np.array(y, dtype=np.int64)

    def train(self, db: Session) -> dict[str, Any]:
        X, y = self._build_dataset(db)
        total = len(y)

        if total < MIN_SAMPLES_TO_TRAIN:
            raise ValueError(
                f"Se necesitan al menos {MIN_SAMPLES_TO_TRAIN} reconocimientos "
                f"registrados para entrenar el modelo (hay {total})."
            )

        if len(set(y.tolist())) < 2:
            raise ValueError(
                "El historial solo contiene un tipo de resultado (todo coincidencias "
                "o todo sin coincidencia). Se necesitan ejemplos de ambos casos para "
                "entrenar un clasificador."
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

    def predict(self, similitud: float, distancia: float | None = None) -> float:
        distancia_final = distancia if distancia is not None else (1 - similitud)

        if self.model is not None:
            proba = self.model.predict_proba([[similitud, distancia_final]])[0][1]
            return float(proba)

        # Sin modelo entrenado aún: heurística de respaldo, una sigmoide
        # centrada en el umbral por defecto, para que el sistema siga
        # devolviendo una probabilidad calibrada razonable.
        pendiente = 12.0
        proba = 1 / (1 + np.exp(-pendiente * (similitud - DEFAULT_THRESHOLD)))
        return float(np.clip(proba, 0.01, 0.99))

    def get_metrics(self) -> dict[str, Any] | None:
        return self.metrics

    def is_trained(self) -> bool:
        return self.model is not None

    def get_calibration_curve(self, pasos: int = 50) -> list[dict[str, float]]:
        """Muestrea la función de calibración a lo largo de todo el rango
        de similitud, para poder graficarla (sección 6 del documento:
        relación entre similitud y probabilidad calibrada)."""

        return [
            {
                "similitud": float(similitud),
                "probabilidad": self.predict(float(similitud)),
            }
            for similitud in np.linspace(0, 1, pasos)
        ]


probability_service = ProbabilityService()
