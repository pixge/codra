# Codra

## Requisiti

- Python 3.10+
- Node.js 18+ (solo per il viewer)

## Installazione (core Python)

Assicurati che il tuo `python3.10` sia disponibile nel PATH.

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Esecuzione CLI

Analizza un percorso e stampa il report JSON su stdout:

```bash
python3 -m codra.cli.main /percorso/progetto
```

Esempio con soglie:

```bash
python3 -m codra.cli.main /percorso/progetto --threshold-csa 10 --threshold-id 2 --threshold-bps 0.7
```

Esempio con log e file di output:

```bash
python3 -m codra.cli.main /percorso/progetto --log-level DEBUG --output report.json
```

## Viewer React (opzionale)

```bash
cd viewer
npm install
npm run dev
```

Carica il file JSON generato dalla CLI tramite il file input dell'interfaccia.
