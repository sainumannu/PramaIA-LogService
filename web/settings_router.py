"""
Router per le impostazioni del servizio.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Any, List, Optional
import os
import json
from pydantic import BaseModel
from datetime import datetime

from core.auth import get_api_key, create_api_key
from core.config import get_settings, update_settings
from core.models import LogProject

router = settings_router = APIRouter()

class ApiKeyCreate(BaseModel):
    name: str
    projects: List[str]
    expiry_days: Optional[int] = None

class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key: str
    projects: List[str]
    expiry: Optional[str] = None
    created_at: str

@router.get("/api-keys", response_model=List[Dict[str, Any]])
async def list_api_keys(
    api_key: str = Depends(get_api_key)
):
    """
    Lista delle API keys disponibili.
    
    Richiede un API key valido per l'autenticazione.
    """
    from core.auth import load_api_keys
    
    api_keys_data = load_api_keys()
    
    result = []
    for key_id, key_info in api_keys_data.items():
        if isinstance(key_info, dict):
            result.append({
                "id": key_id,
                "name": key_info.get("name", ""),
                "key_masked": mask_api_key(key_info.get("key", "")),
                "projects": key_info.get("projects", []),
                "expiry": key_info.get("expiry"),
                "created_at": key_info.get("created", datetime.now().isoformat())
            })
        else:
            # Formato legacy
            result.append({
                "id": key_id,
                "name": key_id,
                "key_masked": mask_api_key(key_info),
                "projects": [key_id],
                "expiry": None,
                "created_at": "N/A"
            })
    
    return result

@router.post("/api-keys", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_new_api_key(
    key_data: ApiKeyCreate = Body(...),
    admin_api_key: str = Depends(get_api_key)
):
    """
    Crea una nuova API key.
    
    Richiede un API key valido per l'autenticazione.
    """
    import uuid
    
    # Verifica che i progetti siano validi
    for project in key_data.projects:
        try:
            LogProject(project)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Progetto non valido: {project}"
            )
    
    key_info = create_api_key(
        name=key_data.name,
        projects=key_data.projects,
        expiry_days=key_data.expiry_days
    )
    
    # Trova l'ID della chiave appena creata
    from core.auth import load_api_keys
    api_keys = load_api_keys()
    key_id = None
    for id, info in api_keys.items():
        if isinstance(info, dict) and info.get("key") == key_info["key"]:
            key_id = id
            break
    
    if not key_id:
        key_id = str(uuid.uuid4())
    
    return {
        "id": key_id,
        "name": key_info["name"],
        "key": key_info["key"],
        "projects": key_info["projects"],
        "expiry": key_info.get("expiry"),
        "created_at": key_info.get("created", datetime.now().isoformat())
    }

@router.delete("/api-keys/{key_id}", status_code=status.HTTP_200_OK)
async def delete_api_key(
    key_id: str,
    admin_api_key: str = Depends(get_api_key)
):
    """
    Elimina una API key esistente.
    
    Richiede un API key valido per l'autenticazione.
    """
    api_keys_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "api_keys.json")
    
    if not os.path.exists(api_keys_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File delle API keys non trovato"
        )
    
    # Carica le API keys
    with open(api_keys_path, "r") as f:
        api_keys = json.load(f)
    
    # Verifica che la chiave esista
    if key_id not in api_keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key con ID {key_id} non trovata"
        )
    
    # Salva il nome prima di eliminare
    key_name = api_keys[key_id].get("name", key_id) if isinstance(api_keys[key_id], dict) else key_id
    
    # Elimina la chiave
    del api_keys[key_id]
    
    # Salva le modifiche
    with open(api_keys_path, "w") as f:
        json.dump(api_keys, f, indent=4)
    
    return {"message": f"API key '{key_name}' eliminata con successo"}

@router.post("/api-keys/{key_id}/regenerate", status_code=status.HTTP_200_OK)
async def regenerate_api_key(
    key_id: str,
    admin_api_key: str = Depends(get_api_key)
):
    """
    Rigenera una API key esistente.
    
    Richiede un API key valido per l'autenticazione.
    """
    import random
    import string
    
    api_keys_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "api_keys.json")
    
    if not os.path.exists(api_keys_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File delle API keys non trovato"
        )
    
    # Carica le API keys
    with open(api_keys_path, "r") as f:
        api_keys = json.load(f)
    
    # Verifica che la chiave esista
    if key_id not in api_keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key con ID {key_id} non trovata"
        )
    
    # Estrai le informazioni sulla chiave
    key_info = api_keys[key_id]
    
    if isinstance(key_info, str):
        # Formato legacy
        name = key_id
        projects = [key_id]
        
        # Genera una nuova chiave
        new_key = f"pramaialog_{''.join(random.choices(string.ascii_lowercase + string.digits, k=16))}"
        
        # Aggiorna con il formato nuovo
        api_keys[key_id] = {
            "name": name,
            "key": new_key,
            "projects": projects,
            "created": datetime.now().isoformat(),
            "expiry": None
        }
    else:
        # Formato nuovo
        # Genera una nuova chiave
        new_key = f"pramaialog_{''.join(random.choices(string.ascii_lowercase + string.digits, k=16))}"
        
        # Aggiorna la chiave
        key_info["key"] = new_key
        key_info["regenerated"] = datetime.now().isoformat()
        
        api_keys[key_id] = key_info
    
    # Salva le modifiche
    with open(api_keys_path, "w") as f:
        json.dump(api_keys, f, indent=4)
    
    # Preparazione della risposta
    name = key_info["name"] if isinstance(key_info, dict) else key_id
    key_masked = mask_api_key(new_key)
    
    return {
        "id": key_id,
        "name": name,
        "key": new_key,
        "key_masked": key_masked,
        "message": f"API key '{name}' rigenerata con successo"
    }

@router.post("/retention", status_code=status.HTTP_200_OK)
async def update_retention_settings(
    settings_update: Dict[str, Any] = Body(...),
    api_key: str = Depends(get_api_key)
):
    """
    Aggiorna le impostazioni di conservazione dei log.
    
    Richiede un API key valido per l'autenticazione.
    """
    current_settings = get_settings().dict()
    
    # Aggiorna solo i campi specificati
    for key, value in settings_update.items():
        if key in current_settings:
            current_settings[key] = value
    
    # Aggiorna le impostazioni
    success = update_settings(current_settings)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'aggiornamento delle impostazioni"
        )
    
    return {"message": "Impostazioni aggiornate con successo"}

def mask_api_key(api_key: str) -> str:
    """Maschera una API key per la visualizzazione sicura."""
    if not api_key:
        return "N/A"
    
    if len(api_key) <= 8:
        return f"{api_key[:2]}{'*' * (len(api_key) - 2)}"
    
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"
