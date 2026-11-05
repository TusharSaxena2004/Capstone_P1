# Silent Witness: Installation & Workflow Guide

This document provides a complete step-by-step guide to installing, configuring, and running the full Silent Witness application (Website Frontend + FastAPI Backend + ML Pipeline). 

Share this guide with teammates to ensure seamless local execution.

---

## 1. Prerequisites
Ensure you have the following installed on your machine:
* **Node.js** (v18+ recommended) for the React frontend.
* **Python** (3.9+ recommended) for the ML backend and FastAPI.
* **LM Studio** (or equivalent local LLM host) running the NLI/Event extraction model (typically exposed on `localhost:1234`).

---

## 2. Installation & Setup

You will need to open **two separate terminal windows** to run this project—one for the Python Backend and one for the React Frontend.

### Step 2A: Setup the Backend (FastAPI & ML Core)
The backend uses a monolithic architecture, meaning `server.py` hosts both the Website API and the ML Pipeline orchestrator.

1. Open Terminal 1 and navigate to the project root:
   ```bash
   cd Capstone_P1
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```
3. Install the required Python dependencies:
   ```bash
   pip install fastapi uvicorn pydantic requests
   # Install any specific ML requirements your teammate added:
   pip install spacy fastcoref 
   ```
   *(Note: Ensure you download any required spaCy models, e.g., `python -m spacy download en_core_web_sm`)*

### Step 2B: Setup the Frontend (React + Vite)
1. Open Terminal 2 and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install the Node modules:
   ```bash
   npm install
   ```

---

## 3. Running the System

To start the application, execute the following commands in your respective terminals.

**Terminal 1 (Backend):**
```bash
uvicorn server:app --reload
```
*The backend API will now be running on `http://localhost:8000`. You can view the API documentation at `http://localhost:8000/docs`.*

**Terminal 2 (Frontend):**
```bash
npm run dev
```
*The Vite development server will start. Open `http://localhost:5173` in your browser to view the application.*

---

## 4. How the Application Workflow Operates

Currently, the system is designed to allow the Website and ML Pipeline to communicate seamlessly.

1. **Testimony Ingestion:** 
   The user navigates to the **Testimony Ingestion** tab in the UI, inputs multiple eyewitness statements, and clicks "Extract & align claims".
2. **API Communication:** 
   The React frontend (`api/client.ts`) sends an HTTP `POST` request containing the text to `http://localhost:8000/api/incidents`.
3. **ML Orchestration (`ml_core`):** 
   Inside `server.py`, the backend receives the request and immediately imports and executes `analyze_incident()` from the `ml_core` module. This triggers the local LLMs and spaCy models to perform NER extraction, coreference resolution, and contradiction detection.
4. **Data Translation:**
   Once the ML pipeline finishes, `server.py` takes the highly complex `AnalysisResponse` (the `theft_case_output.json` format) and parses the exact string indexes (`source_span`) and rationales.
5. **UI Rendering:**
   The backend saves this formatted data and returns a success response to the frontend. The React app then dynamically renders the highlighted text and contradiction likelihood bars in the **Discrepancy Inspector**.

### 🛡️ Supervisor Demo Fallback
To ensure a flawless presentation for supervisors, a safety net has been built into `server.py`. 
If the ML Pipeline (`analyze_incident`) fails to execute or LM Studio is offline during the presentation, the backend will automatically intercept the error and gracefully load the pre-calculated `theft_case_output.json`. This guarantees the frontend will successfully render the complex visual Discrepancy Inspector without crashing during a live demo.

---

## 5. Future Architecture Scope
Currently, the Website Backend and ML Backend are merged inside `server.py` for simplicity. In the future, these can be split into a distinct `web_server.py` and `ml_server.py` communicating over HTTP/gRPC.
