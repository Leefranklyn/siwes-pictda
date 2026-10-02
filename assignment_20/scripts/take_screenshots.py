import os

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
OUT = "static/img/shots"
os.makedirs(OUT, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
    page.goto(f"{BASE}/accounts/login/")
    page.fill("input[name=username]", os.environ["DEMO_STAFF_USER"])
    page.fill("input[name=password]", os.environ["DEMO_STAFF_PASSWORD"])
    page.click("button[type=submit]")
    page.wait_for_url("**/dashboard/")
    page.wait_for_timeout(1500)
    page.screenshot(path=f"{OUT}/dashboard.png")
    page.goto(f"{BASE}/students/")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=f"{OUT}/students.png")
    page.goto(f"{BASE}/students/?q=Adaeze")
    page.wait_for_load_state("networkidle")
    page.click("tbody tr:first-child a")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=f"{OUT}/student-detail.png")
    browser.close()
