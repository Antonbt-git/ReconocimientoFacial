import axios from "axios";

// En desarrollo local apunta al backend local por defecto.
// En producción, definir VITE_API_URL en el archivo .env (o en las
// variables de entorno del servicio de hosting del frontend) con la
// URL pública del backend, por ejemplo:
// VITE_API_URL=https://reconocimientofacial-backend.onrender.com/api
const baseURL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api";

export const api = axios.create({
  baseURL,
});
