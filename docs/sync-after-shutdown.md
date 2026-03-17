# Sync Superset: da sviluppo a produzione

Questo documento descrive come replicare l'istanza Superset locale sul server di produzione, e come mantenere la sincronizzazione tramite GitHub.

Esistono **due approcci** per versionalizzare dashboard e chart:

| Approccio | Pro | Contro |
|-----------|-----|--------|
| **ZIP** | Semplice, un singolo file | Binario, diff Git non leggibile |
| **YAML (file singoli)** | Diff leggibili, merge possibile | Richiede un passaggio in più |

L'approccio YAML è quello raccomandato per una sincronizzazione via Git mantenibile nel tempo.

---

## Prerequisiti sul server di produzione

- Docker e Docker Compose installati
- Git installato e accesso al repository Chirone
- Porta 80 (o quella desiderata) aperta sul firewall

---

## Fase 1 — Esportare dashboard e chart dal locale

### Opzione A — Export come file YAML (raccomandato per Git)

Lo ZIP esportato da Superset contiene internamente file YAML. È possibile scompattarlo e versionare i singoli file, ottenendo diff leggibili su Git.

```bash
cd chirone/superset
mkdir -p exports/unpacked

# 1. Esportare lo ZIP dal container
docker compose exec superset superset export-dashboards \
  -f /app/superset_home/exports/all_dashboards.zip
docker compose cp superset:/app/superset_home/exports/all_dashboards.zip /tmp/

# 2. Scompattare i YAML nella cartella versionata
unzip -o /tmp/all_dashboards.zip -d exports/unpacked/

# 3. Committare i file YAML
git add exports/unpacked/
git commit -m "chore: aggiorna export dashboard (YAML)"
git push
```

La struttura risultante sarà:

```
exports/unpacked/
  dashboards/
    my_dashboard.yaml
  charts/
    my_chart.yaml
  datasets/
    my_dataset.yaml
  databases/
    my_database.yaml
  metadata.yaml
```

Per **reimportare** da YAML sul server di produzione, ricreare lo ZIP dai file YAML:

```bash
cd exports/unpacked
zip -r /tmp/all_dashboards.zip .
docker compose cp /tmp/all_dashboards.zip superset:/tmp/
docker compose exec superset superset import-dashboards \
  -p /tmp/all_dashboards.zip --overwrite
```

---

### Opzione B — Export come ZIP (rapido, una tantum)

#### Via UI

1. Aprire Superset locale su `http://localhost:8088`
2. Andare su **Dashboards** → selezionare le dashboard da esportare → **Export**
3. Viene scaricato un file `.zip` per ogni dashboard (include anche le chart e i dataset collegati)
4. Salvare i file nella cartella `exports/` del repository:

```
chirone/superset/exports/
  dashboard_<nome>.zip
  ...
```

#### Via CLI

```bash
# Esportare tutte le dashboard
docker compose exec superset superset export-dashboards \
  -f /app/superset_home/exports/all_dashboards.zip

# Copiare fuori dal container
docker compose cp superset:/app/superset_home/exports/all_dashboards.zip ./exports/
```

```bash
cd chirone/superset
git add exports/
git commit -m "chore: esporta dashboard e chart per sync produzione"
git push
```

---

## Fase 2 — Setup iniziale sul server di produzione

### 2a. Clonare il repository

```bash
git clone <url-repository-chirone> /opt/chirone
cd /opt/chirone/chirone/superset
```

### 2b. Configurare i file di ambiente

Creare `docker/.env-local` con i valori per la produzione:

```bash
cat > docker/.env-local << 'EOF'
SUPERSET_LOAD_EXAMPLES=no
SUPERSET_SECRET_KEY=<SEGRETO_CASUALE_SICURO_64_CARATTERI>
SUPERSET_ENV=production
FLASK_DEBUG=false
EOF
```

> **Importante:** `SUPERSET_SECRET_KEY` deve essere un valore casuale sicuro, diverso dal default `TEST_NON_DEV_SECRET`. Generarlo con:
> ```bash
> openssl rand -base64 48
> ```

Verificare che `docker/.env` contenga `TAG=6.0.0` (stessa versione del locale).

### 2c. Avviare i container

```bash
docker compose up -d --build
```

Attendere che `superset-init` completi (si può monitorare con `docker compose logs -f superset-init`).

---

## Fase 3 — Importare dashboard e chart sul server

### 3a. Import via UI

1. Aprire Superset su `http://<ip-server>`
2. Andare su **Dashboards** → **Import Dashboard**
3. Caricare i file `.zip` dalla cartella `exports/`

### 3b. Import via CLI

```bash
# Copiare il file zip nel container
docker compose cp exports/all_dashboards.zip superset:/tmp/

# Importare
docker compose exec superset superset import-dashboards -p /tmp/all_dashboards.zip
```

---

## Fase 4 — Sincronizzazione continua tramite GitHub

Il flusso di sync è: **export su locale → commit → push → pull su server → import**.

### Workflow con YAML (raccomandato)

**Sul PC di sviluppo** (dopo modifiche a dashboard/chart):

```bash
cd chirone/superset

# 1. Esportare e scompattare i YAML
docker compose exec superset superset export-dashboards \
  -f /app/superset_home/exports/all_dashboards.zip
docker compose cp superset:/app/superset_home/exports/all_dashboards.zip /tmp/
unzip -o /tmp/all_dashboards.zip -d exports/unpacked/

# 2. Committare e pushare (diff leggibili sui singoli YAML)
git add exports/unpacked/
git commit -m "chore: aggiorna dashboard <nome>"
git push
```

**Sul server di produzione** (per applicare gli aggiornamenti):

```bash
cd /opt/chirone/chirone/superset

# 1. Pull degli aggiornamenti
git pull

# 2. (Solo se ci sono modifiche al docker-compose o alla config) Rebuild
docker compose up -d --build

# 3. Ricreare lo ZIP e importare
cd exports/unpacked && zip -r /tmp/all_dashboards.zip . && cd -
docker compose cp /tmp/all_dashboards.zip superset:/tmp/
docker compose exec superset superset import-dashboards \
  -p /tmp/all_dashboards.zip --overwrite
```

### Workflow con ZIP (alternativo)

**Sul PC di sviluppo:**

```bash
cd chirone/superset
docker compose exec superset superset export-dashboards \
  -f /app/superset_home/exports/all_dashboards.zip
docker compose cp superset:/app/superset_home/exports/all_dashboards.zip ./exports/
git add exports/
git commit -m "chore: aggiorna export dashboard"
git push
```

**Sul server di produzione:**

```bash
cd /opt/chirone/chirone/superset
git pull
docker compose cp exports/all_dashboards.zip superset:/tmp/
docker compose exec superset superset import-dashboards \
  -p /tmp/all_dashboards.zip --overwrite
```

> L'opzione `--overwrite` sovrascrive le dashboard esistenti con lo stesso UUID. Gli UUID sono preservati nell'export, quindi l'import idempotente funziona correttamente.

---

## Riepilogo file da tenere nel repository

| File | Scopo |
|------|-------|
| `docker/.env` | Configurazione base (già versionato) |
| `docker/.env-local` | Override locale/produzione — **NON committare** (sta in `.gitignore`) |
| `docker/pythonpath_dev/superset_config.py` | Config Python Superset |
| `exports/unpacked/` | File YAML delle dashboard/chart — **committare** (approccio raccomandato) |
| `exports/*.zip` | ZIP monolitico — alternativa, diff non leggibile su Git |

---

## Note

- **Versione Superset**: mantenere `TAG=6.0.0` identico su locale e produzione per evitare incompatibilità nell'import degli export.
- **Database Superset**: il database interno (`db_home` volume) **non** viene sincronizzato via Git — solo gli export ZIP vengono condivisi. Questo è intenzionale: il database di produzione avrà utenti e permission proprie.
- **Connessioni ai database**: dopo l'import, verificare che le connessioni ai database (es. PostgreSQL datawarehouse) siano configurate correttamente nell'istanza di produzione tramite **Data → Databases**.
- **Secret Key**: non condividere mai la `SUPERSET_SECRET_KEY` di produzione con quella di sviluppo.
