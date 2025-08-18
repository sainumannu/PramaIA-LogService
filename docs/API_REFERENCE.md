# API Reference

## Overview

PramaIA-LogService fornisce una serie di API RESTful per l'invio e la consultazione dei log. Tutte le richieste API richiedono un'autenticazione tramite API key.

## Autenticazione

L'autenticazione avviene tramite l'header HTTP `X-API-Key`.

Esempio:
```
X-API-Key: pramaiaserver_api_key_123456
```

## Endpoints

### Creazione di log

#### POST /api/logs

Crea una nuova voce di log.

**Request Body:**

```json
{
  "project": "PramaIAServer",
  "level": "error",
  "module": "workflow_triggers_router",
  "message": "Errore durante il caricamento dei trigger",
  "details": {
    "workflow_id": "123456",
    "error_type": "DatabaseError",
    "exception": "Unable to connect to database"
  },
  "context": {
    "user_id": "admin",
    "request_id": "abcdef123456",
    "ip_address": "192.168.1.100"
  }
}
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Log registrato con successo"
}
```

#### POST /api/logs/batch

Crea multiple voci di log in un'unica richiesta.

**Request Body:**

```json
[
  {
    "project": "PramaIAServer",
    "level": "info",
    "module": "workflow_service",
    "message": "Workflow avviato",
    "details": {
      "workflow_id": "123456"
    },
    "context": {
      "user_id": "admin"
    }
  },
  {
    "project": "PramaIAServer",
    "level": "error",
    "module": "workflow_service",
    "message": "Errore durante l'esecuzione del workflow",
    "details": {
      "workflow_id": "123456",
      "error_type": "ExecutionError"
    },
    "context": {
      "user_id": "admin"
    }
  }
]
```

**Response:**

```json
{
  "ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "650e8400-e29b-41d4-a716-446655440000"
  ],
  "count": 2,
  "message": "Logs registrati con successo"
}
```

### Consultazione di log

#### GET /api/logs

Recupera le voci di log in base ai filtri specificati.

**Query Parameters:**

- `project`: filtra per progetto (opzionale)
- `level`: filtra per livello di log (opzionale)
- `module`: filtra per modulo (opzionale)
- `start_date`: filtra per data di inizio (ISO format, opzionale)
- `end_date`: filtra per data di fine (ISO format, opzionale)
- `limit`: numero massimo di log da restituire (default: 100)
- `offset`: offset per la paginazione (default: 0)

**Response:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2023-08-18T14:30:00.000Z",
    "project": "PramaIAServer",
    "level": "info",
    "module": "workflow_service",
    "message": "Workflow avviato",
    "details": {
      "workflow_id": "123456"
    },
    "context": {
      "user_id": "admin"
    }
  },
  {
    "id": "650e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2023-08-18T14:31:00.000Z",
    "project": "PramaIAServer",
    "level": "error",
    "module": "workflow_service",
    "message": "Errore durante l'esecuzione del workflow",
    "details": {
      "workflow_id": "123456",
      "error_type": "ExecutionError"
    },
    "context": {
      "user_id": "admin"
    }
  }
]
```

#### GET /api/logs/stats

Recupera statistiche sui log.

**Query Parameters:**

- `project`: filtra per progetto (opzionale)
- `start_date`: filtra per data di inizio (ISO format, opzionale)
- `end_date`: filtra per data di fine (ISO format, opzionale)

**Response:**

```json
{
  "total_logs": 1000,
  "logs_by_level": {
    "debug": 500,
    "info": 300,
    "warning": 100,
    "error": 80,
    "critical": 20
  },
  "logs_by_project": {
    "PramaIAServer": 600,
    "PramaIA-PDK": 300,
    "PramaIA-Agents": 80,
    "PramaIA-Plugins": 20,
    "other": 0
  },
  "logs_by_module": {
    "workflow_service": 300,
    "workflow_triggers_router": 200,
    "pdf_monitor_agent": 150,
    "workflow_editor": 100,
    "user_service": 80
  },
  "time_period": {
    "start": "2023-08-01T00:00:00.000Z",
    "end": "2023-08-18T23:59:59.999Z"
  }
}
```

### Gestione di log

#### DELETE /api/logs/cleanup

Pulisce i log più vecchi di un certo numero di giorni.

**Query Parameters:**

- `days_to_keep`: numero di giorni per cui mantenere i log (default: 30)
- `project`: filtra per progetto (opzionale)
- `level`: filtra per livello di log (opzionale)

**Response:**

```json
{
  "deleted_count": 500,
  "message": "Eliminati 500 log"
}
```
