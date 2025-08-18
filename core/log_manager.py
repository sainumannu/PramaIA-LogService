"""
Sistema di gestione dei log.
"""

import os
import json
import sqlite3
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import uuid
import logging

from core.models import LogEntry, LogLevel, LogProject, LogStats

# Configura il logger interno
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LogManager")

class LogManager:
    """
    Gestisce la memorizzazione e il recupero dei log.
    """
    
    def __init__(self, db_path=None):
        """
        Inizializza il gestore dei log.
        
        Args:
            db_path: Percorso al database SQLite. Se None, usa il percorso predefinito.
        """
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            db_path = os.path.join(base_dir, "logs", "log_database.db")
            
            # Assicurati che la directory logs esista
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
        self.db_path = db_path
        self.start_time = datetime.now()
        self._initialize_database()
    
    def _get_connection(self):
        """
        Ottiene una connessione al database.
        
        Returns:
            Connessione a SQLite
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _initialize_database(self):
        """
        Inizializza il database creando le tabelle necessarie se non esistono.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Crea la tabella dei log
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            project TEXT NOT NULL,
            level TEXT NOT NULL,
            module TEXT NOT NULL,
            message TEXT NOT NULL,
            details TEXT,
            context TEXT
        )
        ''')
        
        # Crea indici per migliorare le performance delle query
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON logs (timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project ON logs (project)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_level ON logs (level)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_module ON logs (module)')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database inizializzato: {self.db_path}")
    
    def add_log(self, log_entry: LogEntry) -> str:
        """
        Aggiunge una voce di log al database.
        
        Args:
            log_entry: LogEntry da aggiungere
            
        Returns:
            ID del log aggiunto
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Converti le strutture dati in JSON
        details_json = json.dumps(log_entry.details) if log_entry.details else None
        context_json = json.dumps(log_entry.context) if log_entry.context else None
        
        # Inserisci il log
        cursor.execute('''
        INSERT INTO logs (id, timestamp, project, level, module, message, details, context)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_entry.id,
            log_entry.timestamp.isoformat(),
            log_entry.project,
            log_entry.level,
            log_entry.module,
            log_entry.message,
            details_json,
            context_json
        ))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Log aggiunto: {log_entry.id} - {log_entry.message}")
        return log_entry.id
    
    def add_logs_batch(self, log_entries: List[LogEntry]) -> List[str]:
        """
        Aggiunge più voci di log al database in un'unica transazione.
        
        Args:
            log_entries: Lista di LogEntry da aggiungere
            
        Returns:
            Lista di ID dei log aggiunti
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        log_ids = []
        
        try:
            for log_entry in log_entries:
                # Converti le strutture dati in JSON
                details_json = json.dumps(log_entry.details) if log_entry.details else None
                context_json = json.dumps(log_entry.context) if log_entry.context else None
                
                # Inserisci il log
                cursor.execute('''
                INSERT INTO logs (id, timestamp, project, level, module, message, details, context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    log_entry.id,
                    log_entry.timestamp.isoformat(),
                    log_entry.project,
                    log_entry.level,
                    log_entry.module,
                    log_entry.message,
                    details_json,
                    context_json
                ))
                
                log_ids.append(log_entry.id)
            
            conn.commit()
            logger.info(f"Batch di {len(log_ids)} log aggiunto con successo")
        except Exception as e:
            conn.rollback()
            logger.error(f"Errore durante l'aggiunta del batch di log: {str(e)}")
            raise
        finally:
            conn.close()
        
        return log_ids
    
    def get_logs(
        self,
        project: Optional[LogProject] = None,
        level: Optional[LogLevel] = None,
        module: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Recupera i log in base ai filtri specificati.
        
        Args:
            project: Filtra per progetto
            level: Filtra per livello di log
            module: Filtra per modulo
            start_date: Data di inizio per il filtro temporale
            end_date: Data di fine per il filtro temporale
            limit: Numero massimo di log da restituire
            offset: Offset per la paginazione
            
        Returns:
            Lista di log che soddisfano i criteri di filtro
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Costruisci la query
        query = "SELECT * FROM logs WHERE 1=1"
        params = []
        
        if project:
            query += " AND project = ?"
            params.append(project)
        
        if level:
            query += " AND level = ?"
            params.append(level)
        
        if module:
            query += " AND module = ?"
            params.append(module)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        # Ordina per timestamp decrescente (più recenti prima)
        query += " ORDER BY timestamp DESC"
        
        # Limita i risultati
        query += " LIMIT ? OFFSET ?"
        params.append(limit)
        params.append(offset)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Converti i risultati in dizionari
        results = []
        for row in rows:
            log_dict = dict(row)
            
            # Converti JSON in dizionari
            if log_dict["details"]:
                log_dict["details"] = json.loads(log_dict["details"])
            
            if log_dict["context"]:
                log_dict["context"] = json.loads(log_dict["context"])
            
            results.append(log_dict)
        
        conn.close()
        return results
    
    def get_stats(
        self,
        project: Optional[LogProject] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> LogStats:
        """
        Ottiene statistiche sui log.
        
        Args:
            project: Filtra per progetto
            start_date: Data di inizio per il filtro temporale
            end_date: Data di fine per il filtro temporale
            
        Returns:
            Statistiche sui log
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Query base per il conteggio totale
        query = "SELECT COUNT(*) as total FROM logs WHERE 1=1"
        params = []
        
        # Aggiungi filtri
        if project:
            query += " AND project = ?"
            params.append(project)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        # Esegui query per il conteggio totale
        cursor.execute(query, params)
        total_logs = cursor.fetchone()["total"]
        
        # Query per conteggio per livello
        level_query = query.replace("COUNT(*)", "level, COUNT(*) as count") + " GROUP BY level"
        cursor.execute(level_query, params)
        level_rows = cursor.fetchall()
        
        logs_by_level = {}
        for level in LogLevel:
            logs_by_level[level] = 0
            
        for row in level_rows:
            logs_by_level[row["level"]] = row["count"]
        
        # Query per conteggio per progetto
        project_query = query.replace("COUNT(*)", "project, COUNT(*) as count") + " GROUP BY project"
        cursor.execute(project_query, params)
        project_rows = cursor.fetchall()
        
        logs_by_project = {}
        for project_enum in LogProject:
            logs_by_project[project_enum] = 0
            
        for row in project_rows:
            logs_by_project[row["project"]] = row["count"]
        
        # Query per conteggio per modulo (top 10)
        module_query = query.replace("COUNT(*)", "module, COUNT(*) as count") + " GROUP BY module ORDER BY count DESC LIMIT 10"
        cursor.execute(module_query, params)
        module_rows = cursor.fetchall()
        
        logs_by_module = {}
        for row in module_rows:
            logs_by_module[row["module"]] = row["count"]
        
        # Determina il periodo di tempo
        time_period = {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        }
        
        if not start_date or not end_date:
            # Se non specificato, prendi il periodo effettivo dai dati
            min_max_query = "SELECT MIN(timestamp) as min_time, MAX(timestamp) as max_time FROM logs"
            cursor.execute(min_max_query)
            time_row = cursor.fetchone()
            
            if not start_date and time_row["min_time"]:
                time_period["start"] = time_row["min_time"]
            
            if not end_date and time_row["max_time"]:
                time_period["end"] = time_row["max_time"]
        
        conn.close()
        
        # Crea l'oggetto statistiche
        stats = {
            "total_logs": total_logs,
            "logs_by_level": logs_by_level,
            "logs_by_project": logs_by_project,
            "logs_by_module": logs_by_module,
            "time_period": time_period
        }
        
        return stats
    
    def cleanup_logs(
        self,
        days_to_keep: int = 30,
        project: Optional[LogProject] = None,
        level: Optional[LogLevel] = None
    ) -> int:
        """
        Elimina i log più vecchi di un certo numero di giorni.
        
        Args:
            days_to_keep: Numero di giorni per cui mantenere i log
            project: Filtra per progetto
            level: Filtra per livello di log
            
        Returns:
            Numero di log eliminati
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Calcola la data limite
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        # Costruisci la query
        query = "DELETE FROM logs WHERE timestamp < ?"
        params = [cutoff_date]
        
        if project:
            query += " AND project = ?"
            params.append(project)
        
        if level:
            query += " AND level = ?"
            params.append(level)
        
        # Esegui la query
        cursor.execute(query, params)
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"Eliminati {deleted_count} log più vecchi di {days_to_keep} giorni")
        return deleted_count
    
    def get_logs_count(
        self,
        project: Optional[LogProject] = None,
        level: Optional[LogLevel] = None,
        module: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Conta i log in base ai filtri specificati.
        
        Args:
            project: Filtra per progetto
            level: Filtra per livello di log
            module: Filtra per modulo
            start_date: Data di inizio per il filtro temporale
            end_date: Data di fine per il filtro temporale
            
        Returns:
            Numero di log che soddisfano i criteri di filtro
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Costruisci la query
        query = "SELECT COUNT(*) as count FROM logs WHERE 1=1"
        params = []
        
        if project:
            query += " AND project = ?"
            params.append(project)
        
        if level:
            query += " AND level = ?"
            params.append(level)
        
        if module:
            query += " AND module = ?"
            params.append(module)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        conn.close()
        return row["count"]
    
    def get_db_size(self) -> str:
        """
        Ottiene la dimensione del file del database.
        
        Returns:
            Dimensione del database in formato leggibile (es. "1.5 MB")
        """
        try:
            # Ottieni la dimensione del file in bytes
            size_bytes = os.path.getsize(self.db_path)
            
            # Converti in formato leggibile
            units = ["B", "KB", "MB", "GB"]
            unit_index = 0
            size = float(size_bytes)
            
            while size >= 1024 and unit_index < len(units) - 1:
                size /= 1024
                unit_index += 1
            
            return f"{size:.1f} {units[unit_index]}"
        except Exception as e:
            logger.error(f"Errore durante il calcolo della dimensione del database: {str(e)}")
            return "N/A"
