"""
Gestione dell'autenticazione per il servizio di logging.
"""

from fastapi import Depends, HTTPException, status, Security
from fastapi.security.api_key import APIKeyHeader
from typing import Dict, Optional
import os
import json
from datetime import datetime, timedelta

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEYS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "api_keys.json")

# Carica le API key dal file di configurazione
def load_api_keys() -> Dict[str, Dict]:
    """Carica le API key dal file di configurazione."""
    if not os.path.exists(API_KEYS_FILE):
        # Crea un file di configurazione di default se non esiste
        default_keys = {
            "server_key": {
                "name": "PramaIAServer",
                "key": "pramaiaserver_api_key_123456",
                "projects": ["PramaIAServer"],
                "expiry": None
            },
            "pdk_key": {
                "name": "PramaIA-PDK",
                "key": "pramaiapdk_api_key_123456",
                "projects": ["PramaIA-PDK"],
                "expiry": None
            },
            "agents_key": {
                "name": "PramaIA-Agents",
                "key": "pramaiaagents_api_key_123456",
                "projects": ["PramaIA-Agents"],
                "expiry": None
            },
            "admin_key": {
                "name": "Admin",
                "key": "pramaiaadmin_api_key_123456",
                "projects": ["PramaIAServer", "PramaIA-PDK", "PramaIA-Agents", "PramaIA-Plugins", "other"],
                "expiry": None
            }
        }
        
        # Assicurati che la directory config esista
        os.makedirs(os.path.dirname(API_KEYS_FILE), exist_ok=True)
        
        with open(API_KEYS_FILE, "w") as f:
            json.dump(default_keys, f, indent=4)
        
        return default_keys
    
    with open(API_KEYS_FILE, "r") as f:
        return json.load(f)

def get_api_key_info(api_key: str) -> Optional[Dict]:
    """Verifica e restituisce le informazioni sull'API key."""
    api_keys = load_api_keys()
    
    for key_id, key_info in api_keys.items():
        if key_info["key"] == api_key:
            # Verifica se la chiave è scaduta
            if key_info.get("expiry"):
                expiry_date = datetime.fromisoformat(key_info["expiry"])
                if datetime.now() > expiry_date:
                    return None
            
            return key_info
    
    return None

async def get_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """
    Dipendenza per verificare l'API key nelle richieste.
    
    Solleva un'eccezione HTTPException se l'API key è mancante o non valida.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key mancante"
        )
    
    key_info = get_api_key_info(api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key non valida o scaduta"
        )
    
    return api_key

def create_api_key(name: str, projects: list, expiry_days: Optional[int] = None) -> Dict:
    """
    Crea una nuova API key.
    
    Args:
        name: Nome dell'API key (di solito il nome del progetto o del client)
        projects: Lista dei progetti a cui l'API key ha accesso
        expiry_days: Giorni di validità della chiave (None per chiave senza scadenza)
        
    Returns:
        Dizionario con le informazioni sulla nuova API key
    """
    import uuid
    import string
    import random
    
    # Genera una chiave casuale
    key = f"pramaialog_{''.join(random.choices(string.ascii_lowercase + string.digits, k=16))}"
    
    # Calcola la data di scadenza se richiesta
    expiry = None
    if expiry_days:
        expiry = (datetime.now() + timedelta(days=expiry_days)).isoformat()
    
    # Crea le informazioni sulla chiave
    key_id = str(uuid.uuid4())
    key_info = {
        "name": name,
        "key": key,
        "projects": projects,
        "expiry": expiry,
        "created": datetime.now().isoformat()
    }
    
    # Salva la chiave
    api_keys = load_api_keys()
    api_keys[key_id] = key_info
    
    with open(API_KEYS_FILE, "w") as f:
        json.dump(api_keys, f, indent=4)
    
    return key_info
