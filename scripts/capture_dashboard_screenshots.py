"""
capture_dashboard_screenshots.py
--------------------------------
Purpose:
    Automates high-resolution screenshot capture of the Streamlit Executive Dashboard
    using Playwright with Google Chrome.
    Captures:
      1. images/dashboard_full.png
      2. images/kpi_section.png
      3. images/revenue_and_segments.png
      4. images/filtered_view.png
      5. images/segmentation_tab.png
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def capture_all() -> None:
    print("Launching Chrome for high-res dashboard screenshot capture...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=True,
            args=["--disable-gpu", "--no-sandbox"],
        )
        # 1680x1050 viewport with 2x retina clarity
        context = browser.new_context(
            viewport={"width": 1680, "height": 1050},
            device_scale_factor=2,
        )
        page = context.new_page()

        print("Navigating to http://localhost:8501 ...")
        page.goto("http://localhost:8501", wait_until="networkidle")

        # Wait for Streamlit initial render
        page.wait_for_selector(".executive-header", timeout=30000)
        page.wait_for_selector(".kpi-container", timeout=30000)
        time.sleep(3)

        # -------------------------------------------------------------
        # 1. Full Dashboard Screenshot (Full Page)
        # -------------------------------------------------------------
        print("Measuring page dimensions for dashboard_full.png ...")
        # Measure true scroll height of the main content
        full_height = page.evaluate("""() => {
            const el = document.querySelector('[data-testid="stMainBlockContainer"]') || document.querySelector('section.main') || document.body;
            return Math.max(el.scrollHeight, document.body.scrollHeight, 2600);
        }""")
        print(f"Detected full page height: {full_height}px")
        
        # Expand viewport height so the entire page is visible without scrolling
        page.set_viewport_size({"width": 1680, "height": int(full_height) + 100})
        time.sleep(2)
        
        print("Capturing 1/5: dashboard_full.png ...")
        page.screenshot(
            path=str(IMAGES_DIR / "dashboard_full.png"),
            full_page=False,
        )

        # Reset viewport to standard 1680x1050
        page.set_viewport_size({"width": 1680, "height": 1050})
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)

        # -------------------------------------------------------------
        # 2. KPI Section Screenshot
        # -------------------------------------------------------------
        print("Capturing 2/5: kpi_section.png ...")
        # Header banner + tabs + 5 KPI cards
        page.screenshot(
            path=str(IMAGES_DIR / "kpi_section.png"),
            clip={"x": 340, "y": 0, "width": 1300, "height": 475},
        )

        # -------------------------------------------------------------
        # 3. Revenue & Segments Middle Section Screenshot
        # -------------------------------------------------------------
        print("Capturing 3/5: revenue_and_segments.png ...")
        # Middle row containing 3 cards: Trend, Segment Revenue, Category Revenue
        page.screenshot(
            path=str(IMAGES_DIR / "revenue_and_segments.png"),
            clip={"x": 340, "y": 485, "width": 1300, "height": 475},
        )

        # -------------------------------------------------------------
        # 4. Filtered View (Region Filter = North)
        # -------------------------------------------------------------
        print("Navigating to http://localhost:8501/?region=North ...")
        page.goto("http://localhost:8501/?region=North", wait_until="networkidle")
        page.wait_for_selector(".executive-header", timeout=30000)
        page.wait_for_selector(".kpi-container", timeout=30000)
        time.sleep(3)

        print("Capturing 4/5: filtered_view.png ...")
        page.screenshot(
            path=str(IMAGES_DIR / "filtered_view.png"),
            clip={"x": 0, "y": 0, "width": 1680, "height": 980},
        )

        # -------------------------------------------------------------
        # 5. Segmentation Tab Screenshot
        # -------------------------------------------------------------
        print("Navigating back to standard view...")
        page.goto("http://localhost:8501", wait_until="networkidle")
        page.wait_for_selector(".executive-header", timeout=30000)
        time.sleep(2)

        print("Switching to 'Segments (RFM)' tab...")
        tabs = page.get_by_role("tab").all()
        if len(tabs) >= 2:
            tabs[1].click()
            time.sleep(3)

        # Measure segmentation tab content height
        seg_height = page.evaluate("""() => {
            const el = document.querySelector('[data-testid="stMainBlockContainer"]') || document.querySelector('section.main') || document.body;
            return Math.max(el.scrollHeight, 1250);
        }""")
        print(f"Detected segmentation tab height: {seg_height}px")
        page.set_viewport_size({"width": 1680, "height": int(seg_height) + 100})
        time.sleep(2)
        page.evaluate("window.scrollTo(0, 0)")

        print("Capturing 5/5: segmentation_tab.png ...")
        page.screenshot(
            path=str(IMAGES_DIR / "segmentation_tab.png"),
            clip={"x": 340, "y": 0, "width": 1300, "height": int(seg_height) + 20},
        )

        browser.close()
        print("Successfully captured all 5 screenshots!")


if __name__ == "__main__":
    capture_all()
