# Come contribuire a Mercurio Gestionale Retail

Grazie per l'interesse! Questo progetto è open source e i contributi sono benvenuti.

## Segnalare un Bug

1.  Controlla che il bug non sia già stato segnalato nelle [Issues](https://github.com/andreasalerno89/Mercurio-Gestionale-Retail/issues).
2.  Apri una nuova Issue descrivendo:
    *   Cosa stavi facendo.
    *   Cosa ti aspettavi succedesse.
    *   Cosa è successo invece (con screenshot o log se possibile).
    *   La tua versione di Python e del sistema operativo.

## Proporre una Nuova Funzionalità

Apri una Issue con etichetta `enhancement` spiegando la funzionalità e perché sarebbe utile per i piccoli esercenti.

## Inviare una Pull Request

1.  Apri prima una Issue per discutere la modifica (evita PR "a sorpresa").
2.  Fai un fork del repository.
3.  Crea un branch (`git checkout -b feature/nome-funzionalita`).
4.  Scrivi il codice seguendo lo stile del progetto (vedi sotto).
5.  Aggiungi o aggiorna i test se necessario.
6.  Assicurati che `python -m py_compile` funzioni su tutti i file modificati.
7.  Invia la PR con una descrizione chiara del problema risolto.

## Stile del Codice

*   **Solo standard library**: Mercurio non usa dipendenze esterne. Se pensi sia necessaria una libreria, chiedi prima.
*   **Import**: dentro `src/modules/`, usa import diretti (`from database import ...`), mai `from src...`.
*   **Logging**: usa il logger `mercurio.<modulo>` per ogni file.
*   **Database**: ogni nuova colonna va aggiunta sia nel `CREATE TABLE` sia nel blocco migrazioni in `database.py`.

## Domande?

Apri una Issue con etichetta `question` o scrivi nella sezione Discussions (se attiva).