import { useCallback, useEffect, useRef, useState } from "react";
import Webcam from "react-webcam";
import { api } from "../services/api";
import type { LoginFacialResult } from "../types/facial";

type Paso = "dni" | "camara" | "resultado";

const BRILLO_BAJO = 80;
const BRILLO_ALTO = 205;

export default function LoginFacial() {
  const [paso, setPaso] = useState<Paso>("dni");
  const [dni, setDni] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const [resultado, setResultado] =
    useState<LoginFacialResult | null>(null);

  const [brillo, setBrillo] = useState<number | null>(null);

  const webcamRef = useRef<Webcam>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // ---------------------------------------------------------
  // Medición de iluminación en vivo: cada ~700ms toma un frame
  // pequeño del video y calcula el brillo promedio, para poder
  // avisarle a la persona si la luz no es suficiente ANTES de
  // intentar el reconocimiento (además del filtro que se aplica
  // en el servidor sobre la imagen ya capturada).
  // ---------------------------------------------------------
  useEffect(() => {
    if (paso !== "camara") {
      return;
    }

    const intervalo = setInterval(() => {
      const video = webcamRef.current?.video;
      const canvas = canvasRef.current;

      if (!video || !canvas || video.readyState < 2) {
        return;
      }

      canvas.width = 48;
      canvas.height = 36;

      const ctx = canvas.getContext("2d");

      if (!ctx) {
        return;
      }

      ctx.drawImage(video, 0, 0, 48, 36);

      const datos = ctx.getImageData(0, 0, 48, 36).data;

      let suma = 0;
      const totalPixeles = datos.length / 4;

      for (let i = 0; i < datos.length; i += 4) {
        suma += 0.299 * datos[i] + 0.587 * datos[i + 1] + 0.114 * datos[i + 2];
      }

      setBrillo(suma / totalPixeles);
    }, 700);

    return () => clearInterval(intervalo);
  }, [paso]);

  const continuarConDni = () => {
    if (!/^\d{8,12}$/.test(dni.trim())) {
      setError("Ingresa un DNI válido (8 a 12 dígitos).");
      return;
    }

    setError(null);
    setResultado(null);
    setPaso("camara");
  };

  const escanearRostro = useCallback(async () => {
    const imagen = webcamRef.current?.getScreenshot();

    if (!imagen) {
      setError("No se pudo capturar la imagen de la cámara.");
      return;
    }

    try {
      setCargando(true);
      setError(null);

      const blob = await fetch(imagen).then((res) => res.blob());

      const formData = new FormData();
      formData.append("dni", dni.trim());
      formData.append("file", blob, "login.jpg");

      const response = await api.post<LoginFacialResult>(
        "/login-facial",
        formData
      );

      setResultado(response.data);
      setPaso("resultado");
    } catch (error: any) {
      console.error(error);

      setError(
        error?.response?.data?.detail ||
          "No se pudo completar la verificación facial."
      );
    } finally {
      setCargando(false);
    }
  }, [dni]);

  const reiniciar = () => {
    setPaso("dni");
    setDni("");
    setError(null);
    setResultado(null);
    setBrillo(null);
  };

  const reintentarEscaneo = () => {
    setResultado(null);
    setError(null);
    setPaso("camara");
  };

  const iluminacionEstado =
    brillo === null
      ? null
      : brillo < BRILLO_BAJO
      ? "baja"
      : brillo > BRILLO_ALTO
      ? "alta"
      : "buena";

  return (
    <div className="page">
      <section className="page-heading">
        <div>
          <span className="eyebrow">ACCESO</span>
          <h1>Login Facial</h1>
          <p>
            Ingresa tu DNI y verifica tu identidad con un escaneo de
            rostro, comparado 1 a 1 contra tus datos ya registrados.
          </p>
        </div>
      </section>

      {paso === "dni" && (
        <div className="form-layout">
          <div className="dashboard-card">
            <span className="eyebrow">PASO 1</span>
            <h2>Ingresa tu DNI</h2>

            <div className="form-group">
              <label htmlFor="login-dni">DNI</label>
              <input
                id="login-dni"
                type="text"
                inputMode="numeric"
                maxLength={12}
                placeholder="Ej. 71234567"
                value={dni}
                onChange={(e) =>
                  setDni(e.target.value.replace(/\D/g, ""))
                }
                onKeyDown={(e) => {
                  if (e.key === "Enter") continuarConDni();
                }}
              />
            </div>

            {error && <p className="model-note">{error}</p>}

            <button className="primary-button" onClick={continuarConDni}>
              Continuar al escaneo facial
            </button>
          </div>

          <div className="dashboard-card">
            <span className="eyebrow">RECOMENDACIONES</span>
            <h2>Antes de escanear tu rostro</h2>

            <ul className="lighting-tips">
              <li>Ubícate frente a una fuente de luz, nunca de espaldas a ella.</li>
              <li>Evita contraluces (ventanas o lámparas detrás de ti).</li>
              <li>Retira lentes oscuros, gorras o mascarillas.</li>
              <li>Mantén el rostro centrado y a una distancia natural de la cámara.</li>
            </ul>
          </div>
        </div>
      )}

      {paso === "camara" && (
        <div className="dashboard-card camera-card">
          <div className="card-header">
            <div>
              <span className="eyebrow">PASO 2 · DNI {dni}</span>
              <h2>Escaneo facial</h2>
            </div>

            {iluminacionEstado && (
              <span
                className={`lighting-badge lighting-${iluminacionEstado}`}
              >
                {iluminacionEstado === "baja" && "⚠ Poca luz detectada"}
                {iluminacionEstado === "alta" && "⚠ Demasiada luz/reflejo"}
                {iluminacionEstado === "buena" && "✓ Iluminación adecuada"}
              </span>
            )}
          </div>

          <div className="camera-container">
            <Webcam
              ref={webcamRef}
              audio={false}
              screenshotFormat="image/jpeg"
              videoConstraints={{
                facingMode: "user",
                width: 480,
                height: 360,
              }}
            />
          </div>

          <canvas ref={canvasRef} style={{ display: "none" }} />

          {iluminacionEstado === "baja" && (
            <p className="model-note lighting-warning">
              La imagen se ve oscura. Acércate a una fuente de luz o
              enciende una luz frente a ti antes de escanear: el sistema
              aplica un filtro de realce, pero muy poca luz igual
              dificulta la detección del rostro.
            </p>
          )}

          {iluminacionEstado === "alta" && (
            <p className="model-note lighting-warning">
              Hay demasiada luz o un reflejo fuerte sobre tu rostro.
              Aléjate un poco de la fuente de luz directa.
            </p>
          )}

          {error && <p className="model-note">{error}</p>}

          <div className="verification-buttons">
            <button
              className="primary-button"
              disabled={cargando}
              onClick={() => void escanearRostro()}
            >
              {cargando ? "Verificando..." : "Escanear rostro"}
            </button>

            <button
              className="secondary-button"
              disabled={cargando}
              onClick={reiniciar}
            >
              Cambiar DNI
            </button>
          </div>
        </div>
      )}

      {paso === "resultado" && resultado && (
        <div
          className={
            resultado.coincide
              ? "recognition-result recognized"
              : "recognition-result unknown"
          }
        >
          <div className="result-icon">
            {resultado.coincide ? "✓" : "✕"}
          </div>

          <span className="result-label">
            {resultado.coincide ? "IDENTIDAD VERIFICADA" : "NO SE PUDO VERIFICAR"}
          </span>

          {resultado.coincide && resultado.persona && (
            <>
              <h2>{resultado.persona.nombre}</h2>
              <p className="model-note">
                DNI {resultado.persona.dni}
                {resultado.persona.email
                  ? ` · ${resultado.persona.email}`
                  : ""}
              </p>
            </>
          )}

          {!resultado.coincide && (
            <p className="model-note">{resultado.mensaje}</p>
          )}

          <div className="result-metrics">
            <div>
              <span>Similitud</span>
              <strong>
                {resultado.similitud !== null
                  ? `${(resultado.similitud * 100).toFixed(2)}%`
                  : "-"}
              </strong>
            </div>

            <div>
              <span>Umbral</span>
              <strong>{(resultado.umbral * 100).toFixed(2)}%</strong>
            </div>

            {resultado.probabilidad_calibrada !== null && (
              <div>
                <span>Probabilidad calibrada</span>
                <strong>
                  {(resultado.probabilidad_calibrada * 100).toFixed(2)}%
                </strong>
              </div>
            )}

            {resultado.iluminacion && (
              <div>
                <span>Iluminación</span>
                <strong>{resultado.iluminacion}</strong>
              </div>
            )}
          </div>

          <div className="verification-buttons">
            {!resultado.coincide && (
              <button className="primary-button" onClick={reintentarEscaneo}>
                Intentar de nuevo
              </button>
            )}

            <button className="secondary-button" onClick={reiniciar}>
              {resultado.coincide ? "Salir" : "Cambiar DNI"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
