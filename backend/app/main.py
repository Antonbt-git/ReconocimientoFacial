from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.history import router as history_router
from app.api.routes.models import router as models_router
from app.api.routes.personas import router as personas_router
from app.api.routes.probabilities import router as probabilities_router
from app.api.routes.recognition import router as recognition_router


app = FastAPI(
    title="Sistema Inteligente de Reconocimiento Facial",
    description="API para reconocimiento facial y análisis de probabilidades",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
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

