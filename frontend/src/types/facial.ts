export interface RecognitionResult {
  success: boolean;
  log_id: number;
  persona_id: number | null;
  nombre: string | null;
  similitud: number | null;
  distancia: number | null;
  umbral: number;
  coincide: boolean;
  probabilidad_calibrada: number | null;
  calidad_imagen: string | null;
  iluminacion: string | null;
  det_score: number;
}

export interface CalibrationPoint {
  similitud: number;
  probabilidad: number;
}

export interface CalibrationCurveResponse {
  puntos: CalibrationPoint[];
  umbral: number;
  modelo_entrenado: boolean;
}