from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401 — registra todos los modelos en Base.metadata
from app.api.routes.health import router as health_router
from app.api.routes.history import router as history_router
from app.api.routes.models import router as models_router
from app.api.routes.personas import router as personas_router
from app.api.routes.probabilities import router as probabilities_router
from app.api.routes.recognition import router as recognition_router
from app.core.config import settings
from app.database.connection import Base, engine


app = FastAPI(
    title="Sistema Inteligente de Reconocimiento Facial",
    description="API para reconocimiento facial y análisis de probabilidades",
    version="1.0.0"
)


@app.on_event("startup")
def crear_tablas():
    # Crea las tablas que falten en la base de datos al arrancar.
    # No borra ni modifica tablas existentes: solo agrega las que no
    # estén, así que es seguro correrlo en cada despliegue.
    Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(personas_router)
app.include_router(recognition_router)
app.include_router(health_router)
app.include_router(history_router)
app.include_router(probabilities_router)
app.include_router(models_router)


@app.get("/")
def root():
    return {
        "message": "API de reconocimiento facial funcionando"
    }

