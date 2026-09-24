import { useEffect, useState } from "react";
import { api } from "../services/api";

interface RecognitionHistory {
  id: number;
  persona_id: number | null;
  persona_nombre: string | null;
  similitud: number;
  distancia: number | null;
  umbral: number;
  coincide: boolean;
  probabilidad_calibrada: number | null;
  calidad_imagen: string | null;
  iluminacion: string | null;
  verificado: boolean;
  created_at: string;
}

export default function Historial() {
  const [historial, setHistorial] =
    useState<RecognitionHistory[]>([]);

  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [verificandoId, setVerificandoId] = useState<number | null>(null);

  useEffect(() => {
    const cargarHistorial = async () => {
      try {
        setCargando(true);
        setError(null);

        const response =
          await api.get<RecognitionHistory[]>(
            "/historial"
          );

        setHistorial(response.data);
      } catch (error) {
        console.error(error);

        setError(
          "No se pudo cargar el historial."
        );
      } finally {
        setCargando(false);
      }
    };

    void cargarHistorial();
  }, []);

  const verificar = async (id: number, resultado_real: boolean) => {
    try {
      setVerificandoId(id);

      await api.post("/modelos/verificaciones", {
        log_id: id,
        resultado_real,
      });

      setHistorial((actual) =>
        actual.map((registro) =>
          registro.id === id
            ? { ...registro, verificado: true }
            : registro
        )
      );
    } catch (error) {
      console.error(error);
      alert("No se pudo registrar la verificación.");
    } finally {
      setVerificandoId(null);
    }
  };

  return (
    <div className="page">
      <section className="page-heading">
        <div>
          <span className="eyebrow">
            AUDITORÍA
          </span>

          <h1>Historial</h1>

          <p>
            Registro de reconocimientos realizados
            por el sistema. Confirmá si cada resultado fue correcto
            para generar datos de entrenamiento para el modelo de
            probabilidades.
          </p>
        </div>
      </section>

      <div className="dashboard-card">
        {cargando && (
          <p>
            Cargando historial...
          </p>
        )}

        {error && (
          <p>
            {error}
          </p>
        )}

        {!cargando &&
          !error &&
          historial.length === 0 && (
            <p>
              No existen reconocimientos registrados.
            </p>
          )}

        {!cargando &&
          !error &&
          historial.length > 0 && (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Persona</th>
                    <th>Resultado</th>
                    <th>Similitud</th>
                    <th>Probabilidad</th>
                    <th>Calidad</th>
                    <th>Iluminación</th>
                    <th>¿Fue correcto?</th>
                  </tr>
                </thead>

                <tbody>
                  {historial.map((registro) => (
                    <tr key={registro.id}>
                      <td>
                        {new Date(
                          registro.created_at
                        ).toLocaleString()}
                      </td>

                      <td>
                        {registro.persona_nombre ??
                          "No identificada"}
                      </td>

                      <td>
                        <span
                          className={`table-status ${
                            registro.coincide ? "success" : "warning"
                          }`}
                        >
                          {registro.coincide
                            ? "Coincidencia"
                            : "Sin coincidencia"}
                        </span>
                      </td>

                      <td>
                        {registro.similitud.toFixed(4)}
                      </td>

                      <td>
                        {registro.probabilidad_calibrada !== null
                          ? `${(
                              registro.probabilidad_calibrada * 100
                            ).toFixed(1)}%`
                          : "-"}
                      </td>

                      <td>{registro.calidad_imagen ?? "-"}</td>
                      <td>{registro.iluminacion ?? "-"}</td>

                      <td>
                        {registro.verificado ? (
                          <span className="table-status success">
                            Verificado
                          </span>
                        ) : (
                          <div className="verification-buttons">
                            <button
                              className="primary-button"
                              disabled={verificandoId === registro.id}
                              onClick={() => verificar(registro.id, true)}
                            >
                              Sí
                            </button>

                            <button
                              className="secondary-button"
                              disabled={verificandoId === registro.id}
                              onClick={() => verificar(registro.id, false)}
                            >
                              No
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </div>
    </div>
  );
}
