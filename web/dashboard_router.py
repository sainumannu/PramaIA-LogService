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

@dashboard_router.get("/logservice", response_class=HTMLResponse)
async def dashboard_logservice(
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """
    Pagina dedicata al servizio di logging.
    
    Mostra informazioni sul servizio, client attivi, chiavi API e guide all'integrazione.
    """
    # Ottieni informazioni sullo stato del servizio
    uptime = datetime.now() - log_manager.start_time if hasattr(log_manager, 'start_time') else "N/A"
    uptime_str = str(uptime).split('.')[0] if isinstance(uptime, timedelta) else uptime
    
    # Dati di stato del servizio
    service_status = {
        "is_running": True,
        "uptime": uptime_str,
        "active_connections": 3,
        "total_connections": 15,
        "logs_received_today": log_manager.get_logs_count(
            start_date=datetime.now() - timedelta(days=1)
        ),
        "db_size": log_manager.get_db_size(),
        "total_logs": log_manager.get_logs_count()
    }
    
    # Client attivi (dati di esempio)
    active_clients = [
        {
            "id": "client-001",
            "project": "PramaIAServer",
            "module": "workflow_service",
            "last_log_time": "2023-10-18 14:32:10",
            "logs_sent": 1254,
            "status": "online"
        },
        {
            "id": "client-002",
            "project": "PramaIA-PDK",
            "module": "pdk-core",
            "last_log_time": "2023-10-18 14:30:45",
            "logs_sent": 873,
            "status": "online"
        },
        {
            "id": "client-003",
            "project": "PramaIA-Agents",
            "module": "pdf-monitor-agent",
            "last_log_time": "2023-10-18 13:45:20",
            "logs_sent": 421,
            "status": "idle"
        }
    ]
    
    # Chiavi API (dati di esempio)
    api_keys = [
        {
            "name": "PramaIAServer API Key",
            "key_masked": "pramaiaserver_api_key_******",
            "project": "PramaIAServer",
            "created_at": "2023-09-15 10:00:00",
            "last_used": "2023-10-18 14:32:10"
        },
        {
            "name": "PDK API Key",
            "key_masked": "pdk_api_key_******",
            "project": "PramaIA-PDK",
            "created_at": "2023-09-15 10:05:00",
            "last_used": "2023-10-18 14:30:45"
        },
        {
            "name": "Agents API Key",
            "key_masked": "agents_api_key_******",
            "project": "PramaIA-Agents",
            "created_at": "2023-09-15 10:10:00",
            "last_used": "2023-10-18 13:45:20"
        }
    ]
    
    return templates.TemplateResponse(
        "logservice.html",
        {
            "request": request,
            "title": "LogService - PramaIA LogService",
            "status": service_status,
            "clients": active_clients,
            "api_keys": api_keys
        }
    )
