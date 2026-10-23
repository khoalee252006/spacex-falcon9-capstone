"""Build the final deck "Data Science Capstone Project Report" (16:9 PPTX + speaker notes + PDF).

Every number on the slides is computed here from the project data / notebook outputs,
so the slides always match the code that was run.

Run:  python build_slides.py      (needs python-pptx; PDF export uses Microsoft PowerPoint on Windows)
"""
import os, re, json, sqlite3
import pandas as pd
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA, IMG, NB = (os.path.join(ROOT, d) for d in ("data", "images", "notebooks"))

REPO = "https://github.com/khoalee252006/spacex-falcon9-capstone"
NB_URL = {k: f"{REPO}/blob/main/notebooks/{v}" for k, v in {
    "api": "01_data_collection_api.ipynb", "scrape": "02_data_collection_webscraping.ipynb",
    "wrangle": "03_data_wrangling.ipynb", "viz": "04_eda_visualization.ipynb", "sql": "05_eda_sql.ipynb",
    "folium": "06_interactive_folium_map.ipynb", "dash": "07_dash_app.py", "ml": "08_predictive_analysis.ipynb"}.items()}

# ---------------------------------------------------------------- facts (all computed) --
df = pd.read_csv(os.path.join(DATA, "dataset_part_2.csv"))
df["Year"] = pd.to_datetime(df["Date"]).dt.year
F = {}
F["n"] = len(df)
F["landed"] = int(df["Class"].sum())
F["rate"] = df["Class"].mean()
F["years"] = (df["Year"].min(), df["Year"].max())
yearly = df.groupby("Year")["Class"].mean()
F["yearly"] = yearly
orbit = df.groupby("Orbit")["Class"].agg(["mean", "count"])
site = df.groupby("LaunchSite")["Class"].agg(["mean", "count"])
attempted = df["Outcome"].str.startswith(("True", "False"))
F["no_attempt"] = int((~attempted).sum())
F["attempt_fail"] = int((attempted & (df["Class"] == 0)).sum())
F["attempted"] = int(attempted.sum())
F["attempt_rate"] = df[attempted]["Class"].mean()
blk_att = df[attempted].groupby("Block")["Class"].mean()
no_try = df[~attempted]
F["no_try_gto"] = int((no_try["Orbit"] == "GTO").sum())
F["no_try_2018"] = int((no_try["Year"] == 2018).sum())
reused = df.groupby("Reused")["Class"].mean()
first30, last30 = df.head(30)["Class"].mean(), df.tail(30)["Class"].mean()
outcomes = df["Outcome"].value_counts()
p1 = pd.read_csv(os.path.join(DATA, "dataset_part_1.csv"))
p3 = pd.read_csv(os.path.join(DATA, "dataset_part_3.csv"))
scraped = pd.read_csv(os.path.join(DATA, "spacex_web_scraped.csv"))
pct = lambda x: f"{x * 100:.1f}%"
pct0 = lambda x: f"{x * 100:.0f}%"


def nb_text(name):
    """All text output of a notebook (stdout + text/plain), joined."""
    nb = json.load(open(os.path.join(NB, name), encoding="utf-8"))
    out = []
    for c in nb["cells"]:
        for o in c.get("outputs", []):
            if o["output_type"] == "stream":
                out.append("".join(o["text"]))
            elif "data" in o and "text/plain" in o["data"]:
                out.append("".join(o["data"]["text/plain"]))
    return "\n".join(out)


# notebook 01: missing payloads + mean used
t1 = nb_text("01_data_collection_api.ipynb")
F["payload_missing"] = int(re.search(r"PayloadMass\s+(\d+)", t1).group(1))
F["payload_mean"] = float(re.search(r"mean payload mass used to fill: ([\d.]+)", t1).group(1))
F["landingpad_missing"] = int(p1["LandingPad"].isnull().sum())
same_cols = [m for m in re.findall(r"(\w+)\s+rows that differ: (\d+)", t1)]
F["cols_identical"] = sum(1 for _, d in same_cols if d == "0")
F["cols_total"] = len(same_cols)

# notebook 08: model results
t8 = nb_text("08_predictive_analysis.ipynb")
models = []
for m in re.finditer(r"^(Logistic Regression|SVM|Decision Tree|KNN)\s+val=([\d.]+)\s+test=([\d.]+)\s+(\{.*\})$", t8, re.M):
    params = re.sub(r"np\.float64\(([\d.e-]+)\)", lambda g: f"{float(g.group(1)):.3g}", m.group(4))
    models.append({"Model": m.group(1), "val": float(m.group(2)), "test": float(m.group(3)), "params": params})
cms = {m.group(1): tuple(int(x) for x in m.groups()[1:]) for m in
       re.finditer(r"^(Logistic Regression|SVM|Decision Tree|KNN)\s+TN=(\d+) FP=(\d+) FN=(\d+) TP=(\d+)", t8, re.M)}
cvs = {m.group(1).strip(): (float(m.group(2)), float(m.group(3))) for m in
       re.finditer(r"^\s*(Logistic Regression|SVM|Decision Tree|KNN)\s+([\d.]+)\s+([\d.]+)\s*$", t8, re.M)}
F["test_n"] = int(re.search(r"test samples: (\d+)", t8).group(1))
F["train_n"] = int(re.search(r"train samples: (\d+)", t8).group(1))
best_val = max(models, key=lambda m: m["val"])
best_test = max(m["test"] for m in models)
tied = [m["Model"] for m in models if m["test"] == best_test]

# notebook 06: proximity table
t6 = nb_text("06_interactive_folium_map.ipynb")
prox = {}
for m in re.finditer(r"^\d+\s+(CCAFS LC-40|CCAFS SLC-40|KSC LC-39A|VAFB SLC-4E)\s+(coastline|railway|highway|city)\s+(.+?)\s+([\d.]+)$", t6, re.M):
    prox[(m.group(1), m.group(2))] = (m.group(3), float(m.group(4)))

# Dash data
dash = pd.read_csv(os.path.join(DATA, "spacex_launch_dash.csv"))
dsite = dash.groupby("Launch Site")["class"].agg(["count", "sum", "mean"])
dsite["share"] = dsite["sum"] / dsite["sum"].sum()
dsite = dsite.sort_values("mean", ascending=False)
dash["range"] = pd.cut(dash["Payload Mass (kg)"], bins=[0, 2000, 4000, 6000, 8000, 10000], include_lowest=True, right=False)
drange = dash.groupby("range", observed=True)["class"].agg(["count", "mean"])
dboost = dash.groupby("Booster Version Category")["class"].agg(["count", "mean"])
best_range = drange["mean"].idxmax()

# SQL (same queries as notebook 05, re-run on the same database file)
con = sqlite3.connect(os.path.join(DATA, "my_data1.db"))
Q = lambda q: pd.read_sql(q, con)
sql = {
    "sites": ("SELECT DISTINCT Launch_Site FROM SPACEXTABLE;", Q("SELECT DISTINCT Launch_Site FROM SPACEXTABLE")),
    "cca": ("SELECT * FROM SPACEXTABLE\nWHERE Launch_Site LIKE 'CCA%' LIMIT 5;",
            Q("SELECT Date, Booster_Version, Launch_Site, Payload, PAYLOAD_MASS__KG_, Orbit, Customer, Mission_Outcome, Landing_Outcome FROM SPACEXTABLE WHERE Launch_Site LIKE 'CCA%' LIMIT 5")),
    "nasa": ("SELECT SUM(PAYLOAD_MASS__KG_) FROM SPACEXTABLE\nWHERE Customer = 'NASA (CRS)';",
             Q("SELECT SUM(PAYLOAD_MASS__KG_) AS Total FROM SPACEXTABLE WHERE Customer = 'NASA (CRS)'")),
    "v11": ("SELECT AVG(PAYLOAD_MASS__KG_) FROM SPACEXTABLE\nWHERE Booster_Version = 'F9 v1.1';",
            Q("SELECT AVG(PAYLOAD_MASS__KG_) AS Avg FROM SPACEXTABLE WHERE Booster_Version = 'F9 v1.1'")),
    "ground": ("SELECT MIN(Date) FROM SPACEXTABLE\nWHERE Landing_Outcome = 'Success (ground pad)';",
               Q("SELECT MIN(Date) AS First FROM SPACEXTABLE WHERE Landing_Outcome = 'Success (ground pad)'")),
    "drone46": ("SELECT Booster_Version FROM SPACEXTABLE\nWHERE Landing_Outcome = 'Success (drone ship)'\n  AND PAYLOAD_MASS__KG_ > 4000 AND PAYLOAD_MASS__KG_ < 6000;",
                Q("SELECT Booster_Version, PAYLOAD_MASS__KG_ AS Payload_kg FROM SPACEXTABLE WHERE Landing_Outcome = 'Success (drone ship)' AND PAYLOAD_MASS__KG_ > 4000 AND PAYLOAD_MASS__KG_ < 6000")),
    "mission": ("SELECT Mission_Outcome, COUNT(*) FROM SPACEXTABLE\nGROUP BY Mission_Outcome;",
                Q("SELECT Mission_Outcome, COUNT(*) AS Total FROM SPACEXTABLE GROUP BY Mission_Outcome")),
    "mission2": (None, Q("SELECT CASE WHEN Mission_Outcome LIKE 'Success%' THEN 'Success' ELSE 'Failure' END AS Outcome, COUNT(*) AS Total FROM SPACEXTABLE GROUP BY Outcome")),
    "maxpl": ("SELECT Booster_Version FROM SPACEXTABLE\nWHERE PAYLOAD_MASS__KG_ =\n  (SELECT MAX(PAYLOAD_MASS__KG_) FROM SPACEXTABLE);",
              Q("SELECT Booster_Version, PAYLOAD_MASS__KG_ AS Payload_kg FROM SPACEXTABLE WHERE PAYLOAD_MASS__KG_ = (SELECT MAX(PAYLOAD_MASS__KG_) FROM SPACEXTABLE)")),
    "f2015": ("SELECT substr(Date,6,2) AS Month, Landing_Outcome,\n       Booster_Version, Launch_Site FROM SPACEXTABLE\nWHERE Landing_Outcome = 'Failure (drone ship)'\n  AND substr(Date,1,4) = '2015';",
              Q("SELECT substr(Date,6,2) AS Month, Landing_Outcome, Booster_Version, Launch_Site FROM SPACEXTABLE WHERE Landing_Outcome = 'Failure (drone ship)' AND substr(Date,1,4) = '2015'")),
    "rank": ("SELECT Landing_Outcome, COUNT(*) AS Total FROM SPACEXTABLE\nWHERE Date BETWEEN '2010-06-04' AND '2017-03-20'\nGROUP BY Landing_Outcome ORDER BY Total DESC;",
             Q("SELECT Landing_Outcome, COUNT(*) AS Total FROM SPACEXTABLE WHERE Date BETWEEN '2010-06-04' AND '2017-03-20' GROUP BY Landing_Outcome ORDER BY Total DESC")),
}
con.close()
for k in ("cca", "drone46", "maxpl", "f2015"):
    sql[k][1].columns = [c.replace("_", " ") for c in sql[k][1].columns]

# ---------------------------------------------------------------- design helpers --
NAVY, TEAL, ORANGE, RED = RGBColor(0x0B, 0x25, 0x45), RGBColor(0x2A, 0x9D, 0x8F), RGBColor(0xF4, 0xA2, 0x61), RGBColor(0xE0, 0x52, 0x52)
BLUE, GREY, DARK, LIGHT, WHITE = RGBColor(0x2A, 0x6F, 0x97), RGBColor(0x5C, 0x67, 0x7D), RGBColor(0x1F, 0x29, 0x37), RGBColor(0xF1, 0xF5, 0xF9), RGBColor(0xFF, 0xFF, 0xFF)
FONT, MONO = "Segoe UI", "Consolas"
W, H = 13.333, 7.5

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W), Inches(H)
BLANK = prs.slide_layouts[6]
NOTES = []          # (slide title, [(english, vietnamese), ...])


def textbox(slide, x, y, w, h, paras, size=18, color=DARK, anchor=MSO_ANCHOR.TOP, align=PP_ALIGN.LEFT, font=FONT):
    """paras: list of str or dict(text, size, bold, color, bullet, link, font, space)."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    for i, p in enumerate(paras):
        p = {"text": p} if isinstance(p, str) else p
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = p.get("align", align)
        para.space_after = Pt(p.get("space", 6))
        runs = p["text"] if isinstance(p["text"], list) else [(p["text"], p.get("bold", False))]
        if p.get("bullet"):
            runs = [("•  ", False)] + list(runs)
        for txt, bold in runs:
            r = para.add_run()
            r.text = txt
            r.font.size = Pt(p.get("size", size))
            r.font.bold = bold
            r.font.name = p.get("font", font)
            r.font.color.rgb = p.get("color", color)
            if p.get("link"):
                r.hyperlink.address = p["link"]
    return tb


def box(slide, x, y, w, h, fill=LIGHT, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1.5)
    s.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = 0.12
    return s


def image(slide, name, x, y, w, h, align="center"):
    """Place an image inside the box (x, y, w, h) keeping its aspect ratio."""
    path = os.path.join(IMG, name)
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    px = x + (w - pw) / 2 if align == "center" else x
    py = y + (h - ph) / 2
    pic = slide.shapes.add_picture(path, Inches(px), Inches(py), Inches(pw), Inches(ph))
    pic.line.color.rgb = RGBColor(0xD9, 0xDE, 0xE5)
    pic.line.width = Pt(0.75)
    return pic


def table(slide, data, x, y, w, col_w=None, size=12, row_h=0.32, header=NAVY):
    rows, cols = data.shape[0] + 1, data.shape[1]
    t = slide.shapes.add_table(rows, cols, Inches(x), Inches(y), Inches(w), Inches(row_h * rows)).table
    if col_w:
        for i, cw in enumerate(col_w):
            t.columns[i].width = Inches(cw)
    for r in range(rows):
        t.rows[r].height = Inches(row_h)
        for c in range(cols):
            cell = t.cell(r, c)
            val = data.columns[c] if r == 0 else data.iat[r - 1, c]
            cell.text = f"{val:,.1f}" if isinstance(val, float) else f"{val:,}" if isinstance(val, int) and not isinstance(val, bool) else str(val)
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            para = cell.text_frame.paragraphs[0]
            para.font.size = Pt(size)
            para.font.name = FONT
            para.font.bold = r == 0
            para.font.color.rgb = WHITE if r == 0 else DARK
            cell.fill.solid()
            cell.fill.fore_color.rgb = header if r == 0 else (LIGHT if r % 2 else WHITE)
    return t


def slide(title, notes, section=None, github=None):
    """New content slide: title bar, optional GitHub link line, footer."""
    s = prs.slides.add_slide(BLANK)
    box(s, 0, 0, W, 0.12, fill=TEAL, shape=MSO_SHAPE.RECTANGLE)
    if section:
        textbox(s, 0.6, 0.28, 9, 0.35, [{"text": section.upper(), "size": 12, "bold": True, "color": TEAL}])
    textbox(s, 0.6, 0.55, W - 1.2, 0.8, [{"text": title, "size": 30, "bold": True, "color": NAVY}])
    n = len(prs.slides)
    textbox(s, W - 1.3, H - 0.45, 0.8, 0.3, [{"text": str(n), "size": 11, "color": GREY, "align": PP_ALIGN.RIGHT}])
    if github:
        textbox(s, 0.6, H - 0.48, W - 2.2, 0.32,
                [{"text": [("GitHub: ", True), (github, False)], "size": 11, "color": BLUE, "link": github}])
    else:
        textbox(s, 0.6, H - 0.48, 8, 0.3, [{"text": "SpaceX Falcon 9 – Data Science Capstone", "size": 11, "color": GREY}])
    NOTES.append((title, notes))
    s.notes_slide.notes_text_frame.text = "\n".join(f"{en}  —  {vi}" for en, vi in notes)
    return s


def insight(s, text, y=6.25, h=0.72, x=0.6, w=W - 1.2):
    box(s, x, y, w, h, fill=RGBColor(0xE8, 0xF6, 0xF4))
    box(s, x, y, 0.09, h, fill=TEAL, shape=MSO_SHAPE.RECTANGLE)
    textbox(s, x + 0.25, y, w - 0.35, h, [{"text": [("Insight:  ", True), (text, False)], "size": 15}], anchor=MSO_ANCHOR.MIDDLE)


def flow(s, steps, x, y, w, box_h=0.95, gap=0.32, fill=NAVY, size=13):
    """Horizontal flowchart of boxes joined by arrows."""
    n = len(steps)
    bw = (w - gap * (n - 1)) / n
    for i, st in enumerate(steps):
        bx = x + i * (bw + gap)
        b = box(s, bx, y, bw, box_h, fill=fill)
        tf = b.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.06)
        tf.text = st
        for para in tf.paragraphs:
            para.alignment = PP_ALIGN.CENTER
            para.font.size = Pt(size)
            para.font.bold = True
            para.font.name = FONT
            para.font.color.rgb = WHITE
        if i < n - 1:
            a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(bx + bw + 0.04), Inches(y + box_h / 2 - 0.13), Inches(gap - 0.08), Inches(0.26))
            a.fill.solid(); a.fill.fore_color.rgb = ORANGE; a.line.fill.background()


def code_box(s, text, x, y, w, h, size=12):
    box(s, x, y, w, h, fill=RGBColor(0x1E, 0x29, 0x3B))
    textbox(s, x + 0.15, y + 0.08, w - 0.3, h - 0.16, [{"text": line, "size": size, "color": RGBColor(0xE2, 0xE8, 0xF0), "font": MONO, "space": 0} for line in text.split("\n")])


# ================================================================== SLIDES ==
# 1. Title -------------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
box(s, 0, 0, W, H, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
box(s, 0.8, 2.15, 0.12, 2.0, fill=TEAL, shape=MSO_SHAPE.RECTANGLE)
textbox(s, 1.15, 1.2, 11, 0.5, [{"text": "IBM APPLIED DATA SCIENCE CAPSTONE", "size": 16, "bold": True, "color": ORANGE}])
textbox(s, 1.15, 2.0, 11.5, 1.6, [{"text": "Data Science Capstone Project Report", "size": 44, "bold": True, "color": WHITE}])
textbox(s, 1.15, 3.35, 11.5, 0.9, [{"text": "Predicting whether the SpaceX Falcon 9 first stage will land", "size": 24, "color": RGBColor(0xCB, 0xD5, 0xE1)}])
textbox(s, 1.15, 4.75, 11.5, 0.9, [
    {"text": [("Author: ", True), ("khoalee252006", False)], "size": 16, "color": WHITE},
    {"text": [("Date: ", True), ("October 23, 2026", False)], "size": 16, "color": WHITE}])
box(s, 1.15, 5.75, 7.6, 0.6, fill=WHITE)      # white box so the (blue) hyperlink stays readable
textbox(s, 1.3, 5.75, 7.4, 0.6, [{"text": [("GitHub: ", True), (REPO, False)], "size": 16, "link": REPO}], anchor=MSO_ANCHOR.MIDDLE)
NOTES.append(("Title", [
    ("Hello everyone.", "Xin chào mọi người."),
    ("My project is about SpaceX Falcon 9 rockets.", "Dự án của tôi nói về tên lửa SpaceX Falcon 9."),
    ("I want to predict if the first stage will land.", "Tôi muốn dự đoán tầng một có hạ cánh được không."),
    ("All my code is on GitHub.", "Toàn bộ code của tôi có trên GitHub.")]))
s.notes_slide.notes_text_frame.text = "\n".join(f"{a}  —  {b}" for a, b in NOTES[-1][1])

# 2. GitHub links --------------------------------------------------------------
s = slide("Project GitHub Repository", [
    ("This slide shows my GitHub repository.", "Slide này cho thấy kho GitHub của tôi."),
    ("Each step has its own notebook.", "Mỗi bước có một notebook riêng."),
    ("You can click the links to see the code.", "Bạn có thể bấm vào link để xem code.")], github=REPO)
textbox(s, 0.6, 1.45, W - 1.2, 0.5, [{"text": [("Repository:  ", True), (REPO, False)], "size": 20, "color": BLUE, "link": REPO}])
rows = [("1", "Data Collection – SpaceX API", "api"), ("2", "Data Collection – Web Scraping", "scrape"),
        ("3", "Data Wrangling", "wrangle"), ("4", "EDA with Data Visualization", "viz"), ("5", "EDA with SQL", "sql"),
        ("6", "Interactive Map with Folium", "folium"), ("7", "Plotly Dash Dashboard", "dash"), ("8", "Predictive Analysis", "ml")]
for i, (num, name, key) in enumerate(rows):
    y = 2.2 + i * 0.52
    box(s, 0.6, y, 0.45, 0.42, fill=TEAL)
    textbox(s, 0.6, y, 0.45, 0.42, [{"text": num, "size": 15, "bold": True, "color": WHITE, "align": PP_ALIGN.CENTER}], anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, 1.2, y, 3.7, 0.42, [{"text": name, "size": 15, "bold": True}], anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, 4.9, y, 7.9, 0.42, [{"text": NB_URL[key], "size": 13, "color": BLUE, "link": NB_URL[key]}], anchor=MSO_ANCHOR.MIDDLE)

# 3. Outline -------------------------------------------------------------------
s = slide("Outline", [
    ("This is the plan of my talk.", "Đây là kế hoạch bài trình bày của tôi."),
    ("First, the summary and the problem.", "Đầu tiên là tóm tắt và vấn đề."),
    ("Then methods, results, and conclusion.", "Sau đó là phương pháp, kết quả và kết luận.")], github=REPO)
items = ["Executive Summary", "Introduction", "Methodology", "Results: EDA with Visualization", "Results: EDA with SQL",
         "Results: Launch Sites Proximity (Folium)", "Results: Dashboard (Plotly Dash)", "Results: Predictive Analysis", "Conclusion", "Appendix"]
for i, it in enumerate(items):
    col, row = divmod(i, 5)
    x, y = 0.9 + col * 6.1, 1.7 + row * 0.92
    box(s, x, y, 5.6, 0.72, fill=LIGHT)
    textbox(s, x + 0.2, y, 0.6, 0.72, [{"text": f"{i + 1:02d}", "size": 22, "bold": True, "color": TEAL}], anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, x + 1.0, y, 4.5, 0.72, [{"text": it, "size": 18, "bold": True, "color": NAVY}], anchor=MSO_ANCHOR.MIDDLE)

# 4. Executive summary -----------------------------------------------------------
s = slide("Executive Summary", [
    ("I collected real launch data from an API and Wikipedia.", "Tôi thu thập dữ liệu phóng thật từ API và Wikipedia."),
    (f"Overall, {pct(F['rate'])} of first stages landed.", f"Nhìn chung, {pct(F['rate'])} tầng một đã hạ cánh."),
    ("Landing success grew a lot over the years.", "Tỉ lệ hạ cánh thành công tăng rất nhiều qua các năm."),
    (f"My best models reach {pct(best_test)} test accuracy.", f"Các mô hình tốt nhất đạt độ chính xác {pct(best_test)} trên tập kiểm tra.")], github=REPO)
box(s, 0.6, 1.5, 5.7, 4.75, fill=LIGHT)
textbox(s, 0.85, 1.6, 5.3, 4.6, [
    {"text": "Methods", "size": 20, "bold": True, "color": TEAL, "space": 10},
    {"text": "Data collection: SpaceX REST API + web scraping (Wikipedia)", "bullet": True, "size": 15},
    {"text": "Data wrangling: missing values, landing label Class (1 / 0), one-hot encoding", "bullet": True, "size": 15},
    {"text": "EDA: pandas, matplotlib / seaborn charts and SQL (SQLite)", "bullet": True, "size": 15},
    {"text": "Interactive analytics: Folium map and Plotly Dash dashboard", "bullet": True, "size": 15},
    {"text": "Machine learning: Logistic Regression, SVM, Decision Tree, KNN with GridSearchCV (cv = 10)", "bullet": True, "size": 15}])
box(s, 6.6, 1.5, 6.13, 4.75, fill=RGBColor(0xE8, 0xF6, 0xF4))
textbox(s, 6.85, 1.6, 5.75, 4.6, [
    {"text": "Key results", "size": 20, "bold": True, "color": TEAL, "space": 10},
    {"text": f"{F['n']} Falcon 9 launches ({F['years'][0]}–{F['years'][1]}); {F['landed']} landed = {pct(F['rate'])} success", "bullet": True, "size": 15},
    {"text": f"Success grew from 0% (2010–2013) to {pct0(yearly[2019])} in 2019", "bullet": True, "size": 15},
    {"text": f"Best common orbit: VLEO {pct0(orbit.loc['VLEO', 'mean'])}; weakest: GTO {pct0(orbit.loc['GTO', 'mean'])}", "bullet": True, "size": 15},
    {"text": f"When a landing was attempted, {pct(F['attempt_rate'])} succeeded", "bullet": True, "size": 15},
    {"text": f"{', '.join(tied)}: {pct(best_test)} test accuracy (tie); SVM has the best validation accuracy ({pct(best_val['val'])})", "bullet": True, "size": 15}])

# 5. Introduction ------------------------------------------------------------------
s = slide("Introduction", [
    ("SpaceX rockets cost about 62 million dollars.", "Tên lửa SpaceX có giá khoảng 62 triệu đô la."),
    ("Other companies cost 165 million dollars or more.", "Các công ty khác tốn 165 triệu đô la trở lên."),
    ("The big saving comes from reusing the first stage.", "Khoản tiết kiệm lớn đến từ việc tái sử dụng tầng một."),
    ("So we predict if the first stage will land.", "Vì vậy chúng tôi dự đoán tầng một có hạ cánh không.")], github=REPO)
textbox(s, 0.6, 1.45, 6.4, 4.8, [
    {"text": "Background", "size": 20, "bold": True, "color": TEAL, "space": 8},
    {"text": "SpaceX advertises Falcon 9 launches at about $62 million.", "bullet": True, "size": 16},
    {"text": "Other providers charge $165 million or more per launch.", "bullet": True, "size": 16},
    {"text": "Most of the saving comes from landing and reusing the first stage.", "bullet": True, "size": 16},
    {"text": "A new company (\"Space Y\") wants to bid against SpaceX.", "bullet": True, "size": 16, "space": 14},
    {"text": "Problem statement", "size": 20, "bold": True, "color": TEAL, "space": 8},
    {"text": "Can we predict if the Falcon 9 first stage will land successfully?", "bullet": True, "size": 16},
    {"text": "If yes, we can estimate the real cost of a launch.", "bullet": True, "size": 16}])
box(s, 7.4, 1.5, 5.33, 4.7, fill=NAVY)
textbox(s, 7.7, 1.65, 4.8, 4.4, [
    {"text": "Questions we answer", "size": 20, "bold": True, "color": ORANGE, "space": 12},
    {"text": "How do payload mass, orbit, launch site and flight number affect landing?", "bullet": True, "size": 16, "color": WHITE, "space": 10},
    {"text": "Did landing success improve over time?", "bullet": True, "size": 16, "color": WHITE, "space": 10},
    {"text": "Where are the launch sites, and why there?", "bullet": True, "size": 16, "color": WHITE, "space": 10},
    {"text": "Which machine-learning model predicts landing best?", "bullet": True, "size": 16, "color": WHITE}])

# 6. Data collection – API ---------------------------------------------------------
s = slide("Data Collection – SpaceX API", [
    ("I call the SpaceX API to get past launches.", "Tôi gọi SpaceX API để lấy các lần phóng trước đây."),
    ("Then I look up rocket, pad, payload and core details.", "Sau đó tôi tra thông tin tên lửa, bệ phóng, tải trọng và lõi."),
    ("I keep only Falcon 9 and save a clean table.", "Tôi chỉ giữ Falcon 9 và lưu một bảng sạch.")],
    section="Methodology", github=NB_URL["api"])
flow(s, ["GET /v4/launches/past", "json_normalize → DataFrame", "Look up rockets, launchpads, payloads, cores",
         "Keep Falcon 9 (1 core, 1 payload, ≤ 13 Nov 2020)", f"Save CSV\n({len(p1)} rows × {p1.shape[1]} columns)"], 0.6, 1.6, W - 1.2, box_h=1.15)
textbox(s, 0.6, 3.1, 6.2, 3.2, [
    {"text": "Key phrases", "size": 18, "bold": True, "color": TEAL},
    {"text": "requests.get() → JSON response", "bullet": True, "size": 15},
    {"text": "pd.json_normalize() to flatten the JSON", "bullet": True, "size": 15},
    {"text": "Helper look-ups: BoosterVersion, LaunchSite, PayloadMass, Orbit, Outcome, Block, Serial…", "bullet": True, "size": 15},
    {"text": f"Missing PayloadMass ({F['payload_missing']}) → filled with mean ({F['payload_mean']:,.2f} kg)", "bullet": True, "size": 15}])
box(s, 7.1, 3.15, 5.63, 2.95, fill=RGBColor(0xFD, 0xF1, 0xE7))
textbox(s, 7.3, 3.2, 5.3, 2.85, [
    {"text": "Note on data source", "size": 16, "bold": True, "color": RGBColor(0xB4, 0x5F, 0x06)},
    {"text": "The live API returned HTTP 522/525 errors (server down) in Oct 2026.", "bullet": True, "size": 13},
    {"text": "The code tries the live API first, then falls back to saved copies of the same API responses: IBM's static launch JSON + archived responses (web.archive.org).", "bullet": True, "size": 13},
    {"text": f"Check: {F['cols_identical']} of {F['cols_total']} columns are identical to IBM's reference dataset_part_1.csv.", "bullet": True, "size": 13}])

# 7. Data collection – web scraping -----------------------------------------------------
s = slide("Data Collection – Web Scraping", [
    ("I download a Wikipedia page with launch tables.", "Tôi tải một trang Wikipedia có các bảng phóng."),
    ("BeautifulSoup reads the HTML tables.", "BeautifulSoup đọc các bảng HTML."),
    (f"I get {len(scraped)} launch rows and save them to CSV.", f"Tôi lấy được {len(scraped)} dòng và lưu vào CSV.")],
    section="Methodology", github=NB_URL["scrape"])
flow(s, ["requests.get() Wikipedia page (oldid = 1027686922)", "BeautifulSoup(html)", "find_all tables \"wikitable plainrowheaders collapsible\"",
         "Read column names + each launch row", f"DataFrame → save CSV\n({len(scraped)} rows)"], 0.6, 1.6, W - 1.2, box_h=1.15)
textbox(s, 0.6, 3.1, W - 1.2, 3.2, [
    {"text": "Key phrases", "size": 18, "bold": True, "color": TEAL},
    {"text": "Page: \"List of Falcon 9 and Falcon Heavy launches\" – fixed old revision used by the IBM lab (June 2021), so results repeat", "bullet": True, "size": 15},
    {"text": "9 launch tables found; flight number is in the <th> cell, other values in <td> cells", "bullet": True, "size": 15},
    {"text": "Columns: Flight No., Date, Time, Version Booster, Launch site, Payload, Payload mass, Orbit, Customer, Launch outcome, Booster landing", "bullet": True, "size": 15},
    {"text": "Cleaning: remove footnote marks like [12], parse \"4,700 kg\" → 4700, parse dates", "bullet": True, "size": 15},
    {"text": f"Result: {len(scraped)} launches from {pd.to_datetime(scraped['Date']).min():%d %b %Y} to {pd.to_datetime(scraped['Date']).max():%d %b %Y}", "bullet": True, "size": 15}])

# 8. Data wrangling ---------------------------------------------------------------------
s = slide("Data Wrangling", [
    ("I check missing values first.", "Đầu tiên tôi kiểm tra giá trị bị thiếu."),
    ("Then I turn the landing outcome into a label called Class.", "Sau đó tôi biến kết quả hạ cánh thành nhãn tên là Class."),
    ("Class is 1 if the booster landed, and 0 if not.", "Class bằng 1 nếu tầng đẩy hạ cánh, bằng 0 nếu không."),
    (f"The overall success rate is {pct(F['rate'])}.", f"Tỉ lệ thành công tổng thể là {pct(F['rate'])}.")],
    section="Methodology", github=NB_URL["wrangle"])
flow(s, ["Load dataset_part_1.csv", "Missing values", "Count launches per site / orbit / outcome", "Outcome → Class (1 / 0)", "One-hot encode features"], 0.6, 1.5, W - 1.2, box_h=0.85, size=13)
textbox(s, 0.6, 2.6, 6.3, 3.6, [
    {"text": f"PayloadMass: {F['payload_missing']} missing → replaced by mean", "bullet": True, "size": 15},
    {"text": f"LandingPad: {F['landingpad_missing']} missing ({F['landingpad_missing'] / F['n']:.1%}) → kept, means \"no landing pad used\"", "bullet": True, "size": 15},
    {"text": "Good outcomes (Class = 1): True ASDS (drone ship), True RTLS (ground pad), True Ocean", "bullet": True, "size": 15},
    {"text": "Bad outcomes (Class = 0): False ASDS / RTLS / Ocean, None ASDS, None None", "bullet": True, "size": 15},
    {"text": f"Success rate = mean(Class) = {pct(F['rate'])}", "bullet": True, "size": 15, "bold": True},
    {"text": f"Output: dataset_part_2.csv (+ Class) and dataset_part_3.csv ({p3.shape[1]} numeric features)", "bullet": True, "size": 15}])
oc = outcomes.reset_index()
oc.columns = ["Outcome", "Launches"]
oc["Class"] = [1 if o.startswith("True") else 0 for o in oc["Outcome"]]
table(s, oc, 7.4, 2.65, 5.3, col_w=[2.5, 1.5, 1.3], size=13, row_h=0.36)

# 9. EDA with visualization (method) ----------------------------------------------------
s = slide("EDA with Data Visualization", [
    ("I use charts to find patterns.", "Tôi dùng biểu đồ để tìm các quy luật."),
    ("Scatter plots show how two things relate.", "Biểu đồ phân tán cho thấy hai yếu tố liên quan thế nào."),
    ("A bar chart compares orbits, and a line chart shows the trend by year.", "Biểu đồ cột so sánh các quỹ đạo, biểu đồ đường cho thấy xu hướng theo năm.")],
    section="Methodology", github=NB_URL["viz"])
charts = [("Scatter", "Flight Number vs. Payload Mass", "Does experience or payload change landing?"),
          ("Scatter", "Flight Number vs. Launch Site", "Do sites improve over time?"),
          ("Scatter", "Payload Mass vs. Launch Site", "Which site handles heavy payloads?"),
          ("Bar", "Success Rate by Orbit", "Which orbit is easiest to land from?"),
          ("Scatter", "Flight Number vs. Orbit", "Does each orbit improve with flights?"),
          ("Scatter", "Payload Mass vs. Orbit", "Is heavy payload a problem in some orbits?"),
          ("Line", "Yearly Success Trend", "Is SpaceX getting better each year?")]
ct = pd.DataFrame(charts, columns=["Chart type", "Chart", "Why we use it"])
table(s, ct, 0.6, 1.5, W - 1.2, col_w=[1.8, 4.4, 5.93], size=15, row_h=0.5)
textbox(s, 0.6, 5.65, W - 1.2, 0.6, [{"text": "Points are colored by Class: green = landed, red = not landed. Tools: pandas, matplotlib, seaborn.", "size": 15, "color": GREY}])

# 10. EDA with SQL (method) --------------------------------------------------------------
s = slide("EDA with SQL", [
    ("I load the launch table into SQLite.", "Tôi nạp bảng phóng vào SQLite."),
    ("Then I answer ten questions with SQL.", "Sau đó tôi trả lời mười câu hỏi bằng SQL."),
    ("I use DISTINCT, LIKE, SUM, AVG, MIN, GROUP BY and subqueries.", "Tôi dùng DISTINCT, LIKE, SUM, AVG, MIN, GROUP BY và truy vấn con.")],
    section="Methodology", github=NB_URL["sql"])
qs = [("1", "Unique launch sites", "SELECT DISTINCT"), ("2", "5 records with site starting 'CCA'", "LIKE 'CCA%' LIMIT 5"),
      ("3", "Total payload for NASA (CRS)", "SUM()"), ("4", "Average payload of F9 v1.1", "AVG()"),
      ("5", "First successful ground-pad landing", "MIN(Date)"), ("6", "Drone-ship success, payload 4000–6000 kg", "AND, > <"),
      ("7", "Count of mission successes / failures", "COUNT(*) GROUP BY"), ("8", "Boosters with maximum payload", "subquery MAX()"),
      ("9", "2015 drone-ship failures by month", "substr(Date)"), ("10", "Rank landing outcomes 2010-06-04 → 2017-03-20", "BETWEEN, ORDER BY DESC")]
table(s, pd.DataFrame(qs, columns=["#", "Question", "Key SQL"]), 0.6, 1.45, W - 1.2, col_w=[0.6, 6.9, 4.63], size=14, row_h=0.4)
textbox(s, 0.6, 5.95, W - 1.2, 0.4, [{"text": f"Data: IBM course table Spacex.csv ({len(pd.read_csv(os.path.join(DATA, 'Spacex.csv')))} Falcon 9 launches) loaded into SQLite with pandas.to_sql().", "size": 14, "color": GREY}])

# 11. Interactive visual analytics (method) -----------------------------------------------
s = slide("Interactive Visual Analytics – Folium & Plotly Dash", [
    ("Folium puts every launch on a map.", "Folium đặt mỗi lần phóng lên bản đồ."),
    ("Green markers mean landed, red markers mean not landed.", "Điểm xanh là hạ cánh, điểm đỏ là không hạ cánh."),
    ("The Dash app lets users filter by site and payload.", "Ứng dụng Dash cho phép lọc theo bãi phóng và tải trọng.")],
    section="Methodology")
for i, (head, lines, url) in enumerate([
        ("Folium map", ["folium.Circle + Marker: each launch site", "MarkerCluster: green = landed, red = not landed",
                        "MousePosition: read coordinates on the map", "PolyLine + distance label: site → coast, railway, highway, city",
                        "Nearest features found with OpenStreetMap (Overpass API) + haversine distance"], NB_URL["folium"]),
        ("Plotly Dash dashboard", ["Dropdown: All sites or one launch site", "Pie chart: successful launches by site / success vs. failure",
                                   "RangeSlider: choose a payload range (kg)", "Scatter: payload vs. launch outcome, colored by booster version",
                                   "Callbacks update the charts when the user changes inputs"], NB_URL["dash"])]):
    x = 0.6 + i * 6.2
    box(s, x, 1.5, 5.93, 4.55, fill=LIGHT)
    textbox(s, x + 0.25, 1.6, 5.5, 4.4, [{"text": head, "size": 20, "bold": True, "color": TEAL, "space": 10}] +
            [{"text": l, "bullet": True, "size": 15} for l in lines])
    textbox(s, x, 6.2, 5.93, 0.55, [{"text": [("GitHub: ", True), (url, False)], "size": 11, "color": BLUE, "link": url}])

# 12. Predictive analysis (method) ---------------------------------------------------------
s = slide("Predictive Analysis – Methodology", [
    ("I split the data into training and test sets.", "Tôi chia dữ liệu thành tập huấn luyện và tập kiểm tra."),
    ("I scale the features and tune four models.", "Tôi chuẩn hoá đặc trưng và tinh chỉnh bốn mô hình."),
    ("GridSearchCV finds the best settings with ten folds.", "GridSearchCV tìm thiết lập tốt nhất với mười phần."),
    ("Then I compare accuracy on the test set.", "Sau đó tôi so sánh độ chính xác trên tập kiểm tra.")],
    section="Methodology", github=NB_URL["ml"])
flow(s, [f"X = {p3.shape[1]} features\nY = Class", f"train_test_split\n80 / 20, random_state = 2\n({F['train_n']} / {F['test_n']})",
         "StandardScaler\n(fit on train)", "GridSearchCV\ncv = 10\n4 models", "Best params →\ntest accuracy +\nconfusion matrix"], 0.6, 1.55, W - 1.2, box_h=1.4, size=14)
grid = pd.DataFrame([("Logistic Regression", "C = 0.01, 0.1, 1"), ("SVM", "kernel = linear / rbf / poly / sigmoid; C, gamma = logspace(-3, 3, 5)"),
                     ("Decision Tree", "criterion, splitter, max_depth 2–18, max_features, min_samples_leaf / split"),
                     ("KNN", "n_neighbors 1–10, algorithm, p = 1 / 2")], columns=["Model", "Parameters searched"])
table(s, grid, 0.6, 3.3, W - 1.2, col_w=[2.8, 9.33], size=14, row_h=0.45)
textbox(s, 0.6, 5.65, W - 1.2, 0.6, [{"text": f"Extra check: the test set has only {F['test_n']} launches, so we also run 10-fold stratified cross-validation on all {F['n']} launches.", "size": 15, "color": GREY}])

# 13–19. EDA visualization results ----------------------------------------------------------
heavy = df[df["PayloadMass"] > 10000]
ccafs = df[df["LaunchSite"] == "CCAFS SLC 40"]
gto = df[df["Orbit"] == "GTO"]
eda = [
    ("Flight Number vs. Payload Mass", "eda_01_flight_vs_payload.png",
     f"Later flights land more often ({pct0(first30)} for flights 1–30 vs. {pct0(last30)} for flights 61–90). Heavy payloads (> 10,000 kg) still landed {int(heavy['Class'].sum())} of {len(heavy)} times.",
     [("Each dot is one launch.", "Mỗi chấm là một lần phóng."), ("Green dots appear more on the right side.", "Chấm xanh xuất hiện nhiều hơn ở bên phải."),
      ("So SpaceX gets better with more flights.", "Vậy SpaceX tiến bộ hơn khi bay nhiều hơn.")]),
    ("Flight Number vs. Launch Site", "eda_02_flight_vs_site.png",
     f"CCAFS SLC 40 has the most launches ({site.loc['CCAFS SLC 40', 'count']}) and the lowest rate ({pct0(site.loc['CCAFS SLC 40', 'mean'])}): its first 20 launches had {pct0(ccafs.head(20)['Class'].mean())} success, later ones {pct0(ccafs.iloc[20:]['Class'].mean())}.",
     [("CCAFS SLC 40 is used the most.", "CCAFS SLC 40 được dùng nhiều nhất."), ("Most early failures happened there.", "Phần lớn thất bại ban đầu xảy ra ở đó."),
      ("Later launches there are much better.", "Các lần phóng sau ở đó tốt hơn nhiều.")]),
    ("Payload Mass vs. Launch Site", "eda_03_payload_vs_site.png",
     f"VAFB SLC 4E never launched more than {df[df.LaunchSite == 'VAFB SLC 4E']['PayloadMass'].max():,.0f} kg. All payloads above 10,000 kg flew from Florida, with high success.",
     [("Heavy payloads only fly from Florida.", "Tải nặng chỉ phóng từ Florida."), ("Vandenberg launches lighter payloads.", "Vandenberg phóng tải nhẹ hơn."),
      ("Heavy launches still land most of the time.", "Các lần phóng nặng vẫn hạ cánh phần lớn.")]),
    ("Success Rate by Orbit Type", "eda_04_success_by_orbit.png",
     f"SSO, ES-L1, GEO and HEO show 100% but have very few launches. Among common orbits, VLEO is best ({pct0(orbit.loc['VLEO', 'mean'])}, n={orbit.loc['VLEO', 'count']}) and GTO is weakest ({pct0(orbit.loc['GTO', 'mean'])}, n={orbit.loc['GTO', 'count']}).",
     [("Each bar is one orbit type.", "Mỗi cột là một loại quỹ đạo."), ("Some orbits have only one launch, so be careful.", "Một số quỹ đạo chỉ có một lần phóng, nên cần cẩn thận."),
      ("VLEO is high and GTO is low.", "VLEO cao còn GTO thấp.")]),
    ("Flight Number vs. Orbit", "eda_05_flight_vs_orbit.png",
     f"LEO failed only in the first two flights, then always landed. GTO shows no clear improvement ({pct0(gto['Class'].mean())}). VLEO flights all came late and landed {pct0(orbit.loc['VLEO', 'mean'])}.",
     [("In LEO, success comes after a few flights.", "Ở LEO, thành công đến sau vài lần bay."), ("In GTO, there is no clear pattern.", "Ở GTO, không có quy luật rõ ràng."),
      ("VLEO launches started late and went well.", "Các lần phóng VLEO bắt đầu muộn và diễn ra tốt.")]),
    ("Payload Mass vs. Orbit", "eda_06_payload_vs_orbit.png",
     f"Heavy VLEO payloads (13,200–15,600 kg) land well. In GTO, heavier payloads land less often ({pct0(gto[gto.PayloadMass <= 5000]['Class'].mean())} for ≤ 5,000 kg vs. {pct0(gto[gto.PayloadMass > 5000]['Class'].mean())} for > 5,000 kg).",
     [("Heavy payloads to VLEO are fine.", "Tải nặng lên VLEO thì ổn."), ("Heavy payloads to GTO are harder.", "Tải nặng lên GTO thì khó hơn."),
      ("GTO needs more fuel, so less is left for landing.", "GTO cần nhiều nhiên liệu, nên còn ít để hạ cánh.")]),
    ("Launch Success Yearly Trend", "eda_07_yearly_trend.png",
     f"Success rose from 0% (2010–2013) to {pct0(yearly[2019])} in 2019 ({pct0(yearly[2020])} in 2020), with one dip in 2018 ({pct0(yearly[2018])}).",
     [("This line shows the success rate each year.", "Đường này cho thấy tỉ lệ thành công mỗi năm."), ("It goes up strongly after 2013.", "Nó tăng mạnh sau năm 2013."),
      ("SpaceX learned quickly.", "SpaceX học hỏi rất nhanh.")]),
]
for title, img, ins, notes in eda:
    s = slide(title, notes, section="Insights drawn from EDA", github=NB_URL["viz"])
    image(s, img, 0.6, 1.4, W - 1.2, 4.75)
    insight(s, ins, y=6.2, h=0.72)

# 20–24. EDA with SQL results ------------------------------------------------------------------
sec = "EDA with SQL – Results"
s = slide("SQL Results: Launch Sites", [
    ("There are four launch sites in the table.", "Có bốn bãi phóng trong bảng."),
    ("Three are in Florida and one is in California.", "Ba bãi ở Florida và một bãi ở California."),
    ("The first five CCA records are early flights.", "Năm bản ghi CCA đầu tiên là các chuyến bay sớm.")], section=sec, github=NB_URL["sql"])
code_box(s, sql["sites"][0], 0.6, 1.45, 4.3, 0.55, size=13)
table(s, sql["sites"][1], 0.6, 2.15, 4.3, size=14, row_h=0.4)
code_box(s, sql["cca"][0], 5.2, 1.45, 7.53, 0.8, size=13)
cca = sql["cca"][1].copy()
cca["Payload"] = cca["Payload"].str.slice(0, 26)
table(s, cca, 5.2, 2.4, 7.53, size=9, row_h=0.5)
insight(s, "4 unique sites; the first 5 'CCA' launches (2010–2013) were early Dragon / CRS missions with no landing attempt or parachute failures.", y=5.6, h=0.8)

s = slide("SQL Results: Payloads", [
    ("NASA CRS missions carried about forty-five thousand kilograms in total.", "Các sứ mệnh NASA CRS mang tổng cộng khoảng bốn mươi lăm nghìn kg."),
    ("F9 v1.1 carried about two thousand nine hundred kilograms on average.", "F9 v1.1 mang trung bình khoảng hai nghìn chín trăm kg."),
    ("Only Block 5 boosters carried the maximum payload.", "Chỉ các tầng đẩy Block 5 mang tải tối đa.")], section=sec, github=NB_URL["sql"])
for i, (k, label, val) in enumerate([("nasa", "Total payload – NASA (CRS)", f"{int(sql['nasa'][1].iat[0, 0]):,} kg"),
                                     ("v11", "Average payload – F9 v1.1", f"{sql['v11'][1].iat[0, 0]:,.1f} kg")]):
    y = 1.45 + i * 2.35
    code_box(s, sql[k][0], 0.6, y, 6.0, 0.8, size=12)
    box(s, 0.6, y + 0.95, 6.0, 1.1, fill=LIGHT)
    textbox(s, 0.8, y + 0.95, 5.6, 1.1, [{"text": label, "size": 14, "color": GREY, "space": 0}, {"text": val, "size": 28, "bold": True, "color": NAVY}], anchor=MSO_ANCHOR.MIDDLE)
code_box(s, sql["maxpl"][0], 6.9, 1.45, 5.83, 1.0, size=12)
mp = sql["maxpl"][1]
textbox(s, 6.9, 2.55, 5.83, 0.4, [{"text": f"{len(mp)} boosters carried the maximum payload of {int(mp.iat[0, 1]):,} kg:", "size": 14, "bold": True}])
mp2 = pd.DataFrame({"Booster": mp.iloc[:6, 0].str.strip().values, " Booster": mp.iloc[6:12, 0].str.strip().values})
table(s, mp2, 6.9, 3.0, 5.83, size=13, row_h=0.36)

s = slide("SQL Results: Success Rates", [
    ("Almost every mission reached orbit.", "Hầu như mọi sứ mệnh đều lên quỹ đạo."),
    ("Only one mission failed in flight.", "Chỉ có một sứ mệnh thất bại khi bay."),
    ("Four boosters landed on a drone ship with medium payloads.", "Bốn tầng đẩy hạ cánh trên tàu không người lái với tải trung bình.")], section=sec, github=NB_URL["sql"])
code_box(s, sql["mission"][0], 0.6, 1.45, 6.0, 0.8, size=12)
table(s, sql["mission"][1], 0.6, 2.4, 6.0, col_w=[4.5, 1.5], size=13, row_h=0.38)
m2 = sql["mission2"][1].set_index("Outcome")["Total"]
box(s, 0.6, 4.5, 6.0, 1.0, fill=LIGHT)
textbox(s, 0.8, 4.5, 5.6, 1.0, [{"text": [("Grouped: ", True), (f"Success = {m2['Success']},  Failure = {m2['Failure']}  →  {m2['Success'] / m2.sum():.1%} mission success", False)], "size": 15}], anchor=MSO_ANCHOR.MIDDLE)
code_box(s, sql["drone46"][0], 6.9, 1.45, 5.83, 1.0, size=12)
table(s, sql["drone46"][1], 6.9, 2.6, 5.83, size=13, row_h=0.38)
insight(s, f"Mission success is very high ({m2['Success']} of {m2.sum()}), but booster landing is the hard part. Only F9 FT boosters landed on a drone ship with 4,000–6,000 kg payloads.", y=5.75, h=0.75)

s = slide("SQL Results: Ranking Landing Outcomes", [
    ("This query ranks landing outcomes in the early years.", "Truy vấn này xếp hạng kết quả hạ cánh trong những năm đầu."),
    ("No attempt is the most common result.", "Không thử hạ cánh là kết quả phổ biến nhất."),
    ("Drone ship success and failure are equal.", "Thành công và thất bại trên tàu không người lái bằng nhau.")], section=sec, github=NB_URL["sql"])
code_box(s, sql["rank"][0], 0.6, 1.45, 6.3, 1.05, size=12)
rk = sql["rank"][1].copy()
rk.insert(0, "Rank", range(1, len(rk) + 1))
table(s, rk, 7.2, 1.45, 5.53, col_w=[0.9, 3.4, 1.23], size=14, row_h=0.42)
r = rk.set_index("Landing_Outcome")["Total"]
insight(s, f"In the early years, 'No attempt' was most common ({r['No attempt']}). Drone-ship landings were 50/50 ({r['Success (drone ship)']} success vs. {r['Failure (drone ship)']} failure), and ground-pad landings already worked ({r['Success (ground pad)']} of {r['Success (ground pad)']}).",
        x=0.6, y=2.75, w=6.3, h=1.6)

s = slide("SQL Results: Time Analysis", [
    ("The first ground pad landing was in December 2015.", "Lần hạ cánh trên bệ mặt đất đầu tiên là tháng 12 năm 2015."),
    ("In 2015, two drone ship landings failed.", "Năm 2015, có hai lần hạ cánh trên tàu thất bại."),
    ("They were in January and April.", "Chúng xảy ra vào tháng 1 và tháng 4.")], section=sec, github=NB_URL["sql"])
code_box(s, sql["ground"][0], 0.6, 1.45, 6.0, 0.8, size=12)
box(s, 0.6, 2.4, 6.0, 1.3, fill=LIGHT)
textbox(s, 0.8, 2.4, 5.6, 1.3, [{"text": "First successful ground-pad landing", "size": 14, "color": GREY, "space": 0},
                               {"text": pd.to_datetime(sql["ground"][1].iat[0, 0]).strftime("%d %B %Y"), "size": 30, "bold": True, "color": NAVY}], anchor=MSO_ANCHOR.MIDDLE)
code_box(s, sql["f2015"][0], 6.9, 1.45, 5.83, 1.25, size=12)
fm = sql["f2015"][1].copy()
fm.insert(1, "Month name", [pd.Timestamp(2015, int(m), 1).strftime("%B") for m in fm["Month"]])
table(s, fm, 6.9, 2.85, 5.83, size=12, row_h=0.42)
insight(s, "Both 2015 drone-ship failures were F9 v1.1 boosters from CCAFS LC-40 (January and April). Eight months later (Dec 2015) the first ground-pad landing succeeded.", y=4.6, h=0.95)

# 25–27. Folium results ---------------------------------------------------------------------------
sec = "Launch Sites Proximity Analysis"
s = slide("Folium: All Launch Sites on the Map", [
    ("Here are all four launch sites.", "Đây là bốn bãi phóng."),
    ("They are close to the coast.", "Chúng nằm gần bờ biển."),
    ("They are also in the south, near the equator.", "Chúng cũng ở phía nam, gần xích đạo.")], section=sec, github=NB_URL["folium"])
image(s, "folium_1_launch_sites.png", 0.6, 1.4, 6.0, 3.4)
image(s, "folium_1b_launch_sites_florida.png", 6.73, 1.4, 6.0, 3.4)
textbox(s, 0.6, 4.85, 6.0, 0.35, [{"text": "All sites (USA)", "size": 12, "color": GREY, "align": PP_ALIGN.CENTER}])
textbox(s, 6.73, 4.85, 6.0, 0.35, [{"text": "Cape Canaveral close-up (LC-40 and SLC-40 labels overlap: same pad area)", "size": 12, "color": GREY, "align": PP_ALIGN.CENTER}])
insight(s, "3 sites in Florida (CCAFS LC-40, CCAFS SLC-40, KSC LC-39A) and 1 in California (VAFB SLC-4E). All sit on the coast in the south of the USA – closer to the equator gives extra speed from Earth's rotation, and launches fly over the ocean.", y=5.35, h=0.95)

s = slide("Folium: Launch Outcomes per Site", [
    ("Each marker is one launch.", "Mỗi điểm đánh dấu là một lần phóng."),
    ("Green means landed and red means not landed.", "Xanh nghĩa là hạ cánh, đỏ nghĩa là không hạ cánh."),
    ("KSC LC-39A has the most green markers.", "KSC LC-39A có nhiều điểm xanh nhất.")], section=sec, github=NB_URL["folium"])
image(s, "folium_2_launch_outcomes.png", 0.6, 1.4, 5.9, 3.5)
image(s, "folium_2b_launch_outcomes_ksc.png", 6.83, 1.4, 5.9, 3.5)
textbox(s, 0.6, 4.95, 5.9, 0.35, [{"text": "MarkerCluster – number of launches per site", "size": 12, "color": GREY, "align": PP_ALIGN.CENTER}])
textbox(s, 6.83, 4.95, 5.9, 0.35, [{"text": "KSC LC-39A cluster opened – green = landed, red = not landed", "size": 12, "color": GREY, "align": PP_ALIGN.CENTER}])
geo = pd.read_csv(os.path.join(DATA, "spacex_launch_geo.csv")).groupby("Launch Site")["class"].agg(["count", "sum", "mean"]).sort_values("mean", ascending=False)
insight(s, "  |  ".join(f"{k}: {int(v['sum'])}/{int(v['count'])} landed ({pct0(v['mean'])})" for k, v in geo.iterrows()), y=5.45, h=0.7)

s = slide("Folium: Proximity Analysis (CCAFS SLC-40)", [
    ("I measure distances from the launch site.", "Tôi đo khoảng cách từ bãi phóng."),
    ("The coast and railway are very close.", "Bờ biển và đường sắt rất gần."),
    ("The city is far away for safety.", "Thành phố ở xa để đảm bảo an toàn.")], section=sec, github=NB_URL["folium"])
image(s, "folium_3_proximity.png", 0.6, 1.4, 6.0, 3.4)
image(s, "folium_3b_proximity_closeup.png", 6.73, 1.4, 6.0, 3.4)
textbox(s, 0.6, 4.82, 6.0, 0.3, [{"text": "Overview: highway and city", "size": 12, "color": GREY, "align": PP_ALIGN.CENTER}])
textbox(s, 6.73, 4.82, 6.0, 0.3, [{"text": "Close-up: coastline and railway", "size": 12, "color": GREY, "align": PP_ALIGN.CENTER}])
ps = "CCAFS SLC-40"
pt = pd.DataFrame([(k.capitalize(), prox[(ps, k)][0] if prox[(ps, k)][0] != k else "–", f"{prox[(ps, k)][1]:.2f} km") for k in ("coastline", "railway", "highway", "city")],
                  columns=["Nearest", "Name (OpenStreetMap)", "Distance"])
table(s, pt, 0.6, 5.2, 5.4, col_w=[1.3, 2.6, 1.5], size=11, row_h=0.3)
textbox(s, 6.3, 5.15, 6.43, 1.7, [
    {"text": "Findings", "size": 17, "bold": True, "color": TEAL},
    {"text": f"Very close to the coast ({prox[(ps, 'coastline')][1]:.2f} km): a failed rocket falls into the ocean", "bullet": True, "size": 14},
    {"text": f"Very close to a railway ({prox[(ps, 'railway')][1]:.2f} km): heavy parts arrive by train", "bullet": True, "size": 14},
    {"text": f"Highway {prox[(ps, 'highway')][1]:.1f} km away: road access for people and supplies", "bullet": True, "size": 14},
    {"text": f"Nearest city ({prox[(ps, 'city')][0]}) {prox[(ps, 'city')][1]:.1f} km away: far from people for safety", "bullet": True, "size": 14}])

# 28–30. Dash results ---------------------------------------------------------------------------
sec = "Dashboard with Plotly Dash"
best_site = dsite.index[0]
s = slide("Dash: Successful Launches by Site (All Sites)", [
    ("This pie shows where the successful launches come from.", "Biểu đồ tròn này cho thấy các lần thành công đến từ đâu."),
    (f"{best_site} has the biggest share.", f"{best_site} có phần lớn nhất."),
    ("CCAFS SLC-40 has the smallest share.", "CCAFS SLC-40 có phần nhỏ nhất.")], section=sec, github=NB_URL["dash"])
image(s, "dash_1_pie_all_sites.png", 0.6, 1.4, 8.3, 4.6)
ds = dsite.reset_index()[["Launch Site", "sum", "share"]].sort_values("share", ascending=False)
ds.columns = ["Launch Site", "Successes", "Share"]
ds["Share"] = ds["Share"].map(pct)
ds["Successes"] = ds["Successes"].astype(int)
table(s, ds, 9.1, 1.6, 3.63, col_w=[1.6, 1.1, 0.93], size=12, row_h=0.42)
insight(s, f"{best_site} produced the largest share of all successful launches ({pct(dsite.loc[best_site, 'share'])}); CCAFS SLC-40 the smallest ({pct(dsite.loc['CCAFS SLC-40', 'share'])}).", y=6.1, h=0.75)

s = slide(f"Dash: Highest Success Rate Site – {best_site}", [
    (f"This pie is only for {best_site}.", f"Biểu đồ tròn này chỉ dành cho {best_site}."),
    (f"{pct(dsite.loc[best_site, 'mean'])} of its launches were successful.", f"{pct(dsite.loc[best_site, 'mean'])} số lần phóng ở đây thành công."),
    ("It is the best site in this data.", "Đây là bãi phóng tốt nhất trong dữ liệu này.")], section=sec, github=NB_URL["dash"])
image(s, "dash_2_pie_best_site.png", 0.6, 1.4, 8.3, 4.6)
dr = dsite.reset_index()[["Launch Site", "count", "mean"]]
dr.columns = ["Launch Site", "Launches", "Success rate"]
dr["Success rate"] = dr["Success rate"].map(pct)
table(s, dr, 9.1, 1.6, 3.63, col_w=[1.6, 1.0, 1.03], size=12, row_h=0.42)
insight(s, f"{best_site} has the highest success rate: {int(dsite.loc[best_site, 'sum'])} of {int(dsite.loc[best_site, 'count'])} launches ({pct(dsite.loc[best_site, 'mean'])} success, {pct(1 - dsite.loc[best_site, 'mean'])} failure).", y=6.1, h=0.75)

s = slide("Dash: Payload vs. Launch Outcome (All Sites)", [
    ("These charts show payload and outcome together.", "Các biểu đồ này cho thấy tải trọng và kết quả cùng nhau."),
    ("Light and medium payloads succeed more often.", "Tải nhẹ và trung bình thành công thường xuyên hơn."),
    ("The FT booster version has the best success rate.", "Phiên bản tầng đẩy FT có tỉ lệ thành công tốt nhất.")], section=sec, github=NB_URL["dash"])
image(s, "dash_4_scatter_low_payload.png", 0.6, 1.35, 7.6, 2.4)
image(s, "dash_5_scatter_high_payload.png", 0.6, 3.82, 7.6, 2.4)
dr2 = drange.reset_index()
dr2.columns = ["Payload (kg)", "Launches", "Success"]
dr2["Payload (kg)"] = [f"{int(i.left):,}–{int(i.right):,}" for i in dr2["Payload (kg)"]]
dr2["Success"] = dr2["Success"].map(pct0)
table(s, dr2, 8.5, 1.4, 4.23, col_w=[1.8, 1.25, 1.18], size=12, row_h=0.34)
db = dboost.reset_index()
db.columns = ["Booster", "Launches", "Success"]
db["Success"] = db["Success"].map(pct0)
table(s, db, 8.5, 3.65, 4.23, col_w=[1.8, 1.25, 1.18], size=12, row_h=0.34)
insight(s, f"Best payload range: {int(best_range.left):,}–{int(best_range.right):,} kg ({pct0(drange.loc[best_range, 'mean'])}, n = {drange.loc[best_range, 'count']}); "
           f"worst: 6,000–8,000 kg (0 of {drange.iloc[3]['count']:.0f}). Best booster: FT ({pct0(dboost.loc['FT', 'mean'])}, n = {dboost.loc['FT', 'count']}); "
           f"B5 is 1 of 1 (too few); v1.1 lowest ({pct0(dboost.loc['v1.1', 'mean'])}).", y=6.3, h=0.72)

# 31–34. Predictive analysis results -------------------------------------------------------------
sec = "Predictive Analysis (Classification)"
s = slide("Classification Accuracy", [
    ("I tested four models.", "Tôi đã thử bốn mô hình."),
    (f"Three models tie at {pct(best_test)} on the test set.", f"Ba mô hình hoà nhau ở mức {pct(best_test)} trên tập kiểm tra."),
    ("SVM has the best validation score.", "SVM có điểm kiểm định tốt nhất."),
    ("The decision tree is the weakest on the test set.", "Cây quyết định yếu nhất trên tập kiểm tra.")], section=sec, github=NB_URL["ml"])
image(s, "ml_accuracy_comparison.png", 0.6, 1.4, 7.0, 3.6)
mt = pd.DataFrame([(m["Model"], pct(m["val"]), pct(m["test"]), f"{pct(cvs[m['Model']][0])} ± {cvs[m['Model']][1] * 100:.1f}") for m in models],
                  columns=["Model", "Validation", "Test", f"10-fold CV (all {F['n']})"])
table(s, mt, 7.8, 1.5, 4.93, col_w=[1.6, 1.0, 0.8, 1.53], size=11, row_h=0.45)
bp = pd.DataFrame([(m["Model"], m["params"].replace("'", "").strip("{}")) for m in models], columns=["Model", "Best parameters (GridSearchCV)"])
table(s, bp, 0.6, 5.1, W - 1.2, col_w=[2.3, 9.83], size=11, row_h=0.32)

s = slide("Confusion Matrix", [
    (f"The test set has {F['test_n']} launches.", f"Tập kiểm tra có {F['test_n']} lần phóng."),
    ("All landed boosters are predicted correctly by three models.", "Ba mô hình dự đoán đúng tất cả tầng đẩy đã hạ cánh."),
    ("The problem is false positives.", "Vấn đề là dương tính giả."),
    ("Some failed landings are predicted as landed.", "Một số lần hạ cánh thất bại bị dự đoán là đã hạ cánh.")], section=sec, github=NB_URL["ml"])
image(s, "ml_confusion_matrices.png", 0.6, 1.4, W - 1.2, 3.4)
tn, fp, fn, tp = cms["SVM"]
textbox(s, 0.6, 4.95, W - 1.2, 1.3, [
    {"text": [("LR, SVM and KNN: ", True), (f"same matrix – TP = {tp}, TN = {tn}, FP = {fp}, FN = {fn}. Every landed booster is found (recall = {tp / (tp + fn):.0%}), but {fp} of {tn + fp} non-landings are wrongly predicted as landed.", False)], "size": 15},
    {"text": [("Decision Tree: ", True), (f"TP = {cms['Decision Tree'][3]}, TN = {cms['Decision Tree'][0]}, FP = {cms['Decision Tree'][1]}, FN = {cms['Decision Tree'][2]} – it also misses {cms['Decision Tree'][2]} real landings.", False)], "size": 15}])
insight(s, "The main error is the false positive: the models are too optimistic about landing. For cost estimates this is the risky mistake (a bid would assume a reusable booster).", y=6.15, h=0.72)

s = slide("Best Model", [
    ("On the test set, three models are equal.", "Trên tập kiểm tra, ba mô hình bằng nhau."),
    ("The test set is small, so this tie is not surprising.", "Tập kiểm tra nhỏ nên việc hoà không có gì lạ."),
    ("SVM is a little better in cross validation.", "SVM tốt hơn một chút khi kiểm định chéo."),
    ("So I choose SVM, but the difference is small.", "Vì vậy tôi chọn SVM, nhưng khác biệt là nhỏ.")], section=sec, github=NB_URL["ml"])
svm = next(m for m in models if m["Model"] == "SVM")
box(s, 0.6, 1.5, 5.4, 4.6, fill=NAVY)
textbox(s, 0.9, 1.65, 4.9, 4.3, [
    {"text": "Selected model", "size": 16, "color": ORANGE, "bold": True},
    {"text": "Support Vector Machine", "size": 28, "bold": True, "color": WHITE, "space": 14},
    {"text": f"Kernel: sigmoid, C = 1, gamma = {float(re.search(r'gamma.: ([\d.e-]+)', svm['params']).group(1)):.3f}", "size": 15, "color": WHITE},
    {"text": f"Validation accuracy: {pct(svm['val'])} (best of 4)", "size": 15, "color": WHITE},
    {"text": f"Test accuracy: {pct(svm['test'])} (tied best)", "size": 15, "color": WHITE},
    {"text": f"10-fold CV on all data: {pct(cvs['SVM'][0])} (best of 4)", "size": 15, "color": WHITE}])
textbox(s, 6.4, 1.5, 6.33, 4.7, [
    {"text": "Why SVM – and an honest warning", "size": 18, "bold": True, "color": TEAL, "space": 10},
    {"text": f"{', '.join(tied)} all score {pct(best_test)} on the test set: the same {F['test_n'] - fp} of {F['test_n']} correct.", "bullet": True, "size": 15},
    {"text": f"With only {F['test_n']} test launches, one prediction = {100 / F['test_n']:.1f} points, so the test set cannot separate these models.", "bullet": True, "size": 15},
    {"text": f"SVM is highest on both validation ({pct(svm['val'])}) and 10-fold CV on all {F['n']} launches ({pct(cvs['SVM'][0])}).", "bullet": True, "size": 15},
    {"text": f"But the CV spread is about ±{cvs['SVM'][1] * 100:.0f} points, so the gap to Logistic Regression ({pct(cvs['Logistic Regression'][0])}) is small.", "bullet": True, "size": 15},
    {"text": "Logistic Regression is a good simpler alternative.", "bullet": True, "size": 15}])

s = slide("What Really Drives Landing Success?", [
    (f"{F['no_attempt']} of the 30 failures were not real failures.", f"{F['no_attempt']} trong 30 lần thất bại không phải thất bại thật."),
    ("SpaceX did not even try to land.", "SpaceX thậm chí không thử hạ cánh."),
    (f"When they tried, {pct0(F['attempt_rate'])} landed.", f"Khi họ thử, {pct0(F['attempt_rate'])} đã hạ cánh."),
    ("So the key question is: will they try to land?", "Vậy câu hỏi chính là: họ có thử hạ cánh không?")], section=sec, github=NB_URL["ml"])
image(s, "ml_landing_drivers.png", 0.6, 1.4, 8.2, 3.6)
textbox(s, 9.0, 1.45, 3.73, 3.6, [
    {"text": f"Class = 0: {F['n'] - F['landed']} launches", "size": 15, "bold": True},
    {"text": f"No landing attempt: {F['no_attempt']}", "bullet": True, "size": 14},
    {"text": f"Attempt failed: {F['attempt_fail']}", "bullet": True, "size": 14, "space": 12},
    {"text": f"Attempted landings: {F['landed']} of {F['attempted']} succeeded ({pct(F['attempt_rate'])})", "size": 14, "bold": True, "space": 12},
    {"text": f"Attempted, by Block: 1 = {pct0(blk_att[1.0])}, 2–4 = {pct0(blk_att[2.0])}, 5 = {pct0(blk_att[5.0])}", "size": 14, "space": 12},
    {"text": f"Reused booster: {pct0(reused[True])} vs. new: {pct0(reused[False])}", "size": 14}])
insight(s, f"Most 'failures' are planned: {F['no_attempt']} of {F['n'] - F['landed']} Class-0 launches had no landing attempt ({F['no_try_gto']} of them GTO). Once SpaceX tries, it lands {pct0(F['attempt_rate'])} of the time – so predicting the mission plan (orbit, payload) matters more than the landing itself.", y=5.15, h=1.05)

# 35. Conclusion ---------------------------------------------------------------------------------
s = slide("Conclusion", [
    ("SpaceX improved very fast over the years.", "SpaceX tiến bộ rất nhanh qua các năm."),
    ("Orbit, payload and experience affect landing.", "Quỹ đạo, tải trọng và kinh nghiệm ảnh hưởng đến hạ cánh."),
    ("Our models predict landing with about eighty-three percent accuracy.", "Mô hình của chúng tôi dự đoán hạ cánh với độ chính xác khoảng tám mươi ba phần trăm."),
    ("My advice: first predict if SpaceX will try to land.", "Lời khuyên của tôi: hãy dự đoán trước SpaceX có thử hạ cánh không.")], github=REPO)
textbox(s, 0.6, 1.45, 7.1, 4.9, [
    {"text": f"Experience matters: success rose from 0% (2010–2013) to {pct0(yearly[2019])} (2019); flights 61–90 land {pct0(last30)} vs. {pct0(first30)} for flights 1–30.", "bullet": True, "size": 15, "space": 10},
    {"text": f"Orbit matters: VLEO {pct0(orbit.loc['VLEO', 'mean'])}, ISS {pct0(orbit.loc['ISS', 'mean'])}, GTO only {pct0(orbit.loc['GTO', 'mean'])} (heavy GTO payloads are hardest).", "bullet": True, "size": 15, "space": 10},
    {"text": f"Launch sites are all next to the coast, near rail, and far from cities; {best_site} has the best success rate in the dashboard data ({pct0(dsite.loc[best_site, 'mean'])}).", "bullet": True, "size": 15, "space": 10},
    {"text": f"Payloads of 2,000–4,000 kg and FT boosters show the best success in the dashboard data.", "bullet": True, "size": 15, "space": 10},
    {"text": f"LR, SVM and KNN reach {pct(best_test)} test accuracy; SVM is chosen (best validation / CV), but the small test set means the models are nearly equal.", "bullet": True, "size": 15}])
box(s, 8.0, 1.45, 4.73, 4.85, fill=NAVY)
textbox(s, 8.25, 1.55, 4.3, 4.7, [
    {"text": "Creative insight", "size": 20, "bold": True, "color": ORANGE, "space": 10},
    {"text": f"\"Failure\" is mostly a choice. {F['no_attempt']} of {F['n'] - F['landed']} non-landings had no landing attempt; {F['no_try_gto']} of them were GTO missions.", "size": 15, "color": WHITE, "space": 8},
    {"text": f"This also explains the 2018 dip: {F['no_try_2018']} launches that year did not try to land.", "size": 15, "color": WHITE, "space": 8},
    {"text": f"When SpaceX tries, it lands {pct0(F['attempt_rate'])} of the time.", "size": 15, "color": WHITE, "space": 8},
    {"text": "Advice for Space Y: price a bid in two steps – (1) will SpaceX try to land for this orbit and payload? (2) if yes, expect the booster to be reused.", "size": 15, "color": WHITE}])

# 36. Appendix ---------------------------------------------------------------------------------
s = slide("Appendix: Data Sources and Notes", [
    ("This slide lists my data sources.", "Slide này liệt kê các nguồn dữ liệu của tôi."),
    ("The SpaceX API was down, so I used saved copies of the same data.", "SpaceX API bị lỗi nên tôi dùng bản lưu của cùng dữ liệu đó."),
    ("Everything is in the GitHub repository.", "Mọi thứ đều có trong kho GitHub.")], github=REPO)
textbox(s, 0.6, 1.45, W - 1.2, 4.9, [
    {"text": "SpaceX REST API v4 (api.spacexdata.com) – live server returned HTTP 522/525 in Oct 2026; used IBM static copy of /launches/past and archived API responses from web.archive.org (rockets, payloads, launchpads, cores).", "bullet": True, "size": 14, "space": 8},
    {"text": f"Validation: our dataset_part_1.csv matches IBM's reference in {F['cols_identical']} of {F['cols_total']} columns; small differences in PayloadMass and ReusedCount come from a newer API snapshot.", "bullet": True, "size": 14, "space": 8},
    {"text": "Wikipedia: List of Falcon 9 and Falcon Heavy launches, revision oldid = 1027686922.", "bullet": True, "size": 14, "space": 8},
    {"text": "IBM course files: Spacex.csv (SQL), spacex_launch_geo.csv (Folium), spacex_launch_dash.csv (Dash).", "bullet": True, "size": 14, "space": 8},
    {"text": "OpenStreetMap via Overpass API for nearest coastline, railway, highway and city (© OpenStreetMap contributors, ODbL). Note: the course file places KSC LC-39A slightly inland, so we show proximity for CCAFS SLC-40.", "bullet": True, "size": 14, "space": 8},
    {"text": "Tools: Python 3.12, pandas, numpy, requests, BeautifulSoup, matplotlib, seaborn, sqlite3, folium, plotly / Dash, scikit-learn, Playwright (screenshots).", "bullet": True, "size": 14, "space": 8},
    {"text": "Maps (interactive HTML): images/folium_1_launch_sites.html, folium_2_launch_outcomes.html, folium_3_proximity.html", "bullet": True, "size": 14}])

# ---------------------------------------------------------------- save --
pptx_path = os.path.join(HERE, "Data Science Capstone Project Report.pptx")
prs.save(pptx_path)
print("saved", pptx_path, "-", len(prs.slides), "slides")

with open(os.path.join(HERE, "speaker_notes.md"), "w", encoding="utf-8") as f:
    f.write("# Speaker Notes – Data Science Capstone Project Report\n\n")
    f.write("Short, simple English sentences with the Vietnamese translation.\n\n")
    for i, (title, notes) in enumerate(NOTES, 1):
        f.write(f"## Slide {i} – {title}\n\n")
        for en, vi in notes:
            f.write(f"- {en} — *{vi}*\n")
        f.write("\n")
print("saved speaker_notes.md")

# PDF export with Microsoft PowerPoint (Windows)
try:
    import comtypes.client
except ImportError:
    comtypes = None
pdf_path = os.path.join(HERE, "Data Science Capstone Project Report.pdf")
if comtypes:
    app = comtypes.client.CreateObject("PowerPoint.Application")
    deck = app.Presentations.Open(pptx_path, WithWindow=False)
    deck.SaveAs(pdf_path, 32)          # 32 = ppSaveAsPDF
    deck.Close()
    app.Quit()
    print("saved", pdf_path)
else:
    print("comtypes not installed: open the .pptx in PowerPoint and export to PDF")
