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
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from api.log_router import router as log_router
from core.config import get_settings, configure_service_logging
from core.maintenance import get_maintenance_scheduler
from web.settings_router import settings_router
from web.search_router import search_router

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
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
app.include_router(search_router, prefix="/dashboard", tags=["search"])


@app.get("/dashboard")
async def dashboard_root():
    """Compatibilità: reindirizza /dashboard -> /dashboard/ (pagina di ricerca)."""
    return RedirectResponse(url="/dashboard/")

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "web", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Endpoint radice che reindirizza alla pagina di ricerca."""
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>PramaIA LogService</title>
                    <meta http-equiv="refresh" content="0;url=/dashboard/">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <h1>PramaIA LogService</h1>
            <p>Reindirizzamento alla pagina di ricerca...</p>
            <p>Se non vieni reindirizzato automaticamente, <a href="/dashboard/">clicca qui</a>.</p>
        </body>
    </html>
    """
    return html_content

@app.get("/health")
async def health_check():
    """Endpoint per il controllo dello stato del servizio."""
    return {"status": "ok", "version": app.version}

@app.post("/maintenance")
async def trigger_maintenance():
    """Endpoint per avviare manualmente la manutenzione."""
    from core.log_manager import LogManager
    
    log_manager = LogManager()
    
    # Esegui la manutenzione
    compressed = 0
    if get_settings().enable_log_compression:
        compressed = log_manager.compress_old_logs(days_threshold=get_settings().compress_logs_older_than_days)
    
    deleted = log_manager.cleanup_logs(days_to_keep=get_settings().retention_days)
    
    archived = 0
    if get_settings().enable_log_compression:
        archived = log_manager.cleanup_compressed_logs(days_to_keep=get_settings().compressed_logs_retention_days)
    
    return {
        "success": True,
        "details": {
            "compressed_logs": compressed,
            "deleted_logs": deleted,
            "archived_logs": archived
        }
    }

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
    
    # Avvia lo scheduler di manutenzione
    maintenance_scheduler = get_maintenance_scheduler()
    maintenance_scheduler.start()
    
    # Avvia il server
    uvicorn.run(
        "main:app", 
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
