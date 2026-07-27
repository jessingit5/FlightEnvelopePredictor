# AeroSpecML

Predicting how fast a military aircraft can fly, using nothing but specs pulled straight from Wikipedia.

## What this is

I scrape physical and engine specs (empty weight, wingspan, engine thrust, wing area, and so on) for active US military aircraft directly from Wikipedia's `{{Aircraft specs}}` infobox template, then use that data to predict top speed with regularized linear regression (Ridge, Lasso, ElasticNet), tuned with GridSearchCV.

No Kaggle dataset. No synthetic data. Just Wikipedia, a scraper I wrote myself, and the reality that real data is messier than any textbook example ever lets on.

## Why this project

Most portfolio regression projects reach for the same handful of datasets (concrete strength, Boston housing, you know the ones). This one uses real, scraped data instead, specs pulled straight from Wikipedia, cleaned and consolidated by hand rather than downloaded pre-packaged.

Regularization also isn't just there to check a box. The features here are genuinely correlated with each other, engine thrust, empty weight, and wing area all move together depending on the aircraft class, so Ridge and Lasso have a real job to do, not a toy one.

## The data

`scrape_aircraft_data.py` pulls the list of active US military aircraft from Wikipedia, then visits each aircraft's page and extracts its spec template. A few things worth knowing before you dig into the CSV:

- Not every aircraft makes it in. Helicopters, gliders, and drones sometimes use different infobox templates than fighters, bombers, and transports do, so some get skipped. That's noted when the scraper runs.
- Speed shows up as either Mach number or knots depending on the aircraft, and range shows up as combat range, ferry range, or plain range, never all three at once. These get consolidated during cleaning rather than treated as separate features.
- Wikipedia is crowd-maintained, so there's noise: missing fields, inconsistent reporting between similar aircraft. That's real data collection, and I'd rather show that honestly than pretend the dataset showed up perfectly clean.

## Approach

1. Scrape and clean the data
2. EDA: distributions, missing data, correlation between features
3. Baseline: plain linear regression
4. Ridge / Lasso / ElasticNet, tuned via GridSearchCV
5. Compare models, and check whether the surviving features (after Lasso trims things down) actually line up with real aerodynamics

## Status

Data collection is done. Analysis and modeling notebook is in progress.

## Stack

Python, requests, BeautifulSoup, mwparserfromhell, pandas, scikit-learn

## Running it

```bash
pip install -r requirements.txt
python scrape_aircraft_data.py
```

Takes a few minutes. Wikipedia's API rate-limits requests that come in too fast, so the script backs off and retries automatically when that happens, no need to babysit it.

## License

MIT
