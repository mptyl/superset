# Superset — Workflow Generale: Software e Dashboard

Questo documento descrive come Marco, Sara e Pino collaborano su Superset
mantenendo allineati sia il codice (software) che i contenuti (dashboard).

---

## 1. Ruoli e infrastruttura

| Persona | Ambiente | Porta | Accesso |
|---------|----------|-------|---------|
| **Marco** | Mac locale | 8088 | Owner del branch `master`; accesso SSH al server Sara |
| **Sara**  | Server remoto | 8088 | Accesso SSH da Marco; git push/pull autonomo |
| **Pino**  | Mac locale | 8089 (`docker-compose-pino.yml`) | Solo git oppure file via Google Drive in casi eccezionali |

---

## 2. Regola fondamentale: separare software da dashboard

| Tipo | Cosa comprende | Come si propaga |
|------|---------------|-----------------|
| **Software** | Codice Superset, patch, config Docker | `git pull` + `docker compose build` |
| **Dashboard** | File YAML in `exports/unpacked/dashboard_export_latest/` | `superset import-dashboards` |

**Non fare mai le due cose insieme nella stessa sessione.** Separare gli aggiornamenti
evita di confondere errori di rendering (software) con contenuti mancanti (dashboard).

---

## 3. Allineamento software (codice Superset)

### 3.1 Marco — upgrade upstream

```bash
git fetch upstream
git checkout master
git cherry-pick <sha-patch-1> <sha-patch-2> <sha-patch-3>
# test locale
git push origin master
```

### 3.2 Sara — aggiornamento dal server

```bash
git pull origin master
docker compose build --no-cache
docker compose up -d
```

### 3.3 Pino — aggiornamento sul Mac

```bash
git pull origin master
docker compose -f docker-compose-pino.yml build --no-cache
docker compose -f docker-compose-pino.yml up -d
```

> In caso di problemi di rete o build, Marco può inviare uno ZIP dell'immagine
> via Google Drive come alternativa eccezionale.

### 3.4 Patch essenziali da verificare ad ogni upgrade

Ad ogni aggiornamento upstream verificare che queste tre patch siano ancora applicate:

| File | Commit | Funzione |
|------|--------|----------|
| `superset-frontend/src/dashboard/components/gridComponents/Tabs.jsx` | `efea95e` | Emette `window.resize` dopo il cambio tab — i chart inizializzati in tab nascosti ricevono le dimensioni corrette |
| `superset-frontend/src/components/Chart/Chart.jsx` | `efea95e` | Aggiunge `isComponentVisible` al memo comparator — React ri-renderizza il chart quando il tab diventa visibile |
| `docker/docker-bootstrap.sh` | `f8b04e5` | Abilita psycopg2 per il worker/beat — assente nell'immagine base 6.0.0 |

```bash
# Verifica rapida
git log --oneline efea95e
git show efea95e --name-only
```

---

## 4. Allineamento dashboard (export/import YAML)

### 4.1 Directory fissa

Tutti i file YAML delle dashboard vivono in:

```
exports/unpacked/dashboard_export_latest/
```

Questa directory viene tracciata da git. Aggiornare sempre questa path, non
creare sottocartelle con date diverse.

### 4.2 UUID stabili — nessun duplicato

Superset usa gli UUID per identificare le dashboard. L'import:
- **aggiorna** le dashboard il cui UUID è presente nel pacchetto;
- **non tocca** le dashboard con UUID non presenti nel pacchetto.

Questo significa che le dashboard di Pino (UUID unici) non vengono
sovrascritte da un import delle dashboard di Sara/Marco.

### 4.3 Comando export

```bash
docker compose exec superset superset export-dashboards -f /tmp/exp.zip
unzip -o /tmp/exp.zip -d exports/unpacked/dashboard_export_latest/
git add exports/
git commit -m "chore: export dashboard - $(date +%Y-%m-%d)"
```

### 4.4 Comando import

```bash
docker compose exec superset superset import-dashboards \
  -p exports/unpacked/dashboard_export_latest/
```

---

## 5. Workflow giornaliero Sara / Pino

### 5.1 Inizio sessione (mattina)

```bash
git pull origin master
docker compose exec superset superset import-dashboards \
  -p exports/unpacked/dashboard_export_latest/
```

### 5.2 Proporre modifiche a una dashboard

```bash
# 1. Modificare la dashboard in Superset
# 2. Esportare
docker compose exec superset superset export-dashboards -f /tmp/exp.zip
unzip -o /tmp/exp.zip -d exports/unpacked/dashboard_export_latest/
# 3. Aprire un branch e una PR
git checkout -b <nome>/modifica-dashboard-<data>
git add exports/
git commit -m "feat(dashboard): <descrizione modifica>"
git push origin <nome>/modifica-dashboard-<data>
# Aprire PR su GitHub verso master
```

### 5.3 Revisione PR (Marco)

1. Leggere il diff YAML nella PR su GitHub.
2. Fare checkout del branch in locale e importare:
   ```bash
   git checkout <branch-pr>
   docker compose exec superset superset import-dashboards \
     -p exports/unpacked/dashboard_export_latest/
   ```
3. Verificare nel browser (porta 8088).
4. Merge se tutto è corretto.

### 5.4 Dopo il merge

```bash
git pull origin master
docker compose exec superset superset import-dashboards \
  -p exports/unpacked/dashboard_export_latest/
```

---

## 6. Accesso diretto Sara via SSH da Marco

Marco può esportare e importare le dashboard di Sara senza che Sara debba
fare nulla:

```bash
# Esporta dal server Sara
ssh user@server-sara "cd /percorso/superset && \
  docker compose exec -T superset superset export-dashboards -f /tmp/exp.zip"

# Scarica in locale
scp user@server-sara:/tmp/exp.zip /tmp/sara-export.zip

# Estrai nella directory fissa
unzip -o /tmp/sara-export.zip \
  -d /Users/mp/Chirone/chirone/superset/exports/unpacked/dashboard_export_latest/
```

---

## 7. Gestione conflitti YAML

Se lo stesso file YAML (stessa dashboard) viene modificato da due persone
contemporaneamente, git segnala un conflitto durante il merge/pull.

**Procedura di risoluzione:**

1. Uno dei due reimporta `master` (sovrascrivendo la sua versione locale).
2. Riesporta dal proprio Superset.
3. Riapre la PR con il branch aggiornato.
4. Marco fa merge.

Non tentare mai di risolvere conflitti YAML a mano — la struttura è complessa
e un errore renderebbe la dashboard non importabile.

---

## 8. Upgrade a nuova release Superset

**Solo Marco gestisce gli upgrade.** Procedura:

```bash
git fetch upstream
git checkout -b upgrade/superset-X.Y.Z
git merge upstream/master  # o cherry-pick dei commit rilevanti

# Riapplicare le tre patch (vedi sezione 3.4)
# Testare in locale su porta 8088

git checkout master
git merge upgrade/superset-X.Y.Z
git push origin master
```

**Comunicare a Sara e Pino:** fare `git pull + docker rebuild` (solo software,
NON import-dashboards — le dashboard non cambiano con un upgrade software).

```bash
# Sara / Pino dopo comunicazione di Marco:
git pull origin master
docker compose build --no-cache
docker compose up -d
# (nessun import-dashboards)
```
