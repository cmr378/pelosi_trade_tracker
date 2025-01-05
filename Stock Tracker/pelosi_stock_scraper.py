from io import BytesIO
import os
import requests
from pathlib import Path
import zipfile
from datetime import datetime
import time
import json
from utilities.pdf_handler import PDFHandler
from utilities.robinhood_handler import RobinhoodHandler

from config.config import (
    DOWNLOAD_URL,
    OUTPUT_FOLDER,
    JSON_OUTPUT,
    PDF_OUTPUT,
    SAVE_FILES
)   

# Time interval in seconds
CHECK_INTERVAL = 3600  # Default is 1 hour

CURRENT_DISCLOSURE = None

def download_file(url: str, output_folder: Path) -> bool:
    """
    Downloads and processes the file from the given URL in memory.
    Optionally saves the text file to disk at the end.
    Returns True if successful, False otherwise.
    """
    global CURRENT_DISCLOSURE

    try:
        # Make a HEAD request to get the Last-Modified header
        response = requests.head(url)
        response.raise_for_status()
        last_modified = response.headers.get("Last-Modified")

        if not last_modified:
            print("Last-Modified header not found. Aborting download.")
            return False

        new_file_name = last_modified.replace(",", "").replace(" ", "_").replace(":", "-") + ".txt"
        print(f"Using new_file_name with last_modified as file name: {new_file_name}")

        # Download the ZIP file into memory
        response = requests.get(url, stream=True)
        response.raise_for_status()
        zip_data = BytesIO(response.content)
        print("ZIP file downloaded successfully into memory.")

        # Check if the file is a valid ZIP and extract its contents
        if zipfile.is_zipfile(zip_data):
            with zipfile.ZipFile(zip_data, 'r') as zip_ref:
                # Iterate through files in the ZIP
                for file_name in zip_ref.namelist():
                    with zip_ref.open(file_name) as file:
                        if file_name.endswith(".txt"):
                            # Process the text file in memory
                            CURRENT_DISCLOSURE = file.read().decode('utf-8')
                            if SAVE_FILES:
                                file_path = output_folder / new_file_name
                                with open(file_path, "w", encoding="utf-8") as f:
                                    f.write(CURRENT_DISCLOSURE)
                                print(f"Text file saved to disk: {file_path}")

                        elif file_name.endswith(".xml"):
                            print(f"Ignored and skipped XML file: {file_name}")
            return True

        else:
            print("The downloaded file is not a valid ZIP file.")
            return False

    except Exception as e:
        print(f"Error downloading or processing file: {e}")
        return False

def get_most_recent_file_by_name(directory: Path) -> Path:
    """
    Finds the most recent file in the specified directory based on its name.
    Assumes file names contain timestamps in a specific format.
    Returns the most recent file or None if no files are found.
    """
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

def parse_text_content(text_content: str) -> dict:
    """
    Parses the text content to extract transaction information related to Pelosi.
    Returns a dictionary with document IDs as keys and trade dates as values.
    """
    disclosure_content = {}
    try:
        for line in text_content.splitlines():
            fields = [field.strip() for field in line.split('\t')]
            if len(fields) > 1 and fields[1] == "Pelosi":
                disclosure_content[fields[-1]] = fields[-2]  # doc_id, trade_date 
        return disclosure_content
    except Exception as e:
        print(f"Error parsing text content: {e}")
        return {}

def save_to_json(data: dict, file_path: Path, last_modified: str) -> None:
    """
    Save a dictionary to a JSON file with a last-modified timestamp.
    """
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

def load_from_json(folder_path: Path) -> list[dict]:
    """
    Load a list of dictionaries from the most recently added JSON file in a folder.
    Returns an empty list if the folder does not contain any JSON files or an error occurs.
    Excludes the 'last_modified' field from the output.
    """
    try:
        if not folder_path.is_dir():
            print(f"The specified path is not a folder: {folder_path}")
            return []

        # Get all JSON files in the folder
        files = list(folder_path.glob("*.json"))

        if not files:
            print(f"No JSON files found in the folder: {folder_path}")
            return []

        # Find the most recently added file based on modification time
        most_recent_file = max(files, key=lambda f: f.stat().st_mtime)

        # Load the JSON data from the most recent file
        with open(most_recent_file, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            print(f"Data successfully loaded from {most_recent_file}")

            # Return only the 'data' field
            return data.get("data", [])

    except Exception as e:
        print(f"Error loading data from JSON: {e}")
        return []
    
def compare_lists(list1, list2):
    """
    Compare two lists of dictionaries and return the differences.
    - Identifies items only in list1.
    - Identifies items only in list2.

    Returns a dictionary with keys:
    - 'only_in_list1'
    - 'only_in_list2'
    """
    # Convert dictionaries to sorted tuples for comparison (to handle unhashable types)
    set1 = {tuple(sorted(d.items())) for d in list1}
    set2 = {tuple(sorted(d.items())) for d in list2}

    # Find unique items in both lists
    differences = set1.symmetric_difference(set2)

    # Convert the tuples back to dictionaries
    return [dict(t) for t in differences]


if __name__ == "__main__":
    """
    Main execution loop for processing disclosures and transactions.
    Periodically checks for updates and processes new data.
    """
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    PDF_OUTPUT.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.mkdir(parents=True, exist_ok=True)
        
    while True:
        try:
            if download_file(DOWNLOAD_URL, OUTPUT_FOLDER):

                # check for existing json file 
                if os.path.exists(JSON_OUTPUT) and os.path.isdir(JSON_OUTPUT):
                    if os.listdir(JSON_OUTPUT):
                         previous_transaction_data = load_from_json(JSON_OUTPUT)
                         print("Previous data loaded")

                pelosi_transactions = parse_text_content(CURRENT_DISCLOSURE)
                # Scrape web for information regarding transaction IDs 
                pdf_handler = PDFHandler(PDF_OUTPUT)

                # Iterate through document IDs and download transaction reports 
                for k, v in pelosi_transactions.items():
                    print("Processing trade ID: ", k)
                    pdf_handler.download_pdf(k) 
                
                transactions_data = pdf_handler.process_all_pdfs()
                
                # Save to JSON 
                last_modified_header = requests.head(DOWNLOAD_URL).headers.get("Last-Modified")
                formatted_date = last_modified_header.replace(" ", "_").replace(":", "-")
                json_filename = JSON_OUTPUT / f"{formatted_date}.json"
                save_to_json(transactions_data, json_filename, last_modified_header)
                
                unique_tickers = {transaction['ticker'] for transaction in transactions_data}

                # Check for any new transactions 
                new_transactions = compare_lists(previous_transaction_data,  transactions_data)
                if len(new_transactions) > 0: 
                    print("New transactions", new_transactions)
                    # Handles all logic related to Robinhood data/transactions 
                    robinhood_handler = RobinhoodHandler() 
                    robinhood_handler.purchase_stock_shares()
                else:
                    print("No new transaction from Nancy Pelosi")

        except Exception as e:
            print(f"Error processing disclosure file: {e}")

        print(f"Waiting for {CHECK_INTERVAL} seconds before checking again...")
        time.sleep(CHECK_INTERVAL)
5