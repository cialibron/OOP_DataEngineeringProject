import os
import pandas as pd


class StagingDataLoader:
    """Handles loading datasets from the staging directory."""

    def __init__(self, staging_dir: str = "staging"):
        self.staging_dir = staging_dir

    def load(self, file_name: str) -> pd.DataFrame:
        path = os.path.join(self.staging_dir, file_name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Staged file not found: {path}")
        return pd.read_parquet(path)


class DataTransformer:
    """Contains modular logic for data cleaning, type casting, and feature calculation."""

    @staticmethod
    def transform_trips(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # Cast timestamp fields to datetime
        for col in ["scheduled_start_time", "actual_start_time", "actual_end_time"]:
            df[col] = pd.to_datetime(df[col])

        # Compute calculated fields
        df["delay_minutes"] = (
            (df["actual_start_time"] - df["scheduled_start_time"]).dt.total_seconds() / 60.0
        ).round(1)

        df["trip_duration_min"] = (
            (df["actual_end_time"] - df["actual_start_time"]).dt.total_seconds() / 60.0
        ).round(1)

        return df

    @staticmethod
    def transform_transactions(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["tap_timestamp"] = pd.to_datetime(df["tap_timestamp"])
        df["fare_amount"] = df["fare_amount"].astype(float)
        df["tap_hour"] = df["tap_timestamp"].dt.hour
        return df

    @staticmethod
    def transform_maintenance(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["service_date"] = pd.to_datetime(df["service_date"])
        df["cost"] = df["cost"].astype(float)
        return df


class DataExporter:
    """Handles saving transformed DataFrames into output storage formats."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def export(self, df: pd.DataFrame, file_name: str):
        # Clean CSV export for database ingestion (e.g., Supabase)
        csv_filename = file_name.replace(".parquet", "_cleaned.csv")
        csv_path = os.path.join(self.output_dir, csv_filename)
        df.to_csv(csv_path, index=False)

        # Parquet export for analytics layer
        parquet_path = os.path.join(self.output_dir, file_name)
        df.to_parquet(parquet_path, index=False)

        print(f"✅ [TRANSFORMED] {file_name} -> Saved to {self.output_dir}/")


class TransformationPipeline:
    """Orchestrates data loading, cleaning, metric calculation, and exporting."""

    def __init__(self, staging_dir: str = "staging", output_dir: str = "output"):
        self.loader = StagingDataLoader(staging_dir)
        self.transformer = DataTransformer()
        self.exporter = DataExporter(output_dir)

    def run(self):
        print("Starting OOP Transformation Pipeline...\n" + "=" * 45)

        # 1. Vehicles
        vehicles = self.loader.load("vehicles.parquet")
        self.exporter.export(vehicles, "vehicles.parquet")

        # 2. Routes
        routes = self.loader.load("routes.parquet")
        self.exporter.export(routes, "routes.parquet")

        # 3. Trips (Enriched with delays & duration)
        trips = self.loader.load("trips.parquet")
        trips_clean = self.transformer.transform_trips(trips)
        self.exporter.export(trips_clean, "trips.parquet")

        # 4. Passenger Transactions (Enriched with tap hour)
        tx = self.loader.load("passenger_transactions.parquet")
        tx_clean = self.transformer.transform_transactions(tx)
        self.exporter.export(tx_clean, "passenger_transactions.parquet")

        # 5. Maintenance
        maint = self.loader.load("maintenance.parquet")
        maint_clean = self.transformer.transform_maintenance(maint)
        self.exporter.export(maint_clean, "maintenance.parquet")


if __name__ == "__main__":
    pipeline = TransformationPipeline()
    pipeline.run()