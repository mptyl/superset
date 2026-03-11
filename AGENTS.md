# AGENTS.md

Indicazioni per lavorare su `chirone/superset/`.

## Natura del repository

Questa cartella e' un checkout del repository upstream Apache Superset, non un sottoprogetto custom Chirone.

## Regola principale

- Non applicare modifiche invasive o refactor "di progetto" qui dentro senza richiesta esplicita.
- Se il task riguarda il prodotto Superset in generale, segui i pattern e la documentazione upstream.
- Se il task riguarda l'integrazione con Chirone, privilegia configurazione, deployment e documentazione esterna invece di patchare il core upstream.

## Cosa e' lecito fare normalmente

- leggere il codice per capire limiti o punti di integrazione;
- verificare file di configurazione o compose locali;
- documentare come Chirone usa Superset.

## Cosa evitare

- cambiare API o componenti core senza motivazione chiara;
- introdurre convenzioni locali nel codice upstream;
- trattare questa directory come se fosse il punto principale della logica Chirone.
