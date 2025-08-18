"""
Modulo principale del servizio di logging PramaIA.
Avvia il server FastAPI e configura le route dell'API.
"""

import os
import logging
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

from api.log_router import router as log_router
from core.config import get_settings, configure_service_logging
from web.dashboard_router import dashboard_router

# Configurazione del logger di sistema
logger = configure_service_logging()

# Creazione dell'app FastAPI
app = FastAPI(
    title="PramaIA LogService",
    description="Servizio centralizzato di logging per l'ecosistema PramaIA",
    version="1.0.0"
)

# Configurazione CORS
settings = get_settings()
origins = settings.cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusione dei router
app.include_router(log_router, prefix="/api/logs", tags=["logs"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "web", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Endpoint radice che reindirizza alla documentazione."""
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>PramaIA LogService</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <h1>PramaIA LogService</h1>
            <p>Servizio centralizzato di logging per i componenti PramaIA</p>
            <p>Visita <a href="/docs">la documentazione</a> per ulteriori informazioni sulle API.</p>
        </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Endpoint per il controllo dello stato del servizio."""
    return {"status": "ok", "version": app.version}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Gestione globale delle eccezioni.
    """
    logger.error(f"Errore non gestito: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Si è verificato un errore interno."}
    )

if __name__ == "__main__":
    # Assicurati che le directory necessarie esistano
    os.makedirs("logs", exist_ok=True)
    
    # Avvia il server
    uvicorn.run(
        "main:app", 
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
