from config.config import (
     OUTPUT_FOLDER,
     CRYPTO_OUTPUT_FOLDER
)

from datetime import datetime
from pathlib import Path

class FileUtils:

    @staticmethod
    def initialize_output_folder():
        OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        print(f"Output folder initialized")
    
    @staticmethod
    def initialize_crypto_output_folder():
        CRYPTO_OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        print(f"Output folder initialized")
    
   
