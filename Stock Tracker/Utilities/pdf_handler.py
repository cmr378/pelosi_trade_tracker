import requests
from io import BytesIO
from pathlib import Path
import pdfplumber
import re
import json
from config.config import SAVE_FILES

class PDFHandler:
    """
    Handles downloading of PDFs, parsing their contents, and extracting transaction data.
    """
    def __init__(self, output_folder):
        """
        Initializes the PDFHandler with an output folder and a list to store PDF data or file paths.
        """
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.pdf_data = []  # Store PDF data in memory

    def download_pdf(self, trade_id):
        """
        Downloads the PDF for a given trade ID.
        If SAVE_FILES is True, saves it to the output folder.
        Otherwise, processes it in memory.
        Returns the BytesIO object or the path to the saved PDF.
        """
        pdf_url = f"https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2024/{trade_id}.pdf"
        pdf_path = self.output_folder / f"{trade_id}.pdf"

        try:
            response = requests.get(pdf_url, stream=True)
            response.raise_for_status()
            pdf_data = BytesIO(response.content)
            print(f"PDF downloaded successfully for trade ID: {trade_id}")

            if SAVE_FILES:
                with open(pdf_path, "wb") as pdf_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        pdf_file.write(chunk)
                print(f"PDF saved to disk: {pdf_path}")
                self.pdf_data.append(pdf_path)
                return pdf_path
            else:
                self.pdf_data.append(pdf_data)
                return pdf_data
        except Exception as e:
            print(f"Error downloading PDF for trade ID {trade_id}: {e}")
            return None

    def clean_text(self, text: str) -> str:
        """
        Removes null bytes from the given text.
        """
        if text is None:
            return ""
        # Remove null characters (\u0000) by translating ASCII 0 to None
        return text.translate({0: None})

    def get_lines_from_pdf(self, pdf_source):
        """
        Extracts text from the first page of the given PDF and returns it as a list of lines.
        Accepts either a BytesIO object (in-memory) or a file path.
        """
        with pdfplumber.open(pdf_source) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()
        if not text:
            return []
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        return lines

    def parse_4line_block(self, line1: str, line2: str, line3: str, line4: str) -> dict:
        """
        Extracts key information:
        1. Ticker symbol (or company name if ticker not found)
        2. Buy/Sell indicator
        3. Whether it's shares or options (including expiration date for options)
        """
        # Find ticker from either line1 or line2
        ticker = ""
        ticker_match = re.search(r'\(([A-Z]+)\)', line1 + line2)
        if ticker_match:
            ticker = ticker_match.group(1)
        else:
            # If no ticker found, extract company name from line1
            company_match = re.match(r'^SP\s+(.*?)(?:\d{2}/\d{2}/\d{4}|$)', line1)
            if company_match:
                ticker = company_match.group(1).strip()

        # Determine if Buy or Sell from line1
        buy_or_sell = "Unknown"
        if 'S' in line1.split()[2:]:  # Skip the "SP" at start
            buy_or_sell = "Sell"
        elif 'P' in line1.split()[2:]:
            buy_or_sell = "Buy"

        # Check if options or shares and get expiration date if it's an option
        transaction_type = "shares"
        expiration_date = None
        
        if any(word in line4.lower() for word in ['call', 'option', 'strike']):
            transaction_type = "options"
            # Try multiple date patterns and print debug info
            print(f"Found options trade, line4: {line4}")  # Debug print
            
            date_patterns = [
                r'(?:exp|expiration|expires?)?\s*(\d{2}/\d{2}/\d{4})',  # MM/DD/YYYY
                r'(?:exp|expiration|expires?)?\s*(\d{1,2}/\d{1,2}/\d{2,4})',  # M/D/YY or M/D/YYYY
                r'(\d{1,2}/\d{1,2}/\d{2,4})',  # Any date format
                r'(?:exp|expiration|expires?)?\s*(\w+ \d{1,2},? \d{4})'  # January 15, 2024
            ]
            
            for pattern in date_patterns:
                exp_match = re.search(pattern, line4)
                if exp_match:
                    expiration_date = exp_match.group(1)
                    print(f"Found expiration date: {expiration_date}")  # Debug print
                    break

        result = {
            "ticker": ticker,
            "buy_or_sell": buy_or_sell,
            "transaction_type": transaction_type
        }

        # Only add expiration_date if it's an option and we found a date
        if transaction_type == "options" and expiration_date:
            print("Expiration date found:", expiration_date)
            result["expiration_date"] = expiration_date

        return result

    def get_transactions(self, pdf_source) -> list[dict]:
        """
        Iterates through lines from the PDF, recognizes 4-line blocks that start with 'SP',
        and parses them into transaction records.
        Accepts either a BytesIO object (in-memory) or a file path.
        """
        lines = self.get_lines_from_pdf(pdf_source)
        transactions = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("SP "):
                if i + 3 < len(lines):
                    line1 = lines[i]
                    line2 = lines[i+1]
                    line3 = lines[i+2]
                    line4 = lines[i+3]
                    parsed = self.parse_4line_block(line1, line2, line3, line4)
                    transactions.append(parsed)
                    i += 4
                    continue
                else:
                    break
            i += 1
        return transactions

    def extract_trade_data(self, pdf_source) -> list[dict]:
        """
        Retrieves all parsed transactions from a single PDF source.
        Accepts either a BytesIO object (in-memory) or a file path.
        Returns the list of transactions.
        """
        transactions = self.get_transactions(pdf_source)
        for idx, tx in enumerate(transactions, 1):
            print(f"Transaction {idx}:")
            for k, v in tx.items():
                print(f"  {k}: {v}")
            print()
        return transactions

    def process_all_pdfs(self) -> list[dict]:
        """
        Processes every PDF stored in pdf_data, extracting and returning 
        all transaction data as a combined list. 
        """
        all_trades = []
        for pdf_source in self.pdf_data:
            trades = self.extract_trade_data(pdf_source)
            if trades:
                all_trades.extend(trades)
        return all_trades
