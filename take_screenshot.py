import subprocess
import time
import os
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print("Starting server...")
server = subprocess.Popen(
    [".venv\\Scripts\\python.exe", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8420"],
    cwd=BASE_DIR
)

time.sleep(3) # wait for startup

try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 800})
        
        # screenshot home
        print("Screenshotting home page...")
        page.goto("http://127.0.0.1:8420")
        page.screenshot(path=os.path.join(BASE_DIR, "docs", "screenshot_home.png"), full_page=True)
        
        # screenshot cases
        print("Screenshotting cases page...")
        page.goto("http://127.0.0.1:8420/cases")
        page.screenshot(path=os.path.join(BASE_DIR, "docs", "screenshot_cases.png"), full_page=True)
        
        browser.close()
        print("Screenshots taken.")
finally:
    print("Terminating server...")
    server.terminate()
