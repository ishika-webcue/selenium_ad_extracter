import os
import sys
import time
import shutil
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def ensure_directory(path: Path) -> Path:

    path.mkdir(parents=True, exist_ok=True)
    return path


def configure_chrome_with_extension(
    extension_path: Path,
    download_dir: Path,
    headless: bool = True,
) -> webdriver.Chrome:

    chrome_options = Options()

    # New headless supports extensions; can be disabled via flag
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    )

    # Load the extension: support unpacked dir and packed .crx
    if extension_path.is_dir():
        chrome_options.add_argument(f"--disable-extensions-except={extension_path}")
        chrome_options.add_argument(f"--load-extension={extension_path}")
    else:
        # If this is a CRX file, add it as an extension
        if extension_path.suffix.lower() == ".crx":
            chrome_options.add_extension(str(extension_path))
        else:
            raise ValueError(f"Unsupported extension path: {extension_path}")

    # Set a persistent user data dir so the extension can initialize cleanly
    user_data_dir = download_dir.parent / "chrome_profile"
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

    # Ensure downloads work in headless mode
    prefs = {
        "download.default_directory": str(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)

    # Enable downloads in headless via CDP
    driver.execute_cdp_cmd(
        "Page.setDownloadBehavior",
        {"behavior": "allow", "downloadPath": str(download_dir)},
    )

    # Best-effort stealth tweak
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                """,
            },
        )
    except Exception:
        pass

    return driver


def wait_for_extension_content_button(driver: webdriver.Chrome, timeout_seconds: int = 30) -> None:

    WebDriverWait(driver, timeout_seconds).until(
        EC.presence_of_element_located((By.ID, "nb-export-ads-btn"))
    )


def try_force_inject_button(driver: webdriver.Chrome) -> None:

    driver.execute_script(
        """
        try {
            if (typeof window.injectExportButton === 'function') {
                window.injectExportButton();
            }
        } catch (e) {}
        """
    )


def wait_for_csv_download(download_dir: Path, timeout_seconds: int = 30) -> Path:

    end_time = time.time() + timeout_seconds
    latest_csv: Path | None = None
    while time.time() < end_time:
        # Ignore temporary .crdownload files
        csv_files = [f for f in download_dir.glob("*.csv") if not f.name.endswith(".crdownload")]
        if csv_files:
            # Pick the newest
            latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
            # Extra small wait to ensure the file is fully finalized
            time.sleep(0.5)
            return latest_csv
        time.sleep(0.5)
    raise TimeoutError("CSV download did not appear in time")


def main():

    workspace = Path(__file__).resolve().parent
    # Default: load the extension from this folder
    extension_path = workspace
    # Optional CLI args:
    #   --extension-dir=C:\path\to\unpacked
    #   --crx=C:\path\to\packed.crx
    for arg in sys.argv[1:]:
        if arg.startswith("--extension-dir="):
            extension_path = Path(arg.split("=", 1)[1]).expanduser().resolve()
        elif arg.startswith("--crx="):
            extension_path = Path(arg.split("=", 1)[1]).expanduser().resolve()
    download_dir = ensure_directory(workspace / "downloads")

    # Basic validation that this looks like an extension dir
    if extension_path.is_dir():
        manifest_path = extension_path / "manifest.json"
        if not manifest_path.exists():
            print(f"manifest.json not found in {extension_path}. Exiting.")
            sys.exit(1)

    # First attempt: headless
    driver = configure_chrome_with_extension(extension_path, download_dir, headless=True)
    try:
        # Visit NewsBreak; your content script matches both domains
        driver.get("https://www.newsbreak.com/")

        # Wait for the content script to inject the Export button
        try:
            wait_for_extension_content_button(driver, timeout_seconds=45)
        except Exception:
            # Try to force reinjection once and wait again briefly
            try_force_inject_button(driver)
            wait_for_extension_content_button(driver, timeout_seconds=15)

        # Click the Export Ads CSV button
        export_button = driver.find_element(By.ID, "nb-export-ads-btn")
        export_button.click()

        # Wait for CSV file to appear in download folder
        csv_path = wait_for_csv_download(download_dir, timeout_seconds=60)
        print(f"CSV downloaded: {csv_path}")

    except Exception as headless_err:
        # Fallback: rerun in visible mode to allow extension UI to initialize
        driver.quit()
        driver = configure_chrome_with_extension(extension_path, download_dir, headless=False)
        try:
            driver.get("https://www.newsbreak.com/")
            try:
                wait_for_extension_content_button(driver, timeout_seconds=45)
            except Exception:
                try_force_inject_button(driver)
                wait_for_extension_content_button(driver, timeout_seconds=20)
            driver.find_element(By.ID, "nb-export-ads-btn").click()
            csv_path = wait_for_csv_download(download_dir, timeout_seconds=60)
            print(f"CSV downloaded (fallback visible): {csv_path}")
        finally:
            driver.quit()
        return
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()


