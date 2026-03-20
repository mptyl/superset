# Allineamento Contingente — Marzo 2026

Procedura una-tantum per allineare Marco, Sara e Pino partendo dalla
situazione attuale:

| Persona | Stato dashboard |
|---------|----------------|
| **Sara** (server remoto) | Versione più avanzata — **fonte di verità** |
| **Marco** (Mac locale) | Indietro rispetto a Sara |
| **Pino** (Mac locale) | Ha dashboard **nuove** con UUID distinti da preservare |

---

## Step 1 — Esportare le dashboard dal server Sara

### Opzione A — Marco via SSH (preferita, nessun intervento di Sara)

```bash
# 1. Esporta dal server Sara
ssh user@server-sara "cd /percorso/superset && \
  docker compose exec -T superset superset export-dashboards -f /tmp/export_sara.zip"

# 2. Scarica in locale su Mac Marco
scp user@server-sara:/tmp/export_sara.zip /tmp/sara-export.zip

# 3. Estrai nella directory fissa
unzip -o /tmp/sara-export.zip \
  -d /Users/mp/Chirone/chirone/superset/exports/unpacked/dashboard_export_latest/
```

### Opzione B — Sara lo fa in autonomia (se SSH non disponibile)

Sara sul suo server:

```bash
# 1. Esporta e decomprimi
docker compose exec superset superset export-dashboards -f /tmp/export.zip
unzip -o /tmp/export.zip -d exports/unpacked/dashboard_export_latest/

# 2. Crea branch e committa
git checkout -b sara/allineamento-marzo-2026
git add exports/
git commit -m "chore: export dashboard sara - marzo 2026"
git push origin sara/allineamento-marzo-2026
```

Marco poi fa pull del branch e continua dallo Step 2.

---

## Step 2 — Marco importa le dashboard di Sara sul suo Mac

```bash
# I file sono già in dashboard_export_latest/ (da Step 1 Opzione A)
# oppure hai fatto pull del branch Sara (Opzione B)

docker compose exec superset superset import-dashboards \
  -p exports/unpacked/dashboard_export_latest/
```

Aprire il browser su `http://localhost:8088` e verificare che le dashboard
di Sara siano presenti e corrette.

---

## Step 3 — Marco committa e pusha su master

```bash
git checkout master
git add exports/
git commit -m "chore: allineamento dashboard master a server sara - marzo 2026"
git push origin master
```

---

## Step 4 — Pino si allinea preservando le sue dashboard

Pino sul suo Mac:

```bash
# 1. Aggiorna master
git checkout master && git pull origin master

# 2. Importa le dashboard di Sara/Marco
docker compose -f docker-compose-pino.yml exec superset \
  superset import-dashboards \
  -p exports/unpacked/dashboard_export_latest/
```

> **Nota importante:** Le dashboard nuove di Pino hanno UUID diversi da
> quelle di Sara/Marco. L'import non le tocca. Al termine Pino avrà sia le
> dashboard di Sara/Marco che le sue.

---

## Step 5 (opzionale) — Pino porta le sue dashboard nuove in master

Se Pino vuole che le sue dashboard nuove siano disponibili anche a Marco e Sara:

```bash
# 1. Esporta tutto (include sia le dashboard Sara/Marco che quelle nuove di Pino)
docker compose -f docker-compose-pino.yml exec superset \
  superset export-dashboards -f /tmp/export_pino.zip

unzip -o /tmp/export_pino.zip \
  -d exports/unpacked/dashboard_export_latest/

# 2. Crea branch e PR
git checkout -b pino/dashboard-locali-marzo-2026
git add exports/
git commit -m "feat(dashboard): aggiungi dashboard locali pino - marzo 2026"
git push origin pino/dashboard-locali-marzo-2026
```

Marco revisiona la PR (legge il diff YAML, importa in locale, verifica nel
browser) e fa merge se tutto è corretto.

---

## Verifica finale

Dopo che tutti hanno completato i propri step:

**Marco** — aprire `http://localhost:8088` e verificare:
- Le dashboard di Sara sono presenti e corrette

**Pino** — aprire `http://localhost:8089` e verificare:
- Le dashboard di Sara/Marco sono presenti
- Le sue dashboard nuove sono ancora presenti

**Tutti** — verificare il log git:

```bash
git log --oneline -5
```

Output atteso simile a:
```
abc1234 feat(dashboard): aggiungi dashboard locali pino - marzo 2026  # se Step 5
def5678 chore: allineamento dashboard master a server sara - marzo 2026
...
```
