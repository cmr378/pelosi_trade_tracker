import requests
import os
from pathlib import Path
import pdfplumber
import re

class PDFHandler:
    def __init__(self, output_folder):
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def download_pdf(self, trade_id):
        pdf_url = f"https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2024/{trade_id}.pdf"
        pdf_path = self.output_folder / f"{trade_id}.pdf"
        
        try:
            response = requests.get(pdf_url, stream=True)
            response.raise_for_status()

            with open(pdf_path, "wb") as pdf_file:
                for chunk in response.iter_content(chunk_size=8192):
                    pdf_file.write(chunk)

            print(f"PDF downloaded successfully: {pdf_path}")
            return pdf_path

        except Exception as e:
            print(f"Error downloading PDF for trade ID {trade_id}: {e}")
            return None
    
    def extract_trade_data(self, pdf_path):
        """Extract relevant trade data from a PDF."""
        trades = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_number, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    lines = text.split('\n')
                    for line in lines:
                        match = re.search(r"(?:[A-Z]+\s+.*\((\w+)\))\s+(P|S)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+\$([\d,]+)", line)
                        if match:
                            ticker = match.group(1)  # Stock ticker
                            transaction_type = "Purchase" if match.group(2) == "P" else "Sale"
                            transaction_date = match.group(3)  # Transaction date
                            notification_date = match.group(4)  # Notification date
                            amount = match.group(5)  # Transaction amount

                            # Look for description details in subsequent lines
                            description_match = re.search(r"Purchased (\d+) call options with a strike price of \$(\d+(?:\.\d+)?)", text)
                            call_options = None
                            strike_price = None
                            shares_purchased = None

                            if description_match:
                                call_options = int(description_match.group(1))
                                strike_price = float(description_match.group(2))
                            else:
                                # Check for stock shares purchase description
                                shares_match = re.search(r"Purchased (\d+) shares", text)
                                if shares_match:
                                    shares_purchased = int(shares_match.group(1))

                            trades.append({
                                "ticker": ticker,
                                "transaction_type": transaction_type,
                                "transaction_date": transaction_date,
                                "notification_date": notification_date,
                                "amount": amount,
                                "call_options": call_options,
                                "strike_price": strike_price,
                                "shares_purchased": shares_purchased
                            })
            print(f"Extracted trades: {trades}")
            return trades
        except Exception as e:
            print(f"Error extracting data from PDF {pdf_path}: {e}")
            return None


    def parse_pdf(self, pdf_path):
        """Extract data from a PDF."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text()
            print(f"Extracted text from {pdf_path}")
            return text

        except Exception as e:
            print(f"Error parsing PDF {pdf_path}: {e}")
            return None
