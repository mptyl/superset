# Changelog — Chirone/Superset (fork locale)

Questo file traccia le modifiche apportate al fork Chirone di Apache Superset.
Non sostituisce il CHANGELOG upstream (`/CHANGELOG.md`).

Formato: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [Unreleased] — 2026-03-20

### Added
- `docs/chirone-docs/dashboard-workflow.md` — manuale operativo generale per
  la collaborazione multi-utente (Marco/Sara/Pino): ruoli, workflow quotidiano
  dashboard, gestione conflitti YAML, procedura upgrade Superset.
- `docs/chirone-docs/alignment-contingent-2026-03.md` — procedura una-tantum
  per allineare le istanze di Marco, Sara e Pino a partire dal server Sara
  (fonte di verità a marzo 2026), con comandi copia-incolla per tutti gli step.

### Changed
- `superset-frontend/webpack.config.js` — ripristinato da `upstream/master`
  (commit `git checkout upstream/master -- superset-frontend/webpack.config.js`).
  Rimossa l'occorrenza extra di `writeToDisk: true` nel blocco di build
  produzione, che causava la scrittura di bundle sul disco durante lo sviluppo
  e conflitti all'upgrade. L'unica occorrenza rimasta è quella in
  `devServer.devMiddleware` (valore upstream corretto).

### Removed
- `superset/static/assets/*.js` — eliminati 606 file di bundle non tracciati
  scritti su disco dal dev server (effetto collaterale del `writeToDisk: true`
  rimosso sopra).

### Renamed
- `exports/unpacked/dashboard_export_20260318T220954/` →
  `exports/unpacked/dashboard_export_latest/` — directory rinominata al nome
  canonico usato da tutti i comandi di import/export nei documenti operativi.

---

## 2026-03-18

### Added
- `exports/unpacked/dashboard_export_20260318T220954/` — primo export completo
  delle dashboard in formato YAML per il versionamento git.

### Changed
- `.gitignore` — aggiunto `docker/.env` per non tracciare credenziali locali.

---

## 2026-03-17

### Fixed
- `docker/docker-bootstrap.sh` (commit `f8b04e5`) — abilitato psycopg2 per
  worker e beat. L'immagine base 6.0.0 non include psycopg2 preinstallato;
  senza questa patch i task Celery falliscono al primo avvio.
- `docker-compose-pino.yml` — aggiunto compose separato per l'istanza Pino
  (porta 8089).

---

## 2026-03-14

### Added
- `docs/chirone-docs/git_organization.md` — documentazione dell'organizzazione
  git per il fork Chirone.
- `docs/chirone-docs/staging-server-setup.md` — guida setup server di staging.
- `docs/chirone-docs/superset_backup_strategies.md` — strategie di backup e
  versionamento dashboard.

---

## 2026-03-13 — Patch chart in tab (commit `efea95e`)

### Fixed
- `superset-frontend/src/dashboard/components/gridComponents/Tabs/Tabs.jsx` —
  aggiunto dispatch di `window.resize` dopo il cambio tab. I chart inizializzati
  in tab nascosti ricevono dimensioni zero; l'evento resize forza il ricalcolo.
- `superset-frontend/src/dashboard/components/gridComponents/Chart/Chart.jsx` —
  aggiunto `isComponentVisible` al comparator del memo di React. Senza questa
  patch React non ri-renderizza il chart quando il tab diventa visibile, perché
  il comparator non include la visibilità tra le dipendenze.

> **Patch essenziale** — va riapplicata ad ogni upgrade upstream. Verificare
> con `git show efea95e --name-only`.

---

## Patch attive (da preservare ad ogni upgrade)

| File | Commit | Motivo |
|------|--------|--------|
| `Tabs/Tabs.jsx` | `efea95e` | `window.resize` dopo cambio tab |
| `Chart/Chart.jsx` | `efea95e` | `isComponentVisible` nel memo comparator |
| `docker/docker-bootstrap.sh` | `f8b04e5` | psycopg2 su worker/beat |
