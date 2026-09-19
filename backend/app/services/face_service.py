import json
from typing import Any

import cv2
import numpy as np
from insightface.app import FaceAnalysis

from app.core.config import settings


class FaceService:

    def __init__(self):
        # "buffalo_l" pesa ~281MB de descarga y, junto al resto del
        # proceso (FastAPI, OpenCV, onnxruntime), excede los 512Mi del
        # plan gratuito de Render incluso antes de terminar de cargar
        # (el crash ocurre justo tras descargar el zip completo, sin
        # importar qué submodelos se usen después). "buffalo_sc" es un
        # paquete de detección + reconocimiento mucho más liviano
        # (~16MB) pensado para entornos con poca memoria/CPU.
        #
        # IMPORTANTE: al cambiar de paquete cambia también el modelo de
        # reconocimiento (y el tamaño del embedding que genera). Los
        # rostros ya registrados con "buffalo_l" quedan incompatibles
        # y deben volver a registrarse; `compare_embeddings` lo detecta
        # y lanza un error explícito en vez de comparar embeddings de
        # tamaños distintos.
        self.model = FaceAnalysis(
            name=settings.INSIGHTFACE_MODEL_PACK,
            allowed_modules=["detection", "recognition"]
        )

        self.model.prepare(
            ctx_id=0,
            det_size=(320, 320)
        )

    def image_to_array(
        self,
        image_bytes: bytes
    ) -> np.ndarray:

        image_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8
        )

        image = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        if image is None:
            raise ValueError(
                "No se pudo leer la imagen"
            )

        return image

    def detect_faces(
        self,
        image: np.ndarray
    ) -> list[Any]:

        return self.model.get(image)

    def generate_embedding(
        self,
        image_bytes: bytes
    ) -> dict:

        image = self.image_to_array(
            image_bytes
        )

        faces = self.detect_faces(
            image
        )

        if len(faces) == 0:
            raise ValueError(
                "No se detectó ningún rostro"
            )

        if len(faces) > 1:
            raise ValueError(
                "La imagen debe contener un solo rostro"
            )

        face = faces[0]

        embedding = face.embedding

        if embedding is None:
            raise ValueError(
                "No se pudo generar el embedding facial"
            )

        return {
            "embedding": embedding.astype(
                np.float32
            ).tolist(),

            "det_score": float(
                face.det_score
            ),

            "bbox": face.bbox.tolist()
        }

    def compare_embeddings(
        self,
        embedding_1: list[float],
        embedding_2: list[float]
    ) -> dict:

        vector_1 = np.array(
            embedding_1,
            dtype=np.float32
        )

        vector_2 = np.array(
            embedding_2,
            dtype=np.float32
        )

        if vector_1.shape != vector_2.shape:
            raise ValueError(
                f"Los embeddings tienen dimensiones diferentes: "
                f"{vector_1.shape} y {vector_2.shape}"
            )

        norm_1 = np.linalg.norm(vector_1)
        norm_2 = np.linalg.norm(vector_2)

        if norm_1 == 0 or norm_2 == 0:
            raise ValueError(
                "Uno de los embeddings no es válido"
            )

        similarity = float(
            np.dot(vector_1, vector_2)
            / (norm_1 * norm_2)
        )

        distance = float(
            1 - similarity
        )

        return {
            "similarity": similarity,
            "distance": distance
        }
    
    @staticmethod
    def embedding_to_json(
        embedding: list[float]
    ) -> str:

        return json.dumps(
            embedding
        )

    @staticmethod
    def json_to_embedding(
        embedding: str
    ) -> list[float]:

        return json.loads(
            embedding
        )


face_service = FaceService()