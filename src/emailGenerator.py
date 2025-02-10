# src/emailGenerator.py
import json
import re
from pathlib import Path

class EmailGenerator:
    def __init__(self):
        # Load company formats
        self.root_dir = Path(__file__).parent.parent
        company_file = self.root_dir / 'companies.txt'
        with open(company_file, 'r') as f:
            self.company_formats = json.load(f)

    # In emailGenerator.py
    # In emailGenerator.py
    def clean_name(self, name: str) -> str:
        """Remove LinkedIn status phrases, commas and special characters but preserve necessary spaces"""
        # List of phrases to remove
        remove_phrases = [
            " is hiring",
            " is looking",
            " is seeking",
            " is recruiting",
            " is actively hiring",
            " is actively",
            " is open"
        ]

        # First remove LinkedIn status phrases
        for phrase in remove_phrases:
            name = name.replace(phrase, "")

        # Split by comma and take first part
        name = name.split(',')[0]

        # Replace special characters with space and clean up extra spaces
        name = re.sub(r'[^a-zA-Z\s]', ' ', name)  # Keep spaces
        name = ' '.join(name.split())  # Clean up multiple spaces
        return name.lower()

    def generate_email(self, first_name: str, last_name: str, company: str) -> str:
        """Generate email based on company format"""
        try:
            format_type, domain = self.company_formats.get(company, [None, None])
            if not format_type or not domain:
                return ""

            first_name = first_name.lower().strip()
            last_name = last_name.lower().strip()
            first_initial = first_name[0] if first_name else ""

            if format_type == 1:
                return f"{first_initial}{last_name}{domain}"
            elif format_type == 2:
                return f"{first_name}{last_name}{domain}"
            elif format_type == 3:
                return f"{first_name}.{last_name}{domain}"
            elif format_type == 4:
                return f"{first_name}{domain}"
            elif format_type == 5:
                return f"{first_initial}.{last_name}{domain}"
            elif format_type == 6:
                return f"{first_name}_{last_name}{domain}"
            return ""

        except Exception as e:
            print(f"Error generating email for {first_name} {last_name}: {e}")
            return ""