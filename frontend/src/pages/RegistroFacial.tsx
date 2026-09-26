import { useState } from "react";
import CameraCapture from "../components/CameraCapture";
import { api } from "../services/api";

interface PersonaResponse {
  id: number;
  nombre: string;
  dni: string | null;
  email: string | null;
  activo: boolean;
  created_at: string;
}

interface EmbeddingResponse {
  persona_id: number;
  modelo: string;
  det_score: number;
  embedding_dimension: number;
}

export default function RegistroFacial() {
  const [nombre, setNombre] = useState("");
  const [dni, setDni] = useState("");
  const [email, setEmail] = useState("");

  const [persona, setPersona] =
    useState<PersonaResponse | null>(null);

  const [embedding, setEmbedding] =
    useState<EmbeddingResponse | null>(null);

  const [cargandoPersona, setCargandoPersona] =
    useState(false);

  const [cargandoRostro, setCargandoRostro] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const registrarPersona = async () => {
    if (!nombre.trim()) {
      setError("El nombre es obligatorio.");
      return;
    }

    if (!/^\d{8,12}$/.test(dni.trim())) {
      setError("El DNI debe tener entre 8 y 12 dígitos numéricos.");
      return;
    }

    try {
      setError(null);
      setEmbedding(null);
      setCargandoPersona(true);

      const response = await api.post<PersonaResponse>(
        "/personas",
        {
          nombre: nombre.trim(),
          dni: dni.trim(),
          email: email.trim() || null,
        }
      );

      setPersona(response.data);
    } catch (error: any) {
      console.error(error);

      setError(
        error?.response?.data?.detail ||
          "No se pudo registrar la persona."
      );
    } finally {
      setCargandoPersona(false);
    }
  };

  const registrarRostro = async (image: string) => {
    if (!persona) {
      setError(
        "Primero debes registrar la persona."
      );
      return;
    }

    try {
      setError(null);
      setCargandoRostro(true);

      const blob = await fetch(image).then((res) =>
        res.blob()
      );

      const formData = new FormData();

      formData.append(
        "file",
        blob,
        "rostro.jpg"
      );

      const response =
        await api.post<EmbeddingResponse>(
          `/personas/${persona.id}/rostro`,
          formData
        );

      setEmbedding(response.data);
    } catch (error: any) {
      console.error(error);

      setError(
        error?.response?.data?.detail ||
          "No se pudo registrar el rostro."
      );
    } finally {
      setCargandoRostro(false);
    }
  };

  const reiniciarRegistro = () => {
    setNombre("");
    setDni("");
    setEmail("");
    setPersona(null);
    setEmbedding(null);
    setError(null);
  };

  return (
    <div className="page">
      <section className="page-heading">
        <div>
          <span className="eyebrow">
            GESTIÓN BIOMÉTRICA
          </span>

          <h1>Registro Facial</h1>

          <p>
            Registra una persona y captura su rostro
            para generar el embedding facial.
          </p>
        </div>
      </section>

      {error && (
        <div className="dashboard-card">
          <p>{error}</p>
        </div>
      )}

      <div className="form-layout">
        <div className="dashboard-card">
          <span className="eyebrow">
            DATOS PERSONALES
          </span>

          <h2>Información</h2>

          <div className="form-group">
            <label htmlFor="nombre">
              Nombre completo
            </label>

            <input
              id="nombre"
              type="text"
              placeholder="Ingrese el nombre"
              value={nombre}
              onChange={(event) =>
                setNombre(event.target.value)
              }
              disabled={!!persona}
            />
          </div>

          <div className="form-group">
            <label htmlFor="dni">
              DNI
            </label>

            <input
              id="dni"
              type="text"
              inputMode="numeric"
              maxLength={12}
              placeholder="Ingrese el DNI"
              value={dni}
              onChange={(event) =>
                setDni(event.target.value.replace(/\D/g, ""))
              }
              disabled={!!persona}
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">
              Email
            </label>

            <input
              id="email"
              type="email"
              placeholder="Ingrese el email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              disabled={!!persona}
            />
          </div>

          {!persona && (
            <button
              className="primary-button"
              onClick={registrarPersona}
              disabled={cargandoPersona}
            >
              {cargandoPersona
                ? "Registrando..."
                : "Registrar persona"}
            </button>
          )}

          {persona && !embedding && (
            <div>
              <p>
                Persona registrada correctamente.
              </p>

              <p>
                ID de persona: {persona.id}
              </p>
            </div>
          )}

          {embedding && (
            <div>
              <p>
                ✓ Registro facial completado
              </p>

              <p>
                Persona: {persona?.nombre}
              </p>

              <p>
                Modelo: {embedding.modelo}
              </p>

              <p>
                Dimensión:{" "}
                {embedding.embedding_dimension}
              </p>

              <p>
                Detección facial:{" "}
                {(embedding.det_score * 100).toFixed(1)}%
              </p>

              <button
                className="secondary-button"
                onClick={reiniciarRegistro}
              >
                Registrar otra persona
              </button>
            </div>
          )}
        </div>

        <div className="dashboard-card">
          <span className="eyebrow">
            CAPTURA BIOMÉTRICA
          </span>

          <h2>Captura facial</h2>

          {!persona && (
            <p>
              Primero registra los datos de la
              persona para habilitar la captura
              facial.
            </p>
          )}

          {persona && !embedding && (
            <>
              <p>
                Persona registrada. Ahora captura
                el rostro frente a la cámara.
              </p>

              <CameraCapture
                onCapture={registrarRostro}
                autoCapture={false}
              />

              {cargandoRostro && (
                <p>
                  Generando embedding facial...
                </p>
              )}
            </>
          )}

          {embedding && (
            <p>
              Rostro registrado correctamente en
              el sistema.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

