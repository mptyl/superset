# Chirone Superset Runbook

Questo file documenta come Chirone usa il checkout upstream di Superset con una patch frontend versionata e riproducibile.

## Obiettivo

Garantire che:

- locale e produzione usino lo stesso commit o la stessa immagine buildata
- il frontend registri davvero i plugin chart richiesti da Chirone
- il runtime locale non resti in uno stato incompleto con solo `superset_app` attivo

## Modalita' locale

Con `DEV_MODE=true`, il setup docker upstream usa anche il servizio `superset-node`.
Per Chirone il servizio e' obbligatorio durante l'authoring locale delle dashboard.

Avvio consigliato:

```bash
cd /Users/mp/Chirone/chirone/superset
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

Verifica minima:

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml ps
curl -I http://localhost:8088/health
curl -I http://localhost:9000
```

Servizi attesi:

- `superset`
- `superset-node`
- `superset-worker`
- `superset-worker-beat`
- `db`
- `redis`

Nota:

- la build frontend Chirone include una patch per le dashboard a tab
- al cambio tab viene emesso un `window.resize`
- le chart memoizzate reagiscono anche al cambio `isComponentVisible`

## Produzione

Produzione non deve essere aggiornata con patch manuali nei container.

Regola:

1. si fissa un commit di questo repository
2. si builda l'immagine da quel commit
3. la stessa immagine viene promossa negli ambienti successivi
4. la patch frontend per le dashboard a tab deve restare inclusa nell'immagine

## Compatibilita' con Chirone ETL

Le dashboard-as-code di Chirone usano `viz_type` logici e delegano al compiler ETL la traduzione ai `viz_type` runtime di Superset 5.

Riferimento:

- [superset-local-production-parity.md](/Users/mp/Chirone/chirone/etl/docs/runbooks/superset-local-production-parity.md)
- [superset-git-roundtrip.md](/Users/mp/Chirone/chirone/etl/docs/runbooks/superset-git-roundtrip.md)

## Workflow operativo da preservare

Lato ETL esistono tre comandi che dipendono da questa build Superset:

```bash
cd /Users/mp/Chirone/chirone/etl
source .venv/bin/activate
chirone superset apply-local
chirone superset drift-check
chirone superset pull-back --output-dir /tmp/chirone-pullback
```

Questi comandi presuppongono che:

- il backend Superset risponda alle API `dataset`, `chart`, `dashboard`
- la build frontend locale e produzione gestiscano correttamente la dashboard a tab
- gli slug dashboard e i metadata chart restino stabili

Se in produzione si aggiorna Superset rompendo uno di questi presupposti, si rompe anche il round-trip Git/UI.

## File della patch frontend

- [Tabs.jsx](/Users/mp/Chirone/chirone/superset/superset-frontend/src/dashboard/components/gridComponents/Tabs.jsx)
- [Chart.jsx](/Users/mp/Chirone/chirone/superset/superset-frontend/src/dashboard/components/gridComponents/Chart.jsx)
- [Tabs.test.jsx](/Users/mp/Chirone/chirone/superset/superset-frontend/src/dashboard/components/gridComponents/Tabs.test.jsx)
- [Chart.test.jsx](/Users/mp/Chirone/chirone/superset/superset-frontend/src/dashboard/components/gridComponents/Chart.test.jsx)

## Badge `Development`

In locale e' normale vedere il badge rosso `Development` nell'header Superset:

- indica che il frontend e' servito dal development server
- non significa che la dashboard non sia pubblicata

In produzione il badge non deve comparire: la build deve essere servita come artifact stabile, non da dev server.
