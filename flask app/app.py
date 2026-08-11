from flask import Flask, request, jsonify  # type: ignore
from flask_cors import CORS  # type: ignore
import pandas as pd  # type: ignore
import numpy as np
import joblib  # type: ignore
import matplotlib  # type: ignore
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # type: ignore
import io
import base64
import traceback
from datetime import datetime
from tensorflow.keras.models import load_model  # type: ignore
from sklearn.linear_model import Ridge

app = Flask(__name__)
CORS(app)

# ========== Load trained models and data ==========
model1 = joblib.load('flask app/model1_allocation.pkl')
model2 = load_model('flask app/model2_stock_predictor.h5', compile=False)
scaler = joblib.load('flask app/scaler_stock_predictor.pkl')
df_scaled = pd.read_csv('flask app/df_scaled.csv')
feature_columns = [col for col in df_scaled.columns if col != "Date"]  # Features except Date


# Model 3 files
model3 = joblib.load('flask app/model3_property_predictor.pkl')
test_df = pd.read_csv('flask app/testing.csv')

# Feature columns for property model
feature_cols = ['city', 'property_type', 'bhk', 'size_sqft', 'total_price', 'pooled_amount']
X_columns = joblib.load('flask app/X_columns_property.pkl')  # Columns after one-hot encoding

bin_centers = [12.5, 37.5, 62.5, 87.5]
target_columns = ['Stocks (%)', 'Bonds (%)', 'Gold (%)', 'Real Estate (%)']
# ===================================================

# ========== Model 1: Portfolio Allocation ==========
def enrich_user_input(user_input):
    data = user_input.copy()
    income = data['Income']
    investment = data['Investment Amount']

    data['Debt-to-Income Ratio'] = round(investment / (income + 1e-6), 2)
    data['Net Worth'] = round((income * 4.5) + investment, 2)

    if data['Education Level'] in ['Post-Graduate', 'Doctorate']:
        data['Occupation'] = 'Professional' if income > 100000 else 'Researcher'
    elif data['Education Level'] == 'Graduate':
        data['Occupation'] = 'Engineer' if income > 70000 else 'Technician'
    else:
        data['Occupation'] = 'Clerk'

    data['Savings_Rate'] = round(data['Net Worth'] / (income + 1e-6), 2)
    data['Risk_Adjusted_Net_Worth'] = round(data['Net Worth'] * (1 - (data['Risk Tolerance'] / 10)), 2)

    return pd.DataFrame([data])

@app.route('/predict', methods=['POST'])
def predict_allocation():
    try:
        data = request.json
        user_input = {
            'Age': data['age'],
            'Gender': data['gender'],
            'Education Level': data['education_level'],
            'Income': data['annual_income'],
            'Investment Amount': data['investment_amount'],
            'Financial Knowledge': data['financial_knowledge'],
            'Risk Tolerance': data['risk_tolerance'],
            'Investment Horizon': data['investment_horizon']
        }

        user_df = enrich_user_input(user_input)
        class_predictions = model1.predict(user_df)[0]
        expected_percentages = [bin_centers[class_idx] for class_idx in class_predictions]

        total = sum(expected_percentages)
        normalized_percentages = [round((x / total) * 100, 2) for x in expected_percentages]

        fig, ax = plt.subplots()
        ax.pie(normalized_percentages, labels=target_columns, autopct='%1.1f%%', startangle=90,
               colors=['#4e79a7', '#59a14f', '#f28e2c', '#e15759'])
        ax.axis('equal')

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        chart_base64 = base64.b64encode(img.getvalue()).decode()
        plt.close()

        result = {
            "stocks": normalized_percentages[0],
            "bonds": normalized_percentages[1],
            "gold": normalized_percentages[2],
            "real_estate": normalized_percentages[3],
            "chart": f"data:image/png;base64,{chart_base64}"
        }

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ========== Model 2: Stock Price Prediction ==========
def predict_all_stocks(future_date, sequence_length=60):
    last_sequence = df_scaled.iloc[-sequence_length:].drop(columns=["Date"]).values.reshape(1, sequence_length, -1)
    predicted_scaled_prices = model2.predict(last_sequence)[0]
    predicted_prices = scaler.inverse_transform([predicted_scaled_prices])[0]

    future_date_obj = datetime.strptime(future_date, "%Y-%m-%d")
    stock_predictions = {col: predicted_prices[i] for i, col in enumerate(feature_columns)}

    return future_date_obj, stock_predictions

@app.route('/predict_stocks', methods=['POST'])
def predict_stocks():
    try:
        data = request.json
        future_date = data['future_date']

        future_date_obj, predictions = predict_all_stocks(future_date)

        result = {
            "date": future_date_obj.strftime("%Y-%m-%d"),
            "predictions": {stock: round(price, 2) for stock, price in predictions.items()}
        }

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ========== Model 3: Real Estate Property Recommendation ==========
def recommend_properties(user_investment, test_data, model, train_encoded_cols):
    df = test_data.copy()

    # One-hot encode & align
    df_encoded = pd.get_dummies(df[feature_cols], drop_first=True)
    df_encoded = df_encoded.reindex(columns=train_encoded_cols, fill_value=0)

    # Predict ROI
    df['predicted_roi_year_10'] = model.predict(df_encoded)
    df['appreciated_price'] = df['total_price'] * (1 + df['predicted_roi_year_10'])

    # Ownership calculations
    df['ownership_percent'] = df['pooled_amount'] / df['total_price']
    df['user_ownership_percent'] = (user_investment / df['pooled_amount']).clip(upper=1.0)
    df['company_ownership'] = 1 - df['ownership_percent']

    # Rental income (base 3% annual)
    df['base_rent'] = df['total_price'] * 0.03
    df['user_rental_income_years'] = [
        [((row['base_rent'] * (1 + row['predicted_roi_year_10']) ** year) * row['user_ownership_percent']) for year in range(1, 11)]
        for _, row in df.iterrows()
    ]

    # Investment ROI
    df['user_returns_years'] = [
        [roi * user_investment for roi in [row['predicted_roi_year_10'] * (yr / 10) for yr in range(1, 11)]]
        for _, row in df.iterrows()
    ]

    # Total projected return
    df['total_return'] = [sum(r) for r in df['user_returns_years']]
    df['total_rental_income'] = [sum(r) for r in df['user_rental_income_years']]
    df['total_roi'] = df['total_return'] + df['total_rental_income']

    # Predicted ROI for each year
    roi_columns = [f'predicted_roi_year_{i}' for i in range(1, 11)]
    for i, col in enumerate(roi_columns, start=1):
        df[col] = df['predicted_roi_year_10'] * (i / 10)

    # Format currency columns
    for col in ['total_return', 'total_rental_income', 'total_roi']:
        df[col] = df[col] / 1e5  # Convert to lakhs
        df[col] = df[col].round(2)

    df_filtered = df[df['user_ownership_percent'] <= 1.0]
    top_df = df_filtered.sort_values(by='total_roi', ascending=False).head(5)

    return top_df[[ 'city', 'property_type', 'bhk', 'size_sqft', 'total_price', 'user_ownership_percent', 'predicted_roi_year_10', 'total_return', 'total_rental_income', 'total_roi' ] + roi_columns]

@app.route('/predict_properties', methods=['POST'])
def predict_properties():
    try:
        data = request.json
        user_investment = data.get('investment_amount', 100000)

        top_props = recommend_properties(user_investment, test_df, model3, X_columns)
        result = top_props.to_dict(orient='records')

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ================================
if __name__ == '__main__':

    app.run(port=5000, debug=True)