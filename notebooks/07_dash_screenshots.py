"""07b - Start the Dash app, take screenshots of each view, and print the numbers behind the findings.

Run:  python 07_dash_screenshots.py
"""
import os, sys, time, subprocess
import pandas as pd
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "..", "images")
df = pd.read_csv(os.path.join(HERE, "..", "data", "spacex_launch_dash.csv"))

# ---------- 1. Numbers behind the dashboard ----------
print("Success rate by launch site:")
site = df.groupby("Launch Site")["class"].agg(launches="count", successes="sum")
site["rate_%"] = (site["successes"] / site["launches"] * 100).round(1)
site["share_of_all_successes_%"] = (site["successes"] / site["successes"].sum() * 100).round(1)
print(site.sort_values("rate_%", ascending=False), "\n")

print("Success rate by payload range:")
df["Payload range"] = pd.cut(df["Payload Mass (kg)"], bins=[0, 2000, 4000, 6000, 8000, 10000],
                             include_lowest=True, right=False)
print(df.groupby("Payload range", observed=True)["class"].agg(launches="count", rate="mean").round(3), "\n")

print("Success rate by booster version category:")
print(df.groupby("Booster Version Category")["class"].agg(launches="count", rate="mean").round(3), "\n")

print("Payload 2000-5000 kg vs. other payloads:")
mid = df["Payload Mass (kg)"].between(2000, 5000)
print(f"  2000-5000 kg: {df[mid]['class'].mean():.1%} of {mid.sum()} launches")
print(f"  other:        {df[~mid]['class'].mean():.1%} of {(~mid).sum()} launches\n")

best_site = site["rate_%"].idxmax()

# ---------- 2. Screenshots ----------
app = subprocess.Popen([sys.executable, os.path.join(HERE, "07_dash_app.py")],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(8)  # wait for the server to start


def choose_site(page, label):
    page.locator("#site-dropdown").click()
    page.get_by_role("option", name=label, exact=True).click()
    page.wait_for_timeout(2500)


def set_payload(page, low, high):
    for cls, val in [("min", low), ("max", high)]:
        box = page.locator(f".dash-range-slider-{cls}-input")
        box.click()
        box.press("Control+A")
        box.type(str(val))
        box.press("Tab")              # leaving the box sends the new value to the app
        page.wait_for_timeout(800)
    page.wait_for_timeout(2500)


def snap(page, element_id, name):
    page.keyboard.press("Escape")
    page.mouse.move(2, 2, steps=10)   # move the mouse away so no tooltip covers the chart
    page.wait_for_timeout(1000)
    page.locator(f"#{element_id}").screenshot(path=os.path.join(IMG, name))
    print("saved", name)


try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # smaller window + 2x pixel density = bigger, sharper charts in the screenshots
        page = browser.new_page(viewport={"width": 1100, "height": 1500}, device_scale_factor=2)
        page.goto("http://127.0.0.1:8050")
        page.wait_for_timeout(5000)

        page.screenshot(path=os.path.join(IMG, "dash_0_full_dashboard.png"), full_page=True)
        print("saved dash_0_full_dashboard.png")
        snap(page, "success-pie-chart", "dash_1_pie_all_sites.png")
        snap(page, "success-payload-scatter-chart", "dash_3_scatter_all_payloads.png")

        set_payload(page, 0, 5000)
        snap(page, "success-payload-scatter-chart", "dash_4_scatter_low_payload.png")
        set_payload(page, 5000, 10000)
        snap(page, "success-payload-scatter-chart", "dash_5_scatter_high_payload.png")

        set_payload(page, 0, 10000)
        choose_site(page, best_site)
        snap(page, "success-pie-chart", "dash_2_pie_best_site.png")
        browser.close()
finally:
    app.terminate()
