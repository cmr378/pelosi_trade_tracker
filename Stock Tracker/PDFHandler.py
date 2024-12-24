import requests
import os
from pathlib import Path
import pdfplumber
import re
import json

class PDFHandler:
    """
    Handles downloading of PDFs, parsing their contents, and extracting transaction data.
    """
    def __init__(self, output_folder):
        """
        Initializes the PDFHandler with an output folder and a list to store PDF file paths.
        """
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.pdf_files = []

    def download_pdf(self, trade_id):
        """
        Downloads the PDF for a given trade ID and saves it in the output folder.
        Returns the path to the downloaded PDF or None if an error occurs.
        """
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
        """
        Removes null bytes from the given text.
        """
        if text is None:
            return ""
        # Remove null characters (\u0000) by translating ASCII 0 to None
        return text.translate({0: None})

    def get_lines_from_pdf(pdf_path):
        """
        Extracts text from the first page of the given PDF and returns it as a list of lines.
        """
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()
        if not text:
            return []
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        return lines

    def parse_line1(self, line):
        """
        Parses the first line of a 4-line transaction block from the PDF text 
        and returns relevant data as a dictionary.
        """
        pattern_line1 = re.compile(
            r"^SP\s+(.*?)\((.*?)\)\s+([PS].*?)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+\$(.*?)\s*-\s*$"
        )
        match = pattern_line1.match(line)
        if match:
            company_name = match.group(1).strip()
            ticker = match.group(2).strip()
            trans_type = match.group(3).strip()
            trans_date = match.group(4).strip()
            notif_date = match.group(5).strip()
            amount_min = match.group(6).strip()
            return {
                "company_name": company_name,
                "ticker": ticker,
                "transaction_type": trans_type,
                "transaction_date": trans_date,
                "notification_date": notif_date,
                "amount_min": amount_min
            }
        return {}

    def parse_line2(self, line):
        """
        Parses the second line of a 4-line transaction block from the PDF text 
        and returns any bracket code and maximum amount as a dictionary.
        """
        pattern_line2 = re.compile(r"\[(.*?)\]\s*\$(\d[\d,]*)")
        match = pattern_line2.search(line)
        if match:
            bracket_code = match.group(1).strip()
            amount_max = match.group(2).strip()
            return {
                "bracket_code": bracket_code,
                "amount_max": amount_max
            }
        return {}

    def parse_line4(self, line):
        """
        Parses the fourth line of a 4-line transaction block from the PDF text 
        to extract a description.
        """
        pattern_line4 = re.compile(r"(?:D:|Description:)\s*(.*)", re.IGNORECASE)
        match = pattern_line4.search(line)
        if match:
            return match.group(1).strip()
        return ""

    def parse_4line_block(self, line1, line2, line3, line4):
        """
        Combines data from four lines into a single transaction record,
        including company info, transaction type, dates, amounts, and description.

        This method now uses 'clean_text' to remove any null bytes from line3 and line4.
        """
        # Clean line3 and line4 before storing them
        line3_cleaned = self.clean_text(line3)
        line4_cleaned = self.clean_text(line4)

        d = {
            "company_name": "",
            "ticker": "",
            "transaction_type": "",
            "transaction_date": "",
            "notification_date": "",
            "amount_min": "",
            "amount_max": "",
            "bracket_code": "",
            "description": "",
            "buy_or_sell": "",
            "line1_raw": line1,
            "line2_raw": line2,
            "line3_raw": line3_cleaned,  # Store the cleaned version
            "line4_raw": line4_cleaned   # Store the cleaned version
        }

        line1_data = self.parse_line1(line1)
        d.update(line1_data)

        line2_data = self.parse_line2(line2)
        d.update(line2_data)

        desc = self.parse_line4(line4_cleaned)
        d["description"] = desc

        trans_type_lower = d["transaction_type"].lower()
        desc_lower = desc.lower()

        if "s" in trans_type_lower:
            d["buy_or_sell"] = "Sell"
        elif "p" in trans_type_lower:
            d["buy_or_sell"] = "Buy"
        else:
            if "sold" in desc_lower:
                d["buy_or_sell"] = "Sell"
            elif "purchas" in desc_lower:
                d["buy_or_sell"] = "Buy"
            else:
                d["buy_or_sell"] = "Unknown"

        return d

    def get_lines_from_pdf(self, pdf_path):
        """
        Extracts text from the first page of the given PDF and returns it as a list of lines.
        """
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()
        if not text:
            return []
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        return lines

    def get_transactions(self, pdf_path) -> list[dict]:
        """
        Iterates through lines from the PDF, recognizes 4-line blocks that start with 'SP',
        and parses them into transaction records.
        """
        lines = self.get_lines_from_pdf(pdf_path)
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

    def extract_trade_data(self, pdf_path) -> list:
        """
        Retrieves all parsed transactions from a single PDF
        and prints each transaction's details.
        Returns the list of transactions so it can be used or saved.
        """
        transactions = self.get_transactions(pdf_path)
        for idx, tx in enumerate(transactions, 1):
            print(f"Transaction {idx}:")
            for k, v in tx.items():
                print(f"  {k}: {v}")
            print()
        return transactions

    def process_all_pdfs(self):
        """
        Processes every PDF stored in pdf_files, extracting and returning 
        all transaction data from all PDFs as a combined list. 
        Also writes the combined transaction list to a JSON file.
        """
        all_trades = []
        for pdf_file in self.pdf_files:
            trades = self.extract_trade_data(pdf_file)
            if trades:
                all_trades.extend(trades)
        
        return all_trades
