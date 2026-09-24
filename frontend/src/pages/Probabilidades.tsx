import { useEffect, useState } from "react";
import { api } from "../services/api";
import ProbabilityChart from "../components/ProbabilityChart";
import type { CalibrationPoint } from "../types/facial";

interface ProbabilityStats {
  total_reconocimientos: number;
  coincidencias: number;
  no_coincidencias: number;
  tasa_coincidencia: number;
  similitud_promedio: number;
  similitud_maxima: number | null;
  similitud_minima: number | null;
}

interface ConfusionMatrix {
  verdaderos_positivos: number;
  falsos_positivos: number;
  verdaderos_negativos: number;
  falsos_negativos: number;
}

interface ModelMetrics {
  algoritmo: string;
  variables: string[];
  muestras_totales: number;
  muestras_evaluacion: number;
  evaluado_con_conjunto_independiente: boolean;
  precision: number;
  recall: number;
  f1: number;
  tasa_falsos_positivos: number;
  tasa_falsos_negativos: number;
  matriz_confusion: ConfusionMatrix;
  entrenado_en: string;
}

interface PredictionResult {
  similitud: number;
  distancia: number;
  probabilidad_calibrada: number;
  modelo_entrenado: boolean;
}

export default function Probabilidades() {
  const [stats, setStats] = useState<ProbabilityStats | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [metricas, setMetricas] = useState<ModelMetrics | null>(null);
  const [entrenando, setEntrenando] = useState(false);
  const [errorEntrenamiento, setErrorEntrenamiento] = useState<string | null>(null);

  const [similitud, setSimilitud] = useState(0.87);
  const [prediccion, setPrediccion] = useState<PredictionResult | null>(null);
  const [calculando, setCalculando] = useState(false);

  const [curva, setCurva] = useState<CalibrationPoint[]>([]);
  const [umbralCurva, setUmbralCurva] = useState(0.75);

  useEffect(() => {
    const cargarEstadisticas = async () => {
      try {
        setCargando(true);
        setError(null);

        const response = await api.get<ProbabilityStats>("/probabilidades");

        setStats(response.data);
      } catch (error) {
        console.error(error);

        setError("No se pudieron cargar las estadísticas.");
      } finally {
        setCargando(false);
      }
    };

    void cargarEstadisticas();
    void cargarMetricas();
    void cargarCurva();
  }, []);

  const cargarMetricas = async () => {
    try {
      const response = await api.get<ModelMetrics>("/modelos/metricas");

      setMetricas(response.data);
    } catch {
      // El modelo aún no ha sido entrenado (404): no es un error a mostrar.
      setMetricas(null);
    }
  };

  const cargarCurva = async () => {
    try {
      const response = await api.get<{
        puntos: CalibrationPoint[];
        umbral: number;
      }>("/probabilidades/curva");

      setCurva(response.data.puntos);
      setUmbralCurva(response.data.umbral);
    } catch (error) {
      console.error(error);
    }
  };

  const entrenarModelo = async () => {
    try {
      setEntrenando(true);
      setErrorEntrenamiento(null);

      const response = await api.post<ModelMetrics>("/modelos/entrenar");

      setMetricas(response.data);
      void cargarCurva();
    } catch (error) {
      console.error(error);

      const mensaje =
        (error as { response?: { data?: { detail?: string } } })?.response
          ?.data?.detail ?? "No se pudo entrenar el modelo.";

      setErrorEntrenamiento(mensaje);
    } finally {
      setEntrenando(false);
    }
  };

  const calcularProbabilidad = async () => {
    try {
      setCalculando(true);

      const response = await api.post<PredictionResult>(
        "/probabilidades/prediccion",
        { similitud }
      );

      setPrediccion(response.data);
    } catch (error) {
      console.error(error);
      alert("No se pudo calcular la probabilidad calibrada.");
    } finally {
      setCalculando(false);
    }
  };

  if (cargando) {
    return (
      <div className="page">
        <h1>Estadísticas</h1>
        <p>Cargando...</p>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="page">
        <h1>Estadísticas</h1>
        <p>{error ?? "No hay información disponible."}</p>
      </div>
    );
  }

  return (
    <div className="page">
      <section className="page-heading">
        <div>
          <span className="eyebrow">ANÁLISIS</span>

          <h1>Estadísticas de reconocimiento</h1>

          <p>Métricas obtenidas de los reconocimientos almacenados.</p>
        </div>
      </section>

      <div className="stats-grid">
        <div className="stat-card">
          <span className="eyebrow">RECONOCIMIENTOS</span>
          <h2>{stats.total_reconocimientos}</h2>
          <p>Total procesado</p>
        </div>

        <div className="stat-card">
          <span className="eyebrow">COINCIDENCIAS</span>
          <h2>{stats.coincidencias}</h2>
          <p>Rostros identificados</p>
        </div>

        <div className="stat-card">
          <span className="eyebrow">SIN COINCIDENCIA</span>
          <h2>{stats.no_coincidencias}</h2>
          <p>Rostros no identificados</p>
        </div>

        <div className="stat-card">
          <span className="eyebrow">TASA DE COINCIDENCIA</span>
          <h2>{(stats.tasa_coincidencia * 100).toFixed(1)}%</h2>
          <p>Sobre los registros actuales</p>
        </div>
      </div>

      <div className="dashboard-card">
        <span className="eyebrow">SIMILITUD FACIAL</span>
        <h2>Estadísticas del modelo de comparación</h2>

        <div className="metrics-grid">
          <div>
            <span>Promedio</span>
            <strong>{stats.similitud_promedio.toFixed(4)}</strong>
          </div>

          <div>
            <span>Máxima</span>
            <strong>
              {stats.similitud_maxima !== null
                ? stats.similitud_maxima.toFixed(4)
                : "-"}
            </strong>
          </div>

          <div>
            <span>Mínima</span>
            <strong>
              {stats.similitud_minima !== null
                ? stats.similitud_minima.toFixed(4)
                : "-"}
            </strong>
          </div>
        </div>
      </div>

      {/* Machine Learning aplicado al proyecto — sección 7 del documento */}
      <div className="dashboard-card">
        <div className="card-header">
          <div>
            <span className="eyebrow">MACHINE LEARNING</span>
            <h2>Calibración de probabilidades</h2>
          </div>

          <span className={`model-status ${metricas ? "trained" : "untrained"}`}>
            {metricas ? "Modelo entrenado" : "Modelo no entrenado"}
          </span>
        </div>

        <p style={{ color: "var(--text-soft)", fontSize: 12, marginTop: 4 }}>
          Un clasificador de {metricas?.algoritmo ?? "Regresión Logística"} se
          entrena sobre reconocimientos <strong>verificados</strong> desde el
          Historial o el módulo de Reconocimiento (similitud, distancia,
          calidad de imagen e iluminación) para estimar una probabilidad
          calibrada de coincidencia, en lugar de usar la similitud cruda como
          si fuera una probabilidad.
        </p>

        {metricas && (
          <>
            <div className="metrics-grid">
              <div>
                <span>Precisión</span>
                <strong>{(metricas.precision * 100).toFixed(1)}%</strong>
              </div>

              <div>
                <span>Recall</span>
                <strong>{(metricas.recall * 100).toFixed(1)}%</strong>
              </div>

              <div>
                <span>F1-score</span>
                <strong>{(metricas.f1 * 100).toFixed(1)}%</strong>
              </div>

              <div>
                <span>Muestras usadas</span>
                <strong>
                  {metricas.muestras_evaluacion} / {metricas.muestras_totales}
                </strong>
              </div>
            </div>

            <div className="confusion-grid">
              <div className="confusion-cell positive">
                <strong>{metricas.matriz_confusion.verdaderos_positivos}</strong>
                <span>Verdaderos positivos</span>
              </div>

              <div className="confusion-cell negative">
                <strong>{metricas.matriz_confusion.falsos_positivos}</strong>
                <span>Falsos positivos</span>
              </div>

              <div className="confusion-cell positive">
                <strong>{metricas.matriz_confusion.verdaderos_negativos}</strong>
                <span>Verdaderos negativos</span>
              </div>

              <div className="confusion-cell negative">
                <strong>{metricas.matriz_confusion.falsos_negativos}</strong>
                <span>Falsos negativos</span>
              </div>
            </div>

            <p className="model-note">
              Tasa de falsos positivos:{" "}
              {(metricas.tasa_falsos_positivos * 100).toFixed(1)}% · Tasa de
              falsos negativos: {(metricas.tasa_falsos_negativos * 100).toFixed(1)}%
              {!metricas.evaluado_con_conjunto_independiente &&
                " · El historial es pequeño, por lo que estas métricas se calcularon sobre el mismo conjunto de entrenamiento y son optimistas."}
              {" · Entrenado el "}
              {new Date(metricas.entrenado_en).toLocaleString()}
            </p>
          </>
        )}

        {!metricas && (
          <p className="model-note">
            Aún no se ha entrenado ningún modelo. Se necesitan al menos 6
            reconocimientos <strong>verificados</strong> (con ejemplos
            correctos e incorrectos), confirmándolos desde Reconocimiento o
            desde el Historial.
          </p>
        )}

        {errorEntrenamiento && (
          <p className="model-note" style={{ color: "var(--danger)" }}>
            {errorEntrenamiento}
          </p>
        )}

        <button
          className="primary-button"
          onClick={entrenarModelo}
          disabled={entrenando}
        >
          {entrenando
            ? "Entrenando..."
            : metricas
            ? "Reentrenar con historial actual"
            : "Entrenar modelo"}
        </button>
      </div>

      {/* Curva de calibración — relación similitud → probabilidad (sección 6) */}
      {curva.length > 0 && (
        <div className="dashboard-card">
          <span className="eyebrow">CURVA DE CALIBRACIÓN</span>
          <h2>Similitud vs. probabilidad calibrada</h2>

          <p style={{ color: "var(--text-soft)", fontSize: 12, marginTop: 4, marginBottom: 8 }}>
            {metricas
              ? "Salida del modelo entrenado a lo largo de todo el rango de similitud."
              : "Aún no hay modelo entrenado: se muestra la heurística de respaldo."}
          </p>

          <ProbabilityChart data={curva} umbral={umbralCurva} />
        </div>
      )}

      {/* Simulador de calibración — ejemplo de la sección 6 del documento */}
      <div className="dashboard-card">
        <span className="eyebrow">SIMULADOR</span>
        <h2>Calculadora de probabilidad calibrada</h2>

        <div className="simulator-layout">
          <div>
            <p style={{ color: "var(--text-soft)", fontSize: 12, marginTop: 4 }}>
              Ajusta la similitud coseno para ver qué probabilidad calibrada
              estimaría el modelo, sin necesidad de capturar un rostro.
            </p>

            <div className="form-group">
              <div className="range-value">
                <span>Similitud coseno</span>
                <strong>{similitud.toFixed(2)}</strong>
              </div>

              <input
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={similitud}
                onChange={(e) => setSimilitud(Number(e.target.value))}
              />
            </div>

            <button
              className="primary-button"
              onClick={calcularProbabilidad}
              disabled={calculando}
            >
              {calculando ? "Calculando..." : "Calcular probabilidad calibrada"}
            </button>
          </div>

          <div className="dashboard-card" style={{ boxShadow: "none" }}>
            {!prediccion ? (
              <div className="empty-simulator">
                <p style={{ color: "var(--text-soft)", fontSize: 12 }}>
                  El resultado aparecerá aquí.
                </p>
              </div>
            ) : (
              <>
                <span className="eyebrow">PROBABILIDAD CALIBRADA</span>

                <div className="probability-main">
                  <strong>
                    {(prediccion.probabilidad_calibrada * 100).toFixed(1)}
                  </strong>
                  <span>%</span>
                </div>

                <div className="probability-bar">
                  <span
                    style={{
                      width: `${prediccion.probabilidad_calibrada * 100}%`,
                    }}
                  />
                </div>

                <div className="probability-details">
                  <div>
                    <span>Similitud</span>
                    <strong>{prediccion.similitud.toFixed(2)}</strong>
                  </div>

                  <div>
                    <span>Distancia</span>
                    <strong>{prediccion.distancia.toFixed(2)}</strong>
                  </div>

                  <div>
                    <span>Fuente</span>
                    <strong className={prediccion.modelo_entrenado ? "text-success" : ""}>
                      {prediccion.modelo_entrenado ? "Modelo ML" : "Heurística"}
                    </strong>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
