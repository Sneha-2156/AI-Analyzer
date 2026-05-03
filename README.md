# AI Analyzer

AI Analyzer is a full-stack past-paper analysis tool that helps students turn exam papers into actionable revision insights. It extracts text from uploaded files, groups questions into syllabus topics, highlights high-yield areas, and generates a day-by-day study plan.

## What it does

- Upload a `.pdf` or `.txt` past paper
- Extract question text on the backend
- Classify questions against a pasted syllabus using the OpenAI API
- Aggregate topic frequency, marks, and trend-style scores
- Visualize topic frequency in a dashboard
- Generate a study plan from the analyzed topic data
- Load demo data from bundled sample files if you just want to try the app

## Tech stack

- Frontend: Next.js 15, React 19, TypeScript, Tailwind CSS, Recharts
- Backend: FastAPI, Pydantic, PyPDF
- AI integration: OpenAI Python SDK
- Testing: Pytest

## Project structure

```text
AiAnalyzer/
  backend/
    app/
    sample_data/
    tests/
    requirements.txt
  frontend/
    app/
    components/
    lib/
    public/demo/
    package.json
```

## How it works

1. The frontend upload page sends a file to `POST /extract`.
2. The backend extracts text from PDF or plain text uploads.
3. The frontend sends extracted paper text plus a syllabus to `POST /analyze`.
4. The backend extracts questions, classifies them into topics, and builds topic statistics.
5. The dashboard reads the last analysis from session storage and shows topic charts and ranked topics.
6. The planner sends topic stats to `POST /plan` and receives a merged AI + rules-based study plan.

## Requirements

- Node.js 18+ recommended
- Python 3.11+ recommended
- An OpenAI API key for AI-powered classification and plan generation

## Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create an environment variable before starting the API:

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

Optional model override:

```powershell
$env:OPENAI_MODEL="gpt-4o-mini"
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

The API will run on `http://127.0.0.1:8000`.

## Frontend setup

```bash
cd frontend
npm install
```

Optional frontend API override:

```powershell
$env:NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"
```

Start the frontend:

```bash
npm run dev
```

The app will run on `http://localhost:3000`.

## API endpoints

- `GET /health`: health check
- `POST /extract`: accepts uploaded `.pdf` or `.txt` files and returns extracted text plus a success/failed status
- `POST /analyze`: accepts paper text and syllabus text, returns classified questions and topic statistics
- `POST /plan`: accepts topic stats and a day count, returns a generated study plan

## Notes on extraction

- PDF extraction uses `pypdf` by default.
- If a PDF yields too little text, the backend can fall back to OCR logic if `pytesseract` and `pdf2image` are installed.
- OCR dependencies are optional and are not included in `backend/requirements.txt`.

## Demo flow

You can click `Try Demo Data` on the upload page to load the sample papers and sample syllabus from `frontend/public/demo/`.

## Running tests

```bash
cd backend
pytest
```

## Current behavior and limitations

- The dashboard stores the last analysis in browser `sessionStorage`, so results are session-based rather than persisted server-side.
- If no `OPENAI_API_KEY` is set or model output fails validation, the backend falls back to simpler rule-based behavior where possible.
- Topic classification quality depends heavily on the pasted syllabus and the clarity of the extracted paper text.
- CORS is currently configured for local frontend development on port `3000`.

## Sample use case

1. Start the backend and frontend.
2. Open the upload page.
3. Upload a past paper or use demo data.
4. Paste a syllabus.
5. Run analysis.
6. Review topic frequency and high-yield topics in the dashboard.
7. Generate a study plan from the planner page.

## Future improvements

- Persist analysis history in a database
- Support drag-and-drop uploads and multiple papers in one run
- Add OCR dependencies as an optional documented install path
- Export study plans and dashboard summaries
- Improve classification prompts and topic normalization
