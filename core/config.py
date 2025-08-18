"""
Configurazione del servizio di logging.
"""

import os
from typing import Dict, Any, Optional, List

# Gestione della migrazione da pydantic v1 a v2
try:
    # Prova prima con pydantic-settings (pydantic v2+)
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        # Fallback a pydantic v1
        from pydantic import BaseSettings
    except ImportError:
        raise ImportError(
            "Manca la dipendenza 'pydantic-settings'. Installa con: pip install pydantic-settings"
        )

class LogServiceSettings(BaseSettings):
    """
    Impostazioni per il servizio di logging.
    
    Queste impostazioni possono essere sovrascritte utilizzando variabili d'ambiente
    con prefisso PRAMAIALOG_ (es. PRAMAIALOG_HOST=0.0.0.0).
    """
    # Configurazione del server
    host: str = "127.0.0.1"
    port: int = 8081
    debug: bool = False
    log_level: str = "info"
    
    # Configurazione del database
    db_path: Optional[str] = None  # Se None, usa il percorso predefinito in LogManager
    
    # Configurazione di sicurezza
    enable_api_key_auth: bool = True
    enable_cors: bool = True
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:5173"
    ]
    
    # Limiti
    max_log_batch_size: int = 100
    max_logs_per_request: int = 1000
    retention_days: int = 90
    
    # Configurazione dell'interfaccia web
    web_dashboard_enabled: bool = True
    
    # Configurazione dei client
    client_auto_retry: bool = True
    client_retry_max_attempts: int = 3
    client_retry_delay: int = 1  # secondi
    
    # Configurazione Pydantic con supporto per v1 e v2
    model_config = {
        "env_prefix": "PRAMAIALOG_",
        "env_file": ".env"
    }
    
    # Per compatibilità con Pydantic v1
    class Config:
        env_prefix = "PRAMAIALOG_"
        env_file = ".env"

def get_settings() -> LogServiceSettings:
    """
    Ottiene le impostazioni del servizio.
    
    Returns:
        LogServiceSettings
    """
    return LogServiceSettings()

# Ottieni configurazione per log del servizio stesso
def configure_service_logging():
    """
    Configura il logging per il servizio stesso.
    """
    import logging
    from logging.handlers import RotatingFileHandler
    
    # Crea directory logs se non esiste
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Percorso file di log
    log_file = os.path.join(log_dir, "service.log")
    
    # Configura il logger
    log_level = getattr(logging, get_settings().log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                log_file, 
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("PramaIA-LogService")
