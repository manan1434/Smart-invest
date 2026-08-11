# SmartInvest

**AI-Powered Investment Advisory Platform** — personalized portfolio allocation, stock forecasting, and real estate ROI recommendations.

> Patent-published research project. Outputs are model-driven and for educational/demo purposes only; not financial advice.

---

## What it does

SmartInvest helps users explore investment decisions across four asset classes:

| Feature | Description |
|---------|-------------|
| **Portfolio allocation** | ML-based split across stocks, bonds, gold, and real estate from your risk profile |
| **Stock predictor** | LSTM forecasts for 7 tickers (AAPL, MSFT, TSLA, GOOGL, AMZN, NFLX, DPZ) |
| **Real estate ROI** | Top property recommendations with 10-year ROI and rental projections |
| **Gold insights** | Trend charts (demo UI; static data) |

Users sign up, complete a financial profile questionnaire, and access dashboards and prediction tools through a web UI.

---

## Architecture (at a glance)

```
Browser  →  Node.js (Express) :4000  →  MySQL
                ↓
         Flask ML API :5000
                ├── Model 1: Portfolio allocation (XGBoost)
                ├── Model 2: Stock LSTM (Keras)
                └── Model 3: Real estate ROI (sklearn)
```

Stock and real-estate pages call Flask directly from the browser. The main AI dashboard is orchestrated by Node.

**Full documentation:** [docs/PRODUCT.md](docs/PRODUCT.md)

---

## Project structure

```
Smart-Investment-Project/
├── README.md                 ← you are here
├── LICENSE
├── docs/
│   └── PRODUCT.md            ← end-to-end product & API docs
└── smart_invest/
    └── SmartInvest-AI-Powered-Investment-Advisory-System/
        ├── index.js          # Express backend
        ├── package.json
        ├── public/             # HTML UI
        ├── views/              # EJS templates
        └── flask app/          # Python ML API & models
```

---

## Prerequisites

- **Node.js** 18+
- **Python** 3.9+
- **MySQL** Server
- ~500 MB disk for model files and datasets (included in `flask app/`)

---

## Quick start

### 1. Clone and enter the app

```bash
cd smart_invest/SmartInvest-AI-Powered-Investment-Advisory-System
```

### 2. Set up MySQL

Create the database and user table:

```sql
CREATE DATABASE investment;

CREATE TABLE test (
  email VARCHAR(255) PRIMARY KEY,
  password VARCHAR(255) NOT NULL,
  fullname VARCHAR(255),
  age INT,
  gender VARCHAR(50),
  education_level VARCHAR(100),
  annual_income DECIMAL(15, 2),
  investment_amount DECIMAL(15, 2),
  financial_knowledge INT,
  risk_tolerance INT,
  investment_horizon VARCHAR(50)
);
```

Edit database credentials in `index.js` (`host`, `user`, `password`, `database`).

### 3. Install and run the ML API (terminal 1)

```bash
pip install flask flask-cors pandas numpy joblib scikit-learn xgboost tensorflow matplotlib

python "flask app/app.py"
```

Runs at **http://127.0.0.1:5000**

### 4. Install and run the web app (terminal 2)

```bash
npm install
node index.js
```

Runs at **http://localhost:4000**

### 5. Use the app

1. Open http://localhost:4000  
2. **Sign up** → fill the investment profile → **log in**  
3. Open **Dashboard** (`/dashboard`) for AI portfolio allocation (requires Flask)  
4. Use **Stocks** and **Real Estate** pages for specialized predictions  

---

## ML models (summary)

| Model | File | Purpose |
|-------|------|---------|
| 1 | `model1_allocation.pkl` | 4-way portfolio allocation + pie chart |
| 2 | `model2_stock_predictor.h5` | Multi-stock price feature prediction |
| 3 | `model3_property_predictor.pkl` | Top 5 real estate picks by ROI |

Training script for Model 1: `flask app/train_model.py`  
Dataset: `synthetic_investment_dataset_30k.csv`

See [docs/PRODUCT.md](docs/PRODUCT.md) for algorithms, features, and API details.

---

## Tech stack

| Layer | Stack |
|-------|--------|
| Frontend | HTML, Tailwind CDN, Chart.js, EJS |
| Backend | Node.js, Express 5, bcrypt, mysql2 |
| ML | Python, Flask, XGBoost, TensorFlow/Keras, scikit-learn |
| Database | MySQL |

---

## API endpoints (Flask)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | POST | Portfolio allocation from user profile |
| `/predict_stocks` | POST | Stock predictions for a date |
| `/predict_properties` | POST | Top real estate options for investment amount |

Express routes and request shapes are documented in [docs/PRODUCT.md](docs/PRODUCT.md).

---

## Important notes

- **Two servers required** — Node (4000) and Flask (5000) for full functionality.  
- **After login**, visit `/dashboard` for the AI allocation view (login lands on a static hub page).  
- **Do not use hardcoded DB passwords in production** — move secrets to environment variables.  
- **Gold page** uses static demo data, not a trained model.

---

## License

MIT — see [LICENSE](LICENSE).

Copyright (c) 2026 Mahi-Jadeja.

---

## Documentation

| Document | Contents |
|----------|----------|
| [docs/PRODUCT.md](docs/PRODUCT.md) | Full product documentation: flows, models, APIs, schema, limitations |
