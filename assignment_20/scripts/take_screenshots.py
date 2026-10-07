import os

from PIL import Image
from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
OUT = "static/img/shots"
os.makedirs(OUT, exist_ok=True)


def snap(page, name, full=False):
    page.screenshot(path=f"{OUT}/{name}.png", full_page=full)
    Image.open(f"{OUT}/{name}.png").save(f"{OUT}/{name}.webp", "WEBP", quality=90)
    os.remove(f"{OUT}/{name}.png")


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
    page.set_default_timeout(120000)
    page.goto(f"{BASE}/accounts/login/", wait_until="domcontentloaded")
    page.wait_for_selector("input[name=username]")
    page.fill("input[name=username]", os.environ["DEMO_STAFF_USER"])
    page.fill("input[name=password]", os.environ["DEMO_STAFF_PASSWORD"])
    page.click("button[type=submit]")
    page.wait_for_url("**/dashboard/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    snap(page, "dashboard")
    page.goto(f"{BASE}/students/", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    snap(page, "students")
    page.goto(f"{BASE}/students/?q=Adaeze", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    page.click("tbody tr:first-child a")
    page.wait_for_load_state("networkidle")
    snap(page, "student-detail")
    browser.close()
