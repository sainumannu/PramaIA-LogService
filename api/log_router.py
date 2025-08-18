"""
Router per le API di logging.
Definisce gli endpoint per l'invio e la gestione dei log.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from core.models import LogEntry, LogLevel, LogProject
from core.log_manager import LogManager
from core.auth import get_api_key

router = APIRouter()
log_manager = LogManager()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_log(
    log_entry: LogEntry = Body(...),
    api_key: str = Depends(get_api_key)
):
    """
    Crea una nuova voce di log.
    
    Richiede un API key valido per l'autenticazione.
    """
    log_id = log_manager.add_log(log_entry)
    return {"id": log_id, "message": "Log registrato con successo"}

@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def create_logs_batch(
    log_entries: List[LogEntry] = Body(...),
    api_key: str = Depends(get_api_key)
):
    """
    Crea multiple voci di log in un'unica richiesta.
    
    Utile per l'invio di log in batch in caso di connessione intermittente.
    Richiede un API key valido per l'autenticazione.
    """
    log_ids = log_manager.add_logs_batch(log_entries)
    return {"ids": log_ids, "count": len(log_ids), "message": "Logs registrati con successo"}

@router.get("/", response_model=List[Dict[str, Any]])
async def get_logs(
    project: Optional[LogProject] = None,
    level: Optional[LogLevel] = None,
    module: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
    api_key: str = Depends(get_api_key)
):
    """
    Recupera le voci di log in base ai filtri specificati.
    
    Richiede un API key valido per l'autenticazione.
    """
    logs = log_manager.get_logs(
        project=project,
        level=level,
        module=module,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    return logs

@router.get("/stats")
async def get_log_stats(
    project: Optional[LogProject] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    api_key: str = Depends(get_api_key)
):
    """
    Recupera statistiche sui log.
    
    Richiede un API key valido per l'autenticazione.
    """
    stats = log_manager.get_stats(
        project=project,
        start_date=start_date,
        end_date=end_date
    )
    return stats

@router.delete("/cleanup")
async def cleanup_logs(
    days_to_keep: int = 30,
    project: Optional[LogProject] = None,
    level: Optional[LogLevel] = None,
    api_key: str = Depends(get_api_key)
):
    """
    Pulisce i log più vecchi di un certo numero di giorni.
    
    Richiede un API key valido per l'autenticazione.
    """
    deleted_count = log_manager.cleanup_logs(
        days_to_keep=days_to_keep,
        project=project,
        level=level
    )
    return {"deleted_count": deleted_count, "message": f"Eliminati {deleted_count} log"}
