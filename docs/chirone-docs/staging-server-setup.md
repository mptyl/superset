# Setup Staging Server — Database PostgreSQL su Hetzner

Questo documento descrive come configurare un server di staging su Hetzner Cloud con
PostgreSQL per ospitare i dati del datawarehouse e dei datamart, in preparazione
all'installazione di Superset.

---

## 1. Scelta del server Hetzner

### Raccomandazione

Per uno staging database che ospita il datawarehouse Chirone (DIM/FACT/BRIDGE) e i
datamart (mart_paziente ~720k righe, mart_ablazione):

| Modello | vCPU | RAM | Storage | Prezzo ca. | Giudizio |
|---------|------|-----|---------|------------|----------|
| CPX31 | 4 AMD | 8 GB | 160 GB NVMe | ~12 €/mese | **Minimo accettabile** |
| **CPX41** | **8 AMD** | **16 GB** | **240 GB NVMe** | **~24 €/mese** | **✅ Consigliato** |
| CPX51 | 16 AMD | 32 GB | 360 GB NVMe | ~56 €/mese | Sovradimensionato per ora |

**Scelta consigliata: CPX41** — bilancia bene costo e performance per uno staging con
query analitiche su tabelle grandi e future sessioni Superset/Metabase simultanee.

**Datacenter: Falkenstein (FSN1) o Nuremberg (NBG1)** — EU Germania, ok per dati GDPR.

**OS: Ubuntu 22.04 LTS** (supporto fino ad aprile 2027, ampio supporto PostgreSQL).

**Opzioni aggiuntive da attivare alla creazione:**
- Firewall Hetzner (configurare subito)
- Backup automatici (+20% del costo, consigliato)
- Assegnare un IP statico (IPv4)

---

## 2. Configurazione iniziale del server

### 2.1 Accesso e aggiornamento

```bash
# Accesso via SSH (usare la chiave SSH caricata su Hetzner)
ssh root@<SERVER_IP>

# Aggiornamento sistema
apt update && apt upgrade -y

# Crea utente non-root per le operazioni
adduser chirone
usermod -aG sudo chirone

# Copia la chiave SSH all'utente
mkdir -p /home/chirone/.ssh
cp ~/.ssh/authorized_keys /home/chirone/.ssh/
chown -R chirone:chirone /home/chirone/.ssh
```

### 2.2 Firewall (UFW)

```bash
ufw allow OpenSSH
ufw allow 5432/tcp comment "PostgreSQL — solo da IP autorizzati"
ufw enable
ufw status
```

> **Importante**: la porta 5432 deve essere aperta solo verso gli IP noti (ufficio,
> macchina ETL, IP della propria connessione). Su Hetzner conviene usare il Firewall
> del pannello web per limitare l'accesso a livello di rete prima ancora del server.

**Configurazione Firewall Hetzner (pannello web):**
- Regola IN: TCP porta 22 — da tutti (o solo IP noti)
- Regola IN: TCP porta 5432 — solo da IP specifici (lista bianca)
- Regola OUT: tutto permesso

---

## 3. Installazione PostgreSQL 16

```bash
# Aggiungi repository ufficiale PostgreSQL
apt install -y curl ca-certificates
install -d /usr/share/postgresql-common/pgdg
curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail \
  https://www.postgresql.org/media/keys/ACCC4CF8.asc

sh -c 'echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] \
  https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
  > /etc/apt/sources.list.d/pgdg.list'

apt update
apt install -y postgresql-16

# Verifica
psql --version
systemctl status postgresql
```

---

## 4. Configurazione PostgreSQL

### 4.1 Tuning base per CPX41 (16 GB RAM)

Edita `/etc/postgresql/16/main/postgresql.conf`:

```ini
# Connessioni
max_connections = 100

# Memoria — regole empiriche per server dedicato a DB
shared_buffers = 4GB                # 25% della RAM
effective_cache_size = 12GB         # 75% della RAM
work_mem = 64MB                     # per query analitiche
maintenance_work_mem = 1GB

# Write-ahead log
wal_buffers = 64MB
checkpoint_completion_target = 0.9

# Query planner
random_page_cost = 1.1              # NVMe: quasi come memoria
effective_io_concurrency = 200

# Logging minimo (staging)
log_min_duration_statement = 2000   # logga query > 2s
log_line_prefix = '%t [%p] %u@%d '
```

### 4.2 Accesso remoto

Edita `/etc/postgresql/16/main/pg_hba.conf` — aggiungi alla fine:

```
# Accesso remoto autenticato con password (MD5/scram)
host    all             chirone_ro      0.0.0.0/0               scram-sha-256
host    datawarehouse   chirone_app     <IP_ETL>/32              scram-sha-256
```

Edita `/etc/postgresql/16/main/postgresql.conf`:

```ini
listen_addresses = '*'
```

Riavvia:

```bash
systemctl restart postgresql
```

### 4.3 Crea database e utenti

```bash
sudo -u postgres psql <<'EOF'
-- Database principale
CREATE DATABASE chirone_staging
  ENCODING 'UTF8'
  LC_COLLATE 'en_US.UTF-8'
  LC_CTYPE 'en_US.UTF-8'
  TEMPLATE template0;

-- Utente applicativo (ETL, dbt)
CREATE USER chirone_app WITH PASSWORD '<password-sicura-1>';

-- Utente read-only (Superset, analisti)
CREATE USER chirone_ro WITH PASSWORD '<password-sicura-2>';

-- Schemi
\c chirone_staging
CREATE SCHEMA datawarehouse;
CREATE SCHEMA datawarehouse_marts;

-- Permessi chirone_app
GRANT ALL ON SCHEMA datawarehouse TO chirone_app;
GRANT ALL ON SCHEMA datawarehouse_marts TO chirone_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA datawarehouse
  GRANT ALL ON TABLES TO chirone_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA datawarehouse_marts
  GRANT ALL ON TABLES TO chirone_app;

-- Permessi chirone_ro
GRANT USAGE ON SCHEMA datawarehouse TO chirone_ro;
GRANT USAGE ON SCHEMA datawarehouse_marts TO chirone_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA datawarehouse
  GRANT SELECT ON TABLES TO chirone_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA datawarehouse_marts
  GRANT SELECT ON TABLES TO chirone_ro;
EOF
```

---

## 5. Upload del Datawarehouse

Il modo più pulito è `pg_dump` dalla sorgente + `pg_restore` sulla destinazione.
Eseguire dalla macchina ETL (che ha accesso sia al DB sorgente che al server Hetzner).

### 5.1 Dump dalla sorgente (macchina ETL)

```bash
# Dump solo schema datawarehouse (struttura + dati)
pg_dump \
  --host=localhost \
  --port=5432 \
  --username=postgres \
  --dbname=postgres \
  --schema=datawarehouse \
  --format=custom \
  --compress=9 \
  --no-owner \
  --no-privileges \
  --file=datawarehouse_$(date +%Y%m%d).dump

# Verifica dimensione
ls -lh datawarehouse_*.dump
```

> **Credenziali sorgente**: le trovi in `etl/config/database-config.yaml`
> (sezione `destination`, usa le variabili da `.env.secrets`).

### 5.2 Restore sulla destinazione (server Hetzner)

```bash
# Copia il dump sul server Hetzner
scp datawarehouse_*.dump chirone@<SERVER_IP>:~/

# Sul server Hetzner
pg_restore \
  --host=localhost \
  --port=5432 \
  --username=chirone_app \
  --dbname=chirone_staging \
  --schema=datawarehouse \
  --no-owner \
  --no-privileges \
  --jobs=4 \
  --verbose \
  datawarehouse_*.dump

# Verifica conteggio tabelle caricate
psql -U chirone_app -d chirone_staging -c \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='datawarehouse';"
```

---

## 6. Upload dei Datamart

I datamart sono **materialized view** gestite da dbt. Ci sono due approcci:

### Opzione A — Dump diretto (più semplice, snapshot statico)

```bash
# Dump schema datawarehouse_marts
pg_dump \
  --host=localhost --port=5432 \
  --username=postgres --dbname=postgres \
  --schema=datawarehouse_marts \
  --format=custom --compress=9 \
  --no-owner --no-privileges \
  --file=datamart_$(date +%Y%m%d).dump

# Restore sul server Hetzner
pg_restore \
  --host=<SERVER_IP> --port=5432 \
  --username=chirone_app --dbname=chirone_staging \
  --schema=datawarehouse_marts \
  --no-owner --no-privileges \
  --jobs=4 \
  datamart_$(date +%Y%m%d).dump
```

### Opzione B — Rieseguire dbt sul server Hetzner (dati sempre freschi)

Configura `etl/dbt/profiles.yml` con un profilo `staging`:

```yaml
chirone_marts:
  target: staging
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5432
      user: postgres
      password: "{{ env_var('CHIRONE_DEST_PASSWORD') }}"
      dbname: postgres
      schema: datawarehouse_marts
      threads: 4
    staging:
      type: postgres
      host: <SERVER_IP_HETZNER>
      port: 5432
      user: chirone_app
      password: "{{ env_var('STAGING_DB_PASSWORD') }}"
      dbname: chirone_staging
      schema: datawarehouse_marts
      threads: 4
```

Poi esegui:

```bash
cd etl/dbt
dbt run --target staging --select mart_paziente mart_ablazione
dbt test --target staging
```

**Raccomandazione: usa l'Opzione A** per il primo caricamento, poi valuta se
automatizzare con dbt (Opzione B) una volta che il server è stabile.

---

## 7. Verifica finale

```bash
# Connettiti al server Hetzner
psql -h <SERVER_IP> -U chirone_ro -d chirone_staging

-- Elenca schemi
\dn

-- Conta tabelle per schema
SELECT table_schema, count(*) AS tabelle
FROM information_schema.tables
WHERE table_schema IN ('datawarehouse', 'datawarehouse_marts')
GROUP BY table_schema;

-- Verifica mart_paziente
SELECT count(*) FROM datawarehouse_marts.mart_paziente;

-- Verifica mart_ablazione
SELECT count(*) FROM datawarehouse_marts.mart_ablazione;

-- Verifica una tabella DWH
SELECT count(*) FROM datawarehouse.fact_ablazione;
```

---

## 8. Manutenzione periodica

Per tenere i dati aggiornati dopo il primo caricamento, le opzioni sono:

1. **Dump settimanale**: script cron sulla macchina ETL che esegue pg_dump + scp + pg_restore sul Hetzner.
2. **Replica logica PostgreSQL**: PostgreSQL streaming replication verso il server Hetzner (più complessa, dati quasi in tempo reale).
3. **dbt schedulato**: configurare dbt con target staging in un DAG Airflow separato.

Per lo staging dashboards la **frequenza settimanale** con dump manuale è sufficiente.

---

## 9. Prossimi passi (installazione Superset)

Una volta che il database è operativo e i dati sono caricati:

1. Installar Docker e Docker Compose sul server Hetzner
2. Clonare il repo `chirone/superset` sul server
3. Configurare `docker/.env` con:
   - `SUPERSET_BUILD_TARGET=lean` (build di produzione, no webpack dev server)
   - `DATABASE_HOST=<IP_interno>` (puntare al PostgreSQL locale)
4. Lanciare con `docker compose up -d` (senza `superset-node`)
5. Configurare la connessione database in Superset verso `chirone_staging`
6. Eseguire `sandbox/setup_superset.py` per creare i dataset `mart_paziente` e `mart_ablazione`

---

## Riferimenti

- Credenziali sorgente ETL: `etl/config/database-config.yaml` + `etl/.env.secrets`
- dbt profiles: `etl/dbt/profiles.yml`
- Setup dataset Superset: `superset/sandbox/setup_superset.py`
- Documentazione datamart: `chirone/etl/docs/datamart/index.md`
