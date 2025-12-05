
import json
import pandas as pd
from io import StringIO

from google.cloud import storage
from services.base import GoogleAdsService

class GCSGoogleAdsService(GoogleAdsService):
    """GCS-based implementation of GoogleAdsService."""
    def __init__(self, gcs_bucket: str):
        self.gcs_bucket = gcs_bucket
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(gcs_bucket)

    def _read_gcs_file(self, file_path: str):
        blob = self.bucket.blob(file_path)
        content = blob.download_as_string().decode('utf-8')
        return content

    def get_targeting_data(self, file_path: str, **kwargs) -> list[dict]:
        """Reads Google Ads targeting data from a GCS file."""
        content = self._read_gcs_file(file_path)
        if file_path.endswith('.json'):
            return json.loads(content)
        elif file_path.endswith('.csv'):
            return pd.read_csv(StringIO(content)).to_dict(orient='records')
        else:
            raise ValueError("Unsupported file format for Google Ads targeting data.")

    def get_product_data(self, file_path: str, **kwargs) -> list[dict]:
        """Reads Google Ads product data from a GCS file."""
        content = self._read_gcs_file(file_path)
        if file_path.endswith('.json'):
            return json.loads(content)
        elif file_path.endswith('.csv'):
            return pd.read_csv(StringIO(content)).to_dict(orient='records')
        else:
            raise ValueError("Unsupported file format for Google Ads product data.")
