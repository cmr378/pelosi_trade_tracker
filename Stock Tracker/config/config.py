from pathlib import Path

# URL for downloading disclosure data
DOWNLOAD_URL = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2024FD.zip"

# Define base paths
BASE_DIR = Path(__file__).parent.parent
OUTPUT_FOLDER = BASE_DIR / "data" / "public_disclosures"
JSON_OUTPUT = BASE_DIR / "data" / "transactions" / "pelosi_trades.json"
PDF_OUTPUT = BASE_DIR / "data" / "transaction_pdfs"