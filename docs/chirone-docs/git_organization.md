# Organizzazione Git del Progetto Chirone-Superset

Questo documento descrive come è configurato il sistema di versionamento Git per questo progetto, spiegando la relazione tra il repository ufficiale (Apache), il fork personale e l'ambiente di lavoro locale.

## Architettura dei Repository (I tre livelli)

La struttura è organizzata per permettere lo sviluppo di funzionalità personalizzate (file chirone) mantenendo allo stesso tempo la possibilità di ricevere aggiornamenti ufficiali da Apache.

1.  **Upstream (A Monte):** `https://github.com/apache/superset.git`
    *   È il repository ufficiale gestito dalla fondazione Apache.
    *   Serve solo come sorgente per gli aggiornamenti. Non scriveremo mai direttamente qui.
2.  **Origin (Il tuo Fork):** `https://github.com/mptyl/superset.git`
    *   È la tua copia personale su GitHub.
    *   È dove risiedono i tuoi backup remoti e dove carichi le modifiche (push) per metterle al sicuro.
3.  **Local (Il tuo PC):**
    *   L'ambiente di lavoro dove modifichi i file.
    *   È collegato a entrambi i repository sopra citati.

---

## Comandi per l'Aggiornamento (Sync con Apache)

Per mantenere la tua versione allineata con l'ultima release ufficiale di Superset, segui questi passaggi nel terminale:

### 1. Scaricare le novità da Apache
```bash
git fetch upstream
```

### 2. Sincronizzare il master locale
Se ti trovi sul branch `master` e vuoi le ultime novità ufficiali:
```bash
git checkout master
git merge upstream/master
```

### 3. Aggiornare il tuo fork su GitHub
```bash
git push origin master
```

---

## Gestione delle Personalizzazioni (Chirone)

Le personalizzazioni (documentazione, script SQL, dashboard export) vengono gestite preferibilmente in branch dedicati o cartelle specifiche che non confliggono con il core di Superset.

*   **Branch Corrente di Sviluppo:** `feature/backup-docs`
*   **Cartella Documentazione:** `docs/chirone-docs/`

### Workflow consigliato per nuove modifiche:
1. Crea un branch: `git checkout -b nome-funzione`
2. Lavora sui file.
3. Fai il commit: `git commit -m "descrizione"`
4. Carica sul tuo fork: `git push origin nome-funzione`

In questo modo, anche se Superset aggiorna migliaia di file, i tuoi file dentro `docs/chirone-docs/` rimarranno intatti e facili da gestire.
