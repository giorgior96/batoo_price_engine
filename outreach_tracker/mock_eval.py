import requests
import json
import random

# Facciamo finta che l'API locale sia accesa. Se non lo è, restituiamo un mock.
def get_model_evaluation(model_name, year):
    try:
        response = requests.get(f"http://localhost:8000/evaluate?q={model_name}&year={year}")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
        
    # Mock data per il test
    return {
        "valuation": {
            "average_price_eur": 650000,
            "has_depreciation": True,
            "depreciation_percent": 4.5,
            "liquidity_status": "Normale (Buona Scambiabilità)",
            "liquidity_color": "green",
            "average_price_per_meter": 45000
        }
    }
