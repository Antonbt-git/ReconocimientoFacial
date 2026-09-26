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

    def aplicar_filtro_iluminacion(
        self,
        image: np.ndarray
    ) -> np.ndarray:
        """
        Normaliza el contraste/iluminación de la imagen antes de la
        detección facial mediante CLAHE (Contrast Limited Adaptive
        Histogram Equalization) aplicado sobre el canal de luminancia
        (L de LAB). Esto es lo que pide el punto de "iluminación" del
        documento: ayuda a que el reconocimiento funcione en
        condiciones de poca luz, contraluz o sombras marcadas, sin
        alterar los colores originales de la imagen.
        """

        lab = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2LAB
        )

        canal_l, canal_a, canal_b = cv2.split(lab)

        clahe = cv2.createCLAHE(
            clipLimit=2.5,
            tileGridSize=(8, 8)
        )

        canal_l_realzado = clahe.apply(canal_l)

        lab_realzado = cv2.merge(
            (canal_l_realzado, canal_a, canal_b)
        )

        return cv2.cvtColor(
            lab_realzado,
            cv2.COLOR_LAB2BGR
        )

    def detect_faces(
        self,
        image: np.ndarray
    ) -> list[Any]:

        return self.model.get(image)

    def estimar_calidad(
        self,
        image: np.ndarray,
        face: Any
    ) -> dict:
        """Estima iluminación y nitidez a partir del recorte facial.

        Estas son justamente las variables "calidad_imagen" e
        "iluminacion" que pide la sección 7 del documento técnico como
        entrada del modelo de Machine Learning, además de la similitud.
        Se calculan de forma automática para no depender de que un
        operador las tipee a mano en cada reconocimiento.
        """

        x1, y1, x2, y2 = [
            int(coordenada)
            for coordenada in face.bbox
        ]

        x1, y1 = max(x1, 0), max(y1, 0)
        x2 = min(x2, image.shape[1])
        y2 = min(y2, image.shape[0])

        recorte = image[y1:y2, x1:x2]

        if recorte.size == 0:
            recorte = image

        gris = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)

        # Iluminación: brillo promedio del recorte facial (0-255).
        brillo = float(gris.mean())

        if brillo < 80:
            iluminacion = "Baja"
        elif brillo < 170:
            iluminacion = "Media"
        else:
            iluminacion = "Alta"

        # Calidad/nitidez: varianza del laplaciano. Valores bajos
        # indican una imagen borrosa o con poco detalle.
        nitidez = float(cv2.Laplacian(gris, cv2.CV_64F).var())

        if nitidez < 50:
            calidad_imagen = "Baja"
        elif nitidez < 150:
            calidad_imagen = "Media"
        else:
            calidad_imagen = "Alta"

        return {
            "calidad_imagen": calidad_imagen,
            "iluminacion": iluminacion,
            "brillo": brillo,
            "nitidez": nitidez,
        }

    def generate_embedding(
        self,
        image_bytes: bytes
    ) -> dict:

        image = self.image_to_array(
            image_bytes
        )

        # Primero se intenta detectar sobre una versión con el
        # contraste/iluminación normalizados (más robusta ante poca
        # luz o contraluz). Si por algún motivo no detecta nada, se
        # reintenta con la imagen original sin filtrar.
        imagen_realzada = self.aplicar_filtro_iluminacion(
            image
        )

        faces = self.detect_faces(
            imagen_realzada
        )

        if len(faces) == 0:
            faces = self.detect_faces(
                image
            )

        if len(faces) == 0:
            raise ValueError(
                "No se detectó ningún rostro. Verifica que haya "
                "buena iluminación y que el rostro esté centrado "
                "frente a la cámara."
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

        # La calidad/iluminación se mide siempre sobre la imagen
        # original (sin el filtro), para que refleje la condición
        # real de captura y sirva como dato honesto de entrenamiento.
        calidad = self.estimar_calidad(image, face)

        return {
            "embedding": embedding.astype(
                np.float32
            ).tolist(),

            "det_score": float(
                face.det_score
            ),

            "bbox": face.bbox.tolist(),

            "calidad_imagen": calidad["calidad_imagen"],
            "iluminacion": calidad["iluminacion"],
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