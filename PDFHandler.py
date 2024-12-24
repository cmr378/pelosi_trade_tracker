import requests
import os
from pathlib import Path
import pdfplumber
import re

class PDFHandler:
    def __init__(self, output_folder):
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.pdf_files = [] 

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
            self.pdf_files.append(pdf_path)
            return pdf_path

        except Exception as e:
            print(f"Error downloading PDF for trade ID {trade_id}: {e}")
            return None
        
    
    def clean_text(self, text) -> str:
        return text.translate({0: None})  # Remove null bytes (ASCII 0)

    def parse_pdf_text(self, text) -> dict:

        # Extract top-level info (Filing ID, Name, State/District)
        filing_id_match = re.search(r'Filing ID #(\d+)', text)
        name_match = re.search(r'Name:\s*(.+)', text)
        district_match = re.search(r'State/District:\s*(.+)', text)

        filing_id = filing_id_match.group(1).strip() if filing_id_match else None
        name = name_match.group(1).strip() if name_match else None
        state_district = district_match.group(1).strip() if district_match else None

        # Update the transaction block regex to be more flexible
        transaction_blocks = re.findall(r'SP\s+(.+?)\n(?=SP\s+|\* For the complete|I CERTIFY|$)', text, flags=re.DOTALL)

        transactions = []

        for block in transaction_blocks:
            # Update the first line pattern to handle more variations
            first_line_match = re.search(
                r'^(.*?)\((.*?)\)(?:\s+\[(?:OP|ST)\])?\s+([PS])(?:\s+\(partial\))?\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+\$([\d,]+)\s*-\s*\$([\d,]+)',
                block,
                flags=re.MULTILINE
            )
            if not first_line_match:
                continue

            company_name = first_line_match.group(1).strip()
            ticker = first_line_match.group(2).strip()
            transaction_code = first_line_match.group(3).strip()
            transaction_date = first_line_match.group(4).strip()
            notification_date = first_line_match.group(5).strip()
            amount_min = first_line_match.group(6).strip()
            amount_max = first_line_match.group(7).strip()
            amount_range = f"${amount_min} - ${amount_max}"

            # B) Extract amount range from the remainder.
            #    Typically we see something like "$500,001 - [OP] $1,000,000".
            #    Let's do a broad pattern that captures ranges like "$500,001 - $1,000,000" or "$100,001 - $250,000".
            #    In your example, there's a bracket "[OP]" in the middle, so we'll just remove that if it exists.
            remainder_line = amount_range.replace('[OP]', '').strip()
            # Now parse the range. Something like "$500,001 - $1,000,000"
            amount_range_match = re.search(r'\$[\d,]+(?:\s*-\s*\$[\d,]+)', remainder_line)
            if amount_range_match:
                amount_range = amount_range_match.group(0).strip()
            else:
                # fallback if not found
                amount_range = remainder_line

            # C) Now parse the detail line that begins with "D: "
            #    Example:
            #     D: Purchased 50 call options with a strike price of $200 and an expiration date of 1/17/25.
            detail_line_match = re.search(r'D:\s*(.*)', block)
            if detail_line_match:
                detail_text = detail_line_match.group(1).strip()
            else:
                detail_text = ""

            # From detail_text, let's extract:
            #   - purchase vs. sale
            #   - number of contracts or shares
            #   - call/put or shares
            #   - strike price (if call/put)
            #   - expiration date (if call/put)
            #
            # Example detail: "Purchased 50 call options with a strike price of $200 and an expiration date of 1/17/25."
            # We'll do a few simple patterns to parse.

            # Purchase vs. Sale
            if "Purchased" in detail_text:
                transaction_type_full = "Purchase"
            elif "Sold" in detail_text:
                transaction_type_full = "Sale"
            else:
                transaction_type_full = "Unknown"

            # Number of contracts or shares
            # For call/put we often see "Purchased 50 call options ...".
            num_contracts_match = re.search(r'(\d+)\s+(?:call|put|share)', detail_text, flags=re.IGNORECASE)
            if num_contracts_match:
                number_of_contracts = int(num_contracts_match.group(1))
            else:
                number_of_contracts = None

            # Check if it's a call option, put option, or shares
            if re.search(r'call option', detail_text, flags=re.IGNORECASE):
                security_type = "Call Option"
            elif re.search(r'put option', detail_text, flags=re.IGNORECASE):
                security_type = "Put Option"
            elif re.search(r'share', detail_text, flags=re.IGNORECASE):
                security_type = "Stock"
            else:
                # fallback
                security_type = "Unknown"

            # Strike price
            strike_match = re.search(r'strike price of \$([\d\.]+)', detail_text, flags=re.IGNORECASE)
            if strike_match:
                strike_price = float(strike_match.group(1))
            else:
                strike_price = None

            # Expiration date
            expiration_match = re.search(r'expiration date of (\d{1,2}/\d{1,2}/\d{2,4})', detail_text, flags=re.IGNORECASE)
            if expiration_match:
                expiration_date = expiration_match.group(1)
            else:
                expiration_date = None

            # Collect everything into a transaction dictionary
            transaction_info = {
                "company": company_name.strip(",."),
                "ticker": ticker,
                "transaction_code": transaction_code,       # 'P' or 'S'
                "transaction_type": transaction_type_full,  # "Purchase" or "Sale"
                "security_type": security_type,             # "Call Option", "Put Option", "Stock", etc.
                "number_of_contracts": number_of_contracts,
                "strike_price": strike_price,
                "expiration_date": expiration_date,
                "transaction_date": transaction_date,
                "notification_date": notification_date,
                "amount_range": amount_range,
            }
            
            print(transaction_info)

            transactions.append(transaction_info)

        result = {
            "filing_id": filing_id,
            "name": name,
            "state_district": state_district,
            "transactions": transactions
        }

        return result

    
    def extract_trade_data(self, pdf_path) -> dict:
        
        trades = {}
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_number, page in enumerate(pdf.pages, start=1):
                    text = self.clean_text(page.extract_text())
                    print(text)    
                    parsed_data = self.parse_pdf_text(text)
        except Exception as e:
            print(f"Error extracting data from PDF {pdf_path}: {e}")
            return None

    def process_all_pdfs(self):
        all_trades = []
        for pdf_file in self.pdf_files:
            trades = self.extract_trade_data(pdf_file)
            if trades:
                all_trades.extend(trades)
        return all_trades