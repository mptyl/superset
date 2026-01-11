# Strategie di Backup e Versionamento per Apache Superset

Questo documento delinea diverse strategie per gestire il ciclo di vita dei contenuti di Superset (Query SQL e Dashboard) come se fossero codice sorgente. L'obiettivo è permettere il salvataggio locale, il versionamento (es. tramite Git) e il backup delle dashboard e delle query senza dover modificare il codice sorgente di Superset.

## Introduzione

In un ambiente di produzione, è fondamentale trattare gli asset analitici (dashboard e query) con lo stesso rigore del codice applicativo. Questo permette di:
- **Tornare a versioni precedenti** in caso di errori.
- **Collaborare** in modo più efficace.
- **Migrare** facilmente contenuti tra ambienti diversi (es. da Sviluppo a Produzione).

Di seguito vengono presentate tre ipotesi di lavoro, in ordine di complessità e automazione.

---

## Ipotesi 1: Workflow basato su Export/Import (Manuale)
Questa è la soluzione nativa, ideale se non si desidera configurare script o automazioni complesse inizialmente.

### Per le Dashboard
Superset offre una funzione di **"Export"** nativa che include tutte le dipendenze necessarie.

1.  Navigare nella lista delle **Dashboards**.
2.  Selezionare le dashboard che si desidera salvare.
3.  Cliccare su **"Export"**.
4.  Si otterrà un file (solitamente `.zip` o `.yaml`) che contiene:
    *   La definizione della Dashboard (layout o json).
    *   Tutti i **Chart** collegati.
    *   Tutti i **Dataset** collegati (inclusi i campi calcolati, le metriche e le **query SQL** che definiscono i dataset virtuali).
5.  Scompattare o salvare questo file in una cartella locale (es. `my_superset_backup/dashboards/`) e committarlo su Git.

### Per gli SQL (Saved Queries)
Le query salvate in SQL Lab non vengono sempre incluse nell'export delle dashboard a meno che non siano state trasformate in Dataset.
*   **Azione:** Salvare manualmente le query importanti in file `.sql` locali.

---

## Ipotesi 2: CLI Automation (Approccio "GitOps")
Utilizzando Superset in ambiente Docker, è possibile sfruttare la riga di comando (CLI) per automatizzare l'export. Questo approccio è ideale per creare script di backup pianificati (es. cron job).

### Procedura
Si può creare uno script bash che esegue comandi direttamente verso il container di Superset.

Esempio concettuale di script:
```bash
# Esporta le dashboard in un file zip
docker exec -it superset_app superset export-dashboards -f /tmp/dashboard_export.zip

# Copia il file dal container al filesystem locale
docker cp superset_app:/tmp/dashboard_export.zip ./backup_locali/

# (Opzionale) Unzip e commit automatico su Git
unzip -o ./backup_locali/dashboard_export.zip -d ./repo_git/
cd ./repo_git && git add . && git commit -m "Auto-backup dashboards"
```

**Vantaggi:**
*   Il file zip risultante mantiene una struttura ordinata (`dashboards/`, `charts/`, `datasets/`, `databases/`).
*   Completamente automatizzabile.

---

## Ipotesi 3: Script Python via API (Massimo Controllo)
Per avere il massimo controllo e separare nettamente il codice SQL dai file di configurazione YAML/JSON, l'uso delle **API di Superset** è la soluzione raccomandata.

### Funzionamento
Uno script Python esterno può connettersi a Superset per scaricare selettivamente le risorse.

1.  **Autenticazione:** Lo script chiama l'endpoint `/api/v1/security/login` per ottenere un token di accesso.
2.  **Backup SQL:** Chiama l'endpoint `/api/v1/saved_query/` per ottenere tutte le query salvate.
    *   Lo script può salvare ogni query come un file puro `NomeQuery.sql`, ideale per la review e il versionamento.
3.  **Backup Dashboard:** Chiama gli endpoint di export per scaricare i bundle delle dashboard.

### Vantaggi
*   **SQL Pulito:** Si ottengono file `.sql` puri, non "annegati" in file di configurazione complessi.
*   **Flessibilità:** Possibilità di filtrare cosa scaricare (es. solo dashboard con un certo tag).
*   **Integrazione:** Facilmente integrabile in pipeline CI/CD.
