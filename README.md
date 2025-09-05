# Selenium Ad Extracter - Node + Express Server

This repository runs the `automated_ad_collector.py` Python scraper from a Node + Express server, streams logs to the browser (Server-Sent Events), and provides a CSV download when scraping completes.

What was added/updated

- `server.js` - Express server that starts the Python scraper, streams logs via SSE, and exposes `/download-csv`.
- `frontend.html` - simple form and output area to start the scraper and receive logs.
- `package.json` - already contains `start` script (`node server.js`).

Quick start (Windows PowerShell)

1. Install Node dependencies (use PowerShell):

```powershell
cd 'C:\Users\dell\Desktop\s_ad'
npm install
```

2. Ensure Python environment is available with Selenium and a compatible Chrome/Chromium + chromedriver.

- Create/activate a venv and install selenium, for example:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install selenium
```

- If you use a virtual environment, set the `PYTHON_PATH` environment variable so the Node server uses that Python executable:

```powershell
$env:PYTHON_PATH = "C:\Users\dell\Desktop\s_ad\.venv\Scripts\python.exe"
```

3. Start the Node server:

```powershell
npm start
# or
node server.js
```

4. Open the frontend in a browser:

- Visit: http://localhost:3000
- Fill the form (URL, Max Pages, CSV filename, Headless) and click "Run Collector".
- The page will display logs streamed from the Python process. When the server sends the `[DONE]` message the CSV will be downloaded automatically.

API endpoints

- POST /start-collector
  - body: { url, max_pages, csv, headless }
  - Starts the Python scraper.
- GET /collector-stream
  - SSE endpoint that streams log lines from the Python scraper.
- GET /download-csv?filename=your.csv
  - Downloads the generated CSV file.

Troubleshooting

- If the server responds `started` but nothing happens, make sure the Python executable is correct and has `selenium` installed.
- If scraping fails due to browser/driver issues, ensure Chrome/Chromium and chromedriver are compatible versions and chromedriver is reachable from the Python environment.
- Logs are forwarded from Python stdout/stderr; check terminal where Node is running for additional errors.

Change PYTHON executable used by server

- The server will use the `PYTHON_PATH` environment variable if set, otherwise `PYTHON` env var or `python` on PATH.

Security note

- This server runs arbitrary scraping code. Do not expose it to the public internet without proper access controls.

If you want, I can add a preflight endpoint that validates Python + Selenium + ChromeDriver before launching the scraper, or enhance the frontend UI.
