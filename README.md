# SpaceX Falcon 9 First-Stage Landing Prediction – IBM Applied Data Science Capstone

Predict whether the Falcon 9 first stage will land successfully. SpaceX advertises launches at about $62M, while other
providers charge $165M+; most of the saving comes from reusing the first stage. If we can predict the landing, we can
estimate the cost of a launch.

**Final report:** [`slides/Data Science Capstone Project Report.pdf`](slides/Data%20Science%20Capstone%20Project%20Report.pdf)

## Project structure

| Step | File | What it does |
|---|---|---|
| 1 | [`notebooks/01_data_collection_api.ipynb`](notebooks/01_data_collection_api.ipynb) | SpaceX REST API → `data/dataset_part_1.csv` (90 Falcon 9 launches) |
| 2 | [`notebooks/02_data_collection_webscraping.ipynb`](notebooks/02_data_collection_webscraping.ipynb) | Scrape Wikipedia (oldid 1027686922) → `data/spacex_web_scraped.csv` (121 rows) |
| 3 | [`notebooks/03_data_wrangling.ipynb`](notebooks/03_data_wrangling.ipynb) | Missing values, `Class` label → `dataset_part_2.csv`, one-hot features → `dataset_part_3.csv` |
| 4 | [`notebooks/04_eda_visualization.ipynb`](notebooks/04_eda_visualization.ipynb) | 7 charts (scatter, bar, yearly trend) with insights |
| 5 | [`notebooks/05_eda_sql.ipynb`](notebooks/05_eda_sql.ipynb) | 10 SQL questions on SQLite |
| 6 | [`notebooks/06_interactive_folium_map.ipynb`](notebooks/06_interactive_folium_map.ipynb) | Folium maps: sites, green/red launch markers, proximity analysis |
| 7 | [`notebooks/07_dash_app.py`](notebooks/07_dash_app.py) | Plotly Dash dashboard (+ [`07_dash_screenshots.py`](notebooks/07_dash_screenshots.py) for screenshots and numbers) |
| 8 | [`notebooks/08_predictive_analysis.ipynb`](notebooks/08_predictive_analysis.ipynb) | Logistic Regression, SVM, Decision Tree, KNN with GridSearchCV |
| – | [`slides/build_slides.py`](slides/build_slides.py) | Builds the PPTX + PDF; every number is computed from the data / notebook outputs |

`images/` holds every chart, map (PNG + interactive HTML), Dash screenshot and confusion matrix.
`slides/speaker_notes.md` has short English speaker notes with Vietnamese translation.

## Key results

- 90 Falcon 9 launches (2010–2020); 60 landed → **66.7%** overall success.
- Success grew from 0% (2010–2013) to 90% in 2019.
- Among common orbits VLEO is best (86%) and GTO is weakest (52%).
- KSC LC-39A has the highest success rate in the dashboard data (76.9%).
- Logistic Regression, SVM and KNN all reach **83.3%** test accuracy (15 of 18); SVM has the best validation
  (84.8%) and 10-fold CV (84.4%) accuracy. The test set is small, so the models are nearly equal.
- 21 of the 30 non-landings were launches with **no landing attempt**; when SpaceX tried, it landed 87% of the time.

## Data sources and notes

- **SpaceX API v4** – in October 2026 the live server `api.spacexdata.com` returned HTTP 522/525 on every endpoint.
  Notebook 01 tries the live API first, then falls back to saved copies of the same API responses:
  the IBM course static copy of `/launches/past` and archived responses from web.archive.org
  (rockets, payloads, launchpads, cores). These files are cached in `data/raw/`.
  Our `dataset_part_1.csv` matches IBM's reference file in 15 of 17 columns; `PayloadMass` (16 rows) and
  `ReusedCount` (6 rows) differ because the archived API snapshot is newer.
- **Wikipedia** – "List of Falcon 9 and Falcon Heavy launches", revision `oldid=1027686922`.
- **IBM course files** – `Spacex.csv` (SQL), `spacex_launch_geo.csv` (Folium), `spacex_launch_dash.csv` (Dash).
- **OpenStreetMap** (Overpass API) – nearest coastline, railway, highway and city, cached in `data/raw/osm_cache.json`.

## How to run

```bash
pip install -r requirements.txt
python -m playwright install chromium     # only needed for screenshots
cd notebooks
jupyter notebook                           # run 01 → 08 in order
python 07_dash_app.py                      # dashboard at http://127.0.0.1:8050
python 07_dash_screenshots.py              # screenshots + dashboard numbers
cd ../slides && python build_slides.py     # PPTX + PDF (PDF export needs PowerPoint on Windows)
```
