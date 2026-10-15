# SolarShare — P2P energy trading

A local Streamlit prototype with seeded household offers, buy/sell entry, partial-fill matching, cancelable open offers, a trade ledger with CSV export, an illustrative energy chart, and household cost tracking.

## Run

Requires Python 3.10 or newer. Open a terminal in this directory and run:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the localhost URL printed by Streamlit. Click **Run matching** to settle the seeded market, then select a household and post another offer. Reset demo restores the starting order book.

## Matching

One shared simulated delivery interval. Descending buy limits and ascending sell limits have priority, with order ID breaking ties. A bid at or above an ask can match, excluding the same household. Each trade uses the midpoint price and the smaller remaining quantity. Running matching again does not duplicate filled trades.

Quantities are in kWh; prices are illustrative USD/kWh. Trading is unconstrained by the independent energy profile. No real metering, payments, physical grid validation, or persistent database is connected. Browser sessions have separate in-memory state. Grid-rate changes recalculate comparisons for the entire ledger.

## Verify

```sh
python -m unittest discover -s . -p 'test_*.py'
```

Streamlit forms and session state follow the official documentation:
https://docs.streamlit.io/develop/concepts/architecture/forms
https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state

## Deploy to Streamlit Community Cloud

1. Put this directory's contents at the root of a GitHub repository.
2. Sign in at https://share.streamlit.io/ and choose **Create app**.
3. Select the repository, its branch, and `app.py` as the entrypoint.
4. In advanced settings, choose **Python 3.12**, then deploy.

No application secrets are required. Each visitor has a separate demo session.

Official instructions: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

## Deploy with Docker

A Dockerfile is included for hosts that support containers. It listens on the host's `PORT` environment variable, or 8501 by default. The host must support WebSocket connections. Health check path: `/_stcore/health`.

```sh
docker build -t solarshare .
docker run --rm -p 8501:8501 solarshare
```
