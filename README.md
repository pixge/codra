# Codra

## Requisiti

- Python 3.10+
- Node.js 18+ (solo per il viewer)

## Installazione (core Python)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Esecuzione CLI

Analizza un percorso e stampa il report JSON su stdout:

```bash
python -m codra.cli /percorso/progetto
```

Esempio con soglie:

```bash
python -m codra.cli /percorso/progetto --threshold-csa 10 --threshold-id 2 --threshold-bps 0.7
```

## Viewer React (opzionale)

```bash
cd viewer
npm install
npm run dev
```

Carica il file JSON generato dalla CLI tramite il file input dell'interfaccia.
