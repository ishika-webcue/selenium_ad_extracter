require("dotenv").config();
const express = require("express");
const { exec } = require("child_process");
const path = require("path");
const fs = require("fs");

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "public"))); // for frontend files

// Config from .env
const PORT = process.env.PORT || 3000;
const PYTHON_PATH = process.env.PYTHON_PATH || "python";
const PYTHON_SCRIPT = process.env.PYTHON_SCRIPT || path.join(__dirname, "automated_ad_collector.py");
const CSV_FILE = process.env.CSV_FILE || path.join(__dirname, "ad_data_collection.csv");

// ---------------------------
// Run Python Collector
// ---------------------------
app.post("/api/run-collector", (req, res) => {
    const { url, maxPages, csvFile, headless } = req.body;

    if (!url) return res.status(400).json({ error: "URL is required" });

    // Final CSV path
    const finalCsvFile = csvFile
        ? path.join(__dirname, csvFile)
        : CSV_FILE;

    // Delete old CSV
    if (fs.existsSync(finalCsvFile)) fs.unlinkSync(finalCsvFile);

    // Build Python command
    let cmd = `"${PYTHON_PATH}" "${PYTHON_SCRIPT}" --url "${url}" --csv-file "${finalCsvFile}"`;
    if (maxPages) cmd += ` --max-pages ${maxPages}`;
    if (headless) cmd += " --headless";

    console.log("⚡ Running:", cmd);

    let logs = "";

    // Execute Python
    const child = exec(cmd, (error, stdout, stderr) => {
        if (stdout) logs += `\n${stdout}`;
        if (stderr) logs += `\n${stderr}`;

        if (error) {
            logs += `\n❌ Error: ${error.message}`;
            return res.status(500).json({ success: false, logs });
        }

        // Success: return logs + download link
        if (fs.existsSync(finalCsvFile)) {
            return res.json({
                success: true,
                logs,
                download: `/download/${path.basename(finalCsvFile)}`
            });
        } else {
            return res.status(500).json({ success: false, logs: logs + "\nCSV not generated" });
        }
    });

    // Capture live logs
    child.stdout.on("data", (data) => {
        logs += data.toString();
    });

    child.stderr.on("data", (data) => {
        logs += data.toString();
    });
});

// ---------------------------
// File Download Route
// ---------------------------
app.get("/download/:filename", (req, res) => {
    const filePath = path.join(__dirname, req.params.filename);
    if (fs.existsSync(filePath)) {
        res.download(filePath);
    } else {
        res.status(404).send("File not found");
    }
});

// ---------------------------
// Start Server
// ---------------------------
app.listen(PORT, () =>
    console.log(`🚀 Server running on http://localhost:${PORT}`)
);
