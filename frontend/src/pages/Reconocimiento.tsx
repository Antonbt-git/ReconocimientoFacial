import { useState } from "react";
import CameraCapture from "../components/CameraCapture";
import { api } from "../services/api";
import type { RecognitionResult } from "../types/facial";

export default function Reconocimiento() {
const [resultado, setResultado] =
useState<RecognitionResult | null>(null);

const [cargando, setCargando] = useState(false);
const [verificando, setVerificando] = useState(false);
const [verificado, setVerificado] = useState(false);

const reconocer = async (image: string) => {
try {
setCargando(true);
setResultado(null);
setVerificado(false);


  const blob = await fetch(image).then((res) =>
    res.blob()
  );

  const formData = new FormData();

  formData.append(
    "file",
    blob,
    "captura.jpg"
  );

  const response = await api.post<RecognitionResult>(
    "/reconocimiento",
    formData
  );

  setResultado(response.data);
} catch (error) {
  console.error(error);
  alert("No se pudo realizar el reconocimiento");
} finally {
  setCargando(false);
}


};

const verificar = async (resultado_real: boolean) => {
  if (!resultado) return;

  try {
    setVerificando(true);

    await api.post("/modelos/verificaciones", {
      log_id: resultado.log_id,
      resultado_real,
    });

    setVerificado(true);
  } catch (error) {
    console.error(error);
    alert("No se pudo registrar la verificación.");
  } finally {
    setVerificando(false);
  }
};

return ( <div className="page"> <section className="page-heading"> <div> <span className="eyebrow">
INTELIGENCIA ARTIFICIAL </span>

      <h1>Reconocimiento Facial</h1>

      <p>
        Identificación facial en tiempo real.
      </p>
    </div>

    <div className="system-badge">
      <span />
      Cámara activa
    </div>
  </section>

  <div className="recognition-layout">
    <div className="dashboard-card camera-card">
      <div className="card-header">
        <div>
          <span className="eyebrow">
            CÁMARA
          </span>

          <h2>Captura en tiempo real</h2>
        </div>

        {cargando && (
          <span className="processing-badge">
            Analizando...
          </span>
        )}
      </div>

      <div className="camera-container">
        <CameraCapture onCapture={reconocer} />
      </div>
    </div>

    <div className="dashboard-card result-card">
      <span className="eyebrow">
        RESULTADO
      </span>

      {!resultado && !cargando && (
        <div className="empty-result">
          <div className="empty-icon">
            ◎
          </div>

          <h2>Esperando rostro</h2>

          <p>
            Colócate frente a la cámara para
            comenzar el reconocimiento.
          </p>
        </div>
      )}

      {cargando && (
        <div className="empty-result">
          <div className="loading-spinner" />

          <h2>Analizando rostro</h2>

          <p>
            InsightFace está procesando la captura.
          </p>
        </div>
      )}

      {resultado && !cargando && (
        <div
          className={
            resultado.coincide
              ? "recognition-result recognized"
              : "recognition-result unknown"
          }
        >
          <div className="result-icon">
            {resultado.coincide ? "✓" : "?"}
          </div>

          <span className="result-label">
            {resultado.coincide
              ? "PERSONA RECONOCIDA"
              : "SIN COINCIDENCIA"}
          </span>

          {resultado.coincide && (
            <h2>{resultado.nombre}</h2>
          )}

          <div className="result-metrics">
            <div>
              <span>Similitud</span>

              <strong>
                {resultado.similitud !== null
                  ? `${(
                      resultado.similitud * 100
                    ).toFixed(2)}%`
                  : "-"}
              </strong>
            </div>

            <div>
              <span>Umbral</span>

              <strong>
                {(
                  resultado.umbral * 100
                ).toFixed(2)}%
              </strong>
            </div>

            {resultado.probabilidad_calibrada !== null && (
              <div>
                <span>Probabilidad calibrada</span>

                <strong>
                  {(
                    resultado.probabilidad_calibrada * 100
                  ).toFixed(2)}%
                </strong>
              </div>
            )}

            {resultado.calidad_imagen && (
              <div>
                <span>Calidad de imagen</span>
                <strong>{resultado.calidad_imagen}</strong>
              </div>
            )}

            {resultado.iluminacion && (
              <div>
                <span>Iluminación</span>
                <strong>{resultado.iluminacion}</strong>
              </div>
            )}
          </div>

          <div className="verification-actions">
            {verificado ? (
              <p className="model-note">
                Gracias, se guardó como dato de entrenamiento.
              </p>
            ) : (
              <>
                <p className="model-note">
                  ¿Este resultado fue correcto? Tu confirmación
                  se usa para entrenar el modelo de probabilidades.
                </p>

                <div className="verification-buttons">
                  <button
                    className="primary-button"
                    disabled={verificando}
                    onClick={() => verificar(true)}
                  >
                    Sí, es correcto
                  </button>

                  <button
                    className="secondary-button"
                    disabled={verificando}
                    onClick={() => verificar(false)}
                  >
                    No es correcto
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  </div>
</div>


);
}
