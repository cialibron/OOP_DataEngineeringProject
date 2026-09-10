import os
import pandas as pd

RAW_DIR = "raw"
STAGING_DIR = "staging"

EXPECTED_SCHEMAS = {
    "vehicles.csv": ["vehicle_id", "license_plate", "model", "capacity", "status", "manufacture_year"],
    "routes.csv": ["route_id", "route_name", "origin", "destination", "distance_km", "expected_duration_min"],
    "trips.csv": ["trip_id", "route_id", "vehicle_id", "scheduled_start_time", "actual_start_time", "actual_end_time", "status"],
    "passenger_transactions.csv": ["transaction_id", "trip_id", "card_id", "tap_timestamp", "fare_amount", "payment_method"],
    "maintenance.csv": ["maintenance_id", "vehicle_id", "service_date", "issue_type", "description", "cost", "status"]
}

def run_ingestion():
    os.makedirs(STAGING_DIR, exist_ok=True)
    print("Starting Ingestion Pipeline...\n" + "="*40)
    
    for file_name, expected_cols in EXPECTED_SCHEMAS.items():
        raw_path = os.path.join(RAW_DIR, file_name)
        
        if not os.path.exists(raw_path):
            print(f"[ERROR] Missing file: {raw_path}")
            continue
            
        df = pd.read_csv(raw_path)
        
        if df.empty:
            print(f"[WARN] {file_name} is empty.")
            continue
            
        if list(df.columns) != expected_cols:
            print(f"[FAIL] Schema mismatch in {file_name}")
            continue
            
        staging_filename = file_name.replace(".csv", ".parquet")
        staging_path = os.path.join(STAGING_DIR, staging_filename)
        
        df.to_parquet(staging_path, index=False)
        print(f"[PASS] Staged {file_name} -> {staging_path} ({len(df)} rows)")

if __name__ == "__main__":
    run_ingestion()