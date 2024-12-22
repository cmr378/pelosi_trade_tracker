import requests
from pathlib import Path
import zipfile
from datetime import datetime
import time
import json

from PDFHandler import PDFHandler

# Global constants
DOWNLOAD_URL = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2024FD.zip"
OUTPUT_FOLDER = Path("public_disclosures")
JSON_OUTPUT = Path("trades/pelosi_trades.json")
CURRENT_DISCLOSURE = None

# Time interval in seconds
CHECK_INTERVAL = 30  # Default is 1 hour

def download_file(url, output_folder) -> bool:
    
    global CURRENT_DISCLOSURE
    
    try:
        response = requests.head(url)
        response.raise_for_status()
        last_modified = response.headers.get("Last-Modified")

        if not last_modified:
            print("Last-Modified header not found. Aborting download.")
            return False
        
        if CURRENT_DISCLOSURE:
            most_recent_timestamp = datetime.strptime(CURRENT_DISCLOSURE.stem, "%a_%d_%b_%Y_%H-%M-%S_GMT")
            last_modified_timestamp = datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S GMT")
            
            if most_recent_timestamp == last_modified_timestamp:
                print("File hasn't been updated. Skipping download.")
                return  False

        print('test')
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
                    CURRENT_DISCLOSURE = new_name
                    print(f"Renamed text file to: {new_name}")
                elif file.suffix == ".xml":
                    file.unlink()
                    print(f"Deleted XML file: {file}")

            zip_path.unlink()
            print(f"ZIP file removed: {zip_path}")
            return True 

    except Exception as e:
        print(f"Error downloading or processing file: {e}")

def get_most_recent_file_by_name(directory):
    try:
        files = list(directory.glob("*.txt"))  # Filter for text files only
        if not files:
            print("No files found in the directory.")
            return None

        # Extract the timestamp from file names and sort
        most_recent_file = max(
            files, key=lambda f: datetime.strptime(f.stem, "%a_%d_%b_%Y_%H-%M-%S_GMT")
        )
        print(f"Most recent file by name: {most_recent_file}")
        return most_recent_file
    except Exception as e:
        print(f"Error finding most recent file by name: {e}")
        return None

def parse_text_file(file_path):
    pelosi_trades = {}
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                fields = [field.strip() for field in line.split('\t')]
                if fields[1] == "Pelosi":
                    pelosi_trades[fields[-1]] = fields[-2]  # doc_id, trade_date 
        return pelosi_trades
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return {}
    except Exception as e:
        print(f"Error reading file: {e}")
        return {}

def save_to_json(data, file_path, last_modified):
    """Save a dictionary to a JSON file with last modified timestamp."""
    try:
        output_data = {
            "last_modified": last_modified,
            "data": data
        }
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(output_data, json_file, indent=4)
        print(f"Data successfully saved to {file_path}")
    except Exception as e:
        print(f"Error saving data to JSON: {e}")

def load_from_json(file_path):
    try:
        if not file_path.exists():
            print(f"JSON file does not exist: {file_path}")
            return {}

        with open(file_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            print(f"Data successfully loaded from {file_path}")
            return data
    except Exception as e:
        print(f"Error loading data from JSON: {e}")
        return {}

if __name__ == "__main__":

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    # check for existing file in case of restart
    if any(OUTPUT_FOLDER.glob("*.txt")):
        CURRENT_DISCLOSURE = Path(get_most_recent_file_by_name(OUTPUT_FOLDER))
    
    pdf_handler = PDFHandler('trades')
    pdf_handler.extract_trade_data(Path('trades/20024542.pdf'))

    while True:
        try:
            if download_file(DOWNLOAD_URL, OUTPUT_FOLDER):
                CURRENT_DISCLOSURE = Path(get_most_recent_file_by_name(OUTPUT_FOLDER))
                holdings = parse_text_file(CURRENT_DISCLOSURE)

                # save to json 
                last_modified_header = requests.head(DOWNLOAD_URL).headers.get("Last-Modified")
                save_to_json(holdings, JSON_OUTPUT, last_modified_header)

                # scrape web for information regarding trade ids 
                pdf_handler = PDFHandler('trades')

                # iteraste through document ids 
                for k,v in holdings.items():
                    print("processing trade id: ", k)
                    pdf_handler.download_pdf(k)
                
                pdf_handler.print_pdf_line_by_line(Path('trades/20024542.pdf'))

        except Exception as e:
            print(f"Error processing disclosure file: {e}")


        print(f"Waiting for {CHECK_INTERVAL} seconds before checking again...")
        time.sleep(CHECK_INTERVAL)
