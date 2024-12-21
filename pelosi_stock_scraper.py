import requests
from pathlib import Path
import zipfile
from datetime import datetime
import time

DOWNLOAD_URL = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2024FD.zip"
OUTPUT_FOLDER = Path("public_disclosures")
CURRENT_DISCLOSURE = None
CHECK_INTERVAL = 30  # Default is 1 hour


def get_most_recent_file_by_name(directory):
    try:
        files = list(directory.glob("*.txt"))  
        if not files:
            print("No files found in the directory.")
            return None

        most_recent_file = max(
            files, key=lambda f: datetime.strptime(f.stem, "%a_%d_%b_%Y_%H-%M-%S_GMT")
        )
        print(f"Most recent file by name: {most_recent_file}")
        return most_recent_file
    except Exception as e:
        print(f"Error finding most recent file by name: {e}")
        return None
    

def download_file(url, output_folder):
    try:
        response = requests.head(url)
        response.raise_for_status()
        last_modified = response.headers.get("Last-Modified")

        if not last_modified:
            print("Last-Modified header not found. Aborting download.")
            return
        
        if CURRENT_DISCLOSURE:
            most_recent_timestamp = datetime.strptime(CURRENT_DISCLOSURE.stem, "%a_%d_%b_%Y_%H-%M-%S_GMT")
            last_modified_timestamp = datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S GMT")
            
            if most_recent_timestamp == last_modified_timestamp:
                print("File hasn't been updated. Skipping download.")
                return 

        new_file_name = last_modified.replace(",", "").replace(" ", "_").replace(":", "-") + ".txt"
        print(f"Using new_file_name with last_modified as file name: {new_file_name}")

        response = requests.get(url, stream=True)
        response.raise_for_status()
        zip_path = output_folder / "temp_download.zip"

        with open(zip_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"File downloaded successfully: {zip_path}")

        if zipfile.is_zipfile(zip_path):
            extract_path = output_folder
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            print(f"File unzipped successfully to: {extract_path}")

            for file in extract_path.iterdir():
                if file.suffix == ".txt":
                    new_name = extract_path / new_file_name
                    file.rename(new_name)
                    print(f"Renamed text file to: {new_name}")
                elif file.suffix == ".xml":
                    file.unlink()
                    print(f"Deleted XML file: {file}")

            zip_path.unlink()
            print(f"ZIP file removed: {zip_path}")

    except Exception as e:
        print(f"Error downloading or processing file: {e}")

def parse_text_file(file_path):
    pelosi_trades = {}
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                fields = [field.strip() for field in line.split('\t')]
                if fields[1] == "Pelosi":
                    pelosi_trades[fields[-1]] = fields[-2] # doc_id, trade_date 
        return pelosi_trades
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return {}
    except Exception as e:
        print(f"Error reading file: {e}")
        return {}

if __name__ == "__main__":
    # Ensure the directory exists
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    while True:
        if any(OUTPUT_FOLDER.glob("*.txt")):
            CURRENT_DISCLOSURE = Path(get_most_recent_file_by_name(OUTPUT_FOLDER))
        
        download_file(DOWNLOAD_URL, OUTPUT_FOLDER)
        if CURRENT_DISCLOSURE:
            holdings = parse_text_file(CURRENT_DISCLOSURE)
            print(holdings)

        print(f"Waiting for {CHECK_INTERVAL} seconds before checking again...")
        time.sleep(CHECK_INTERVAL)







