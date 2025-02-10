import os
import pdfplumber
from typing import List, Dict

class PDFProcessor:
    def __init__(self):
        self.separator = '• '

    def process_file(self, pdf_path: str) -> List[Dict[str, str]]:
        """Process PDF file and extract recruiter information"""
        try:
            recruiters = []
            if not os.path.exists(pdf_path):
                print(f"PDF file not found: {pdf_path}")
                return recruiters

            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_recruiters = self._process_page(page, page_num)
                    recruiters.extend(page_recruiters)

            print(f"Found {len(recruiters)} recruiters in PDF")
            return recruiters

        except Exception as e:
            print(f"Error processing PDF file: {e}")
            return []

    def _process_page(self, page, page_num: int) -> List[Dict[str, str]]:
        """Process a single PDF page"""
        recruiters = []
        try:
            text = page.extract_text()
            print(f"Processing PDF page {page_num + 1}")

            lines = text.split('\n')
            for line in lines:
                recruiter = self._process_line(line)
                if recruiter:
                    recruiters.append(recruiter)

        except Exception as e:
            print(f"Error processing PDF page {page_num + 1}: {e}")

        return recruiters

    def _process_line(self, line: str) -> Dict[str, str]:
        """Process a single line from the PDF"""
        try:
            if self.separator in line:
                parts = line.split(self.separator)
                if len(parts) >= 2:
                    name = parts[0].strip()
                    title = parts[1].strip()

                    if name and name != "LinkedIn Member":
                        print(f"Found in PDF: {name} - {title}")
                        return {
                            'name': name,
                            'title': title
                        }

        except Exception as e:
            print(f"Error processing line: {e}")

        return None