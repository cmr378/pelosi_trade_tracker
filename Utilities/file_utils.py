from config.config import (
     STOCK_OUTPUT_FOLDER,
     CRYPTO_OUTPUT_FOLDER
)

from datetime import datetime
from pathlib import Path

class FileUtils:

    @staticmethod
    def initialize_output_folder():
        STOCK_OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        print("----------------------------------------------------")
        print(f"Output folder initialized")
    
    @staticmethod
    def initialize_crypto_output_folder():
        CRYPTO_OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        print("----------------------------------------------------")
        print(f"Output folder initialized")
    
   
