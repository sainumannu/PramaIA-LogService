# PramaIA LogService

Servizio centralizzato di logging per l'ecosistema PramaIA.

## Descrizione

PramaIA LogService è un servizio dedicato alla gestione centralizzata dei log per tutti i progetti dell'ecosistema PramaIA. Fornisce API REST per la registrazione dei log, un sistema di archiviazione strutturato e un'interfaccia web per la visualizzazione e la ricerca nei log.

## Caratteristiche

- **API REST** per l'invio dei log da qualsiasi servizio
- **Categorizzazione** dei log per progetto, modulo e livello
- **Rotazione automatica** dei file di log
- **Pulizia programmata** in base alle politiche di retention configurabili
- **Interfaccia web** per la visualizzazione e la ricerca nei log
- **Client leggeri** per l'integrazione con i vari progetti
- **Supporto per diversi livelli di log** (debug, info, warning, error, critical)
- **Autenticazione** per proteggere le API e l'interfaccia web

## Struttura del progetto

```
PramaIA-LogService/
├── api/                  # API REST per la ricezione dei log
├── core/                 # Logica di business del servizio
├── logs/                 # Directory per l'archiviazione dei log
├── web/                  # Interfaccia web per la visualizzazione dei log
├── clients/              # Client per l'integrazione con altri servizi
├── config/               # Configurazione del servizio
└── docs/                 # Documentazione
```

## Integrazione

Il servizio può essere integrato con:
- PramaIAServer
- PramaIA-PDK
- PramaIA-Agents

## Requisiti

- Python 3.9+
- FastAPI
- SQLite (per la configurazione e i metadati)
- HTML/CSS/JavaScript per l'interfaccia web

## Configurazione

La configurazione del servizio è gestita tramite file di configurazione e può essere modificata tramite l'interfaccia web. Le impostazioni includono:

- Livelli di log da registrare
- Periodo di retention dei log
- Dimensione massima dei file di log
- Configurazione dell'autenticazione
- Porte e indirizzi per le API
