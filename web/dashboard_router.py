"""
Router per la dashboard web del servizio di logging.
"""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from datetime import datetime, timedelta
from typing import Optional

from core.auth import get_api_key
from core.models import LogLevel, LogProject
from core.log_manager import LogManager

# Inizializza il router
router = dashboard_router = APIRouter()

# Inizializza il gestore dei template
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "templates")
templates = Jinja2Templates(directory=templates_dir)

# Inizializza il gestore dei log
log_manager = LogManager()

@dashboard_router.get("/", response_class=HTMLResponse)
async def dashboard_home(
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """
    Pagina principale della dashboard.
    
    Mostra una panoramica dei log recenti e statistiche generali.
    """
    # Ottieni statistiche recenti
    stats = log_manager.get_stats()
    
    # Ottieni log recenti (ultimi 100)
    recent_logs = log_manager.get_logs(limit=100)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "logs": recent_logs,
            "title": "Dashboard PramaIA LogService"
        }
    )

@dashboard_router.get("/search", response_class=HTMLResponse)
async def dashboard_search(
    request: Request,
    project: Optional[str] = None,
    level: Optional[str] = None,
    module: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    api_key: str = Depends(get_api_key)
):
    """
    Pagina di ricerca dei log.
    
    Permette di filtrare i log in base a diversi criteri.
    """
    # Converti parametri in tipi appropriati
    project_enum = LogProject(project) if project else None
    level_enum = LogLevel(level) if level else None
    
    start_datetime = None
    if start_date:
        try:
            start_datetime = datetime.fromisoformat(start_date)
        except ValueError:
            start_datetime = None
    
    end_datetime = None
    if end_date:
        try:
            end_datetime = datetime.fromisoformat(end_date)
        except ValueError:
            end_datetime = None
    
    # Ottieni log filtrati
    logs = log_manager.get_logs(
        project=project_enum,
        level=level_enum,
        module=module,
        start_date=start_datetime,
        end_date=end_datetime,
        limit=limit,
        offset=offset
    )
    
    # Calcola pagination
    total_logs = len(logs)  # Questo è una semplificazione, in realtà dovremmo contare tutti i log che corrispondono al filtro
    
    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "logs": logs,
            "total": total_logs,
            "limit": limit,
            "offset": offset,
            "project": project,
            "level": level,
            "module": module,
            "start_date": start_date,
            "end_date": end_date,
            "title": "Ricerca Log - PramaIA LogService"
        }
    )

@dashboard_router.get("/stats", response_class=HTMLResponse)
async def dashboard_stats(
    request: Request,
    project: Optional[str] = None,
    days: int = 7,
    api_key: str = Depends(get_api_key)
):
    """
    Pagina di statistiche dei log.
    
    Mostra grafici e statistiche aggregate sui log.
    """
    # Converti parametri in tipi appropriati
    project_enum = LogProject(project) if project else None
    
    # Calcola date per il periodo richiesto
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Ottieni statistiche
    stats = log_manager.get_stats(
        project=project_enum,
        start_date=start_date,
        end_date=end_date
    )
    
    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "stats": stats,
            "project": project,
            "days": days,
            "title": "Statistiche Log - PramaIA LogService"
        }
    )

@dashboard_router.get("/settings", response_class=HTMLResponse)
async def dashboard_settings(
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """
    Pagina di configurazione del servizio.
    
    Permette di visualizzare e modificare le impostazioni del servizio.
    """
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "title": "Impostazioni - PramaIA LogService"
        }
    )
