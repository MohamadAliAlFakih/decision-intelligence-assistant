# Decision Intelligence Assistant — Frontend

React frontend for the four-way AI comparison tool. Sends customer support queries to the FastAPI backend and displays RAG, non-RAG, ML classifier, and LLM zero-shot results side by side.

## Stack

- React 18 + Vite
- Tailwind CSS v4
- Nginx (production container)

## Structure

```
src/
├── App.jsx                  # Root component — fetches /query, manages state
├── components/
│   ├── QueryInput.jsx       # Text input + submit button
│   ├── ResultCard.jsx       # Single answer card (RAG or non-RAG)
│   └── ComparisonTable.jsx  # Side-by-side ML vs LLM priority comparison
```

## Development

Requires the backend running at `http://localhost:8000`.

```bash
npm install
npm run dev
```

Open `http://localhost:5173`.

## Production (Docker)

Built and served via the root `docker-compose.yml`:

```bash
docker compose up --build
```

Frontend available at `http://localhost:3000`.