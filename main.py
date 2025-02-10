from src.config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD
from src.linkedinAutomation import login, search, filter_recruiters, goto_next_page
from src.html_parser import HTMLProcessor
from src.pdf_parser import PDFProcessor
from src.excelhandler import save_recruiter_data, generate_emails
import os
import time
import json
from playwright.sync_api import sync_playwright


def cleanup_files(html_path, pdf_path):
    """Remove processed HTML and PDF files"""
    try:
        if html_path and os.path.exists(html_path):
            os.remove(html_path)
            print(f"Removed HTML file: {html_path}")

        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)
            print(f"Removed PDF file: {pdf_path}")

    except Exception as e:
        print(f"Error cleaning up files: {e}")


def load_company_data():
    """Load company email format data"""
    try:
        with open('companies.txt') as f:
            return json.loads(f.read())
    except Exception as e:
        print(f"Error loading company data: {e}")
        return None


def export_page_content(page, role_name, page_num):
    """Export current page content in both HTML and PDF formats"""
    try:
        print(f"Exporting page {page_num} content for {role_name}...")
        output_dir = "./data/temp"  # Changed to temp directory
        os.makedirs(output_dir, exist_ok=True)

        # Export HTML
        html_path = f"{output_dir}/raw_{role_name.replace(' ', '_')}_page_{page_num}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page.content())

        # Export PDF
        pdf_path = f"{output_dir}/raw_{role_name.replace(' ', '_')}_page_{page_num}.pdf"
        page.pdf(path=pdf_path)

        return html_path, pdf_path

    except Exception as e:
        print(f"Error exporting page content: {e}")
        return None, None


def process_recruiters(html_path, pdf_path):
    """Process both HTML and PDF files to extract recruiter information"""
    html_processor = HTMLProcessor()
    pdf_processor = PDFProcessor()

    html_results = html_processor.process_file(html_path)
    pdf_results = pdf_processor.process_file(pdf_path)

    # Combine and deduplicate results
    all_recruiters = {}

    # Process HTML results first
    for recruiter in html_results:
        name = recruiter['name']
        if name != "LinkedIn Member":
            all_recruiters[name] = recruiter

    # Add/update with PDF results
    for recruiter in pdf_results:
        name = recruiter['name']
        if name != "LinkedIn Member":
            if name in all_recruiters:
                # If PDF has title and HTML doesn't, use PDF's title
                if not all_recruiters[name]['title'] and recruiter['title']:
                    all_recruiters[name]['title'] = recruiter['title']
            else:
                all_recruiters[name] = recruiter

    return list(all_recruiters.values())


def main():
    # Load company data
    company_dict = load_company_data()
    if not company_dict:
        return

    company = "Zoox"
    roles = [
        {"role": "technical recruiter", "search_text": f"{company} technical recruiter"},
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Create temp directory for intermediate files
        os.makedirs("./data/temp", exist_ok=True)

        # Login
        page.goto('https://linkedin.com/login')
        time.sleep(2)
        login(page)

        all_recruiters = []  # Store all recruiters across pages

        for role in roles:
            search_text = role["search_text"]
            role_name = role["role"]

            search(page, search_text)
            filter_recruiters(page, company)
            time.sleep(5)

            page_num = 1
            while True:
                print(f"\nProcessing page {page_num}...")

                # Export page content
                html_path, pdf_path = export_page_content(page, role_name, page_num)
                if not html_path or not pdf_path:
                    break

                # Process files
                page_recruiters = process_recruiters(html_path, pdf_path)
                print(f"Found {len(page_recruiters)} recruiters on page {page_num}")

                # Add to overall list
                all_recruiters.extend(page_recruiters)

                # Clean up temp files
                cleanup_files(html_path, pdf_path)

                # Try to go to next page
                if not goto_next_page(page):
                    print("No more pages available")
                    break

                page_num += 1
                time.sleep(3)  # Wait between pages

        # Save all recruiters to company file
        if all_recruiters:
            if save_recruiter_data(all_recruiters, company):
                # Generate emails right after saving data
                generate_emails(company)

        browser.close()

        # Clean up temp directory
        try:
            os.rmdir("./data/temp")
            print("Removed temp directory")
        except:
            print("Note: Temp directory not empty or already removed")


if __name__ == "__main__":
    main()