from src.linkedinAutomation import login, search, filter_recruiters, goto_next_page
from src.html_parser import HTMLProcessor
from src.pdf_parser import PDFProcessor
from src.excelhandler import save_recruiter_data, generate_emails
from src.emailDraftManager import generate_company_drafts
from src.emailSender import GmailSender
import pandas as pd
import os
import time
import json
import sys
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


def scrape_recruiters(company):
    """Scrape recruiter names for a given company"""
    print(f"Starting scraping for {company}...")

    roles = [
        {"role": "technical recruiter", "search_text": f"{company} technical recruiter"},
        {"role": "university recruiter", "search_text": f"{company} university recruiter"}
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
            save_recruiter_data(all_recruiters, company)

        browser.close()

        # Clean up temp directory
        try:
            os.rmdir("./data/temp")
            print("Removed temp directory")
        except:
            print("Note: Temp directory not empty or already removed")


def print_usage():
    print("""
Usage:
    python3 main.py scrape <company_name>     - Scrape recruiter names for the specified company
    python3 main.py generate_mails <company_name>  - Generate emails for previously scraped recruiters
    """)

def generate_mails(company):
    """Generate emails and drafts for company"""
    # First generate email addresses
    if generate_emails(company):
        # Then generate drafts
        if generate_company_drafts(company):
            print(f"\nEmail generation complete for {company}")
            print(f"You can find:")
            print(f"1. Email data in: data/{company}/recruiters.xlsx")
            print(f"2. Email drafts in: data/{company}/drafts/drafts.json")
            print(f"3. Preview drafts in: data/{company}/drafts/preview.html")
            return True
    return False

def send_mails(company):
    """Send emails to recruiters with Gmail limits"""
    try:
        # Initialize email sender
        sender = GmailSender()

        # Determine file path based on company name
        if company.lower() == 'test':
            file_path = "data/test/recruiter.xlsx"
        else:
            file_path = f"data/{company}/recruiters.xlsx"

        if not os.path.exists(file_path):
            print(f"No recruiter data found at: {file_path}")
            return False

        # Read recruiter data
        df = pd.read_excel(file_path)

        # Add Email_Sent column if it doesn't exist
        if 'Email_Sent' not in df.columns:
            df['Email_Sent'] = False
            df['Email_Sent_Date'] = None

        # Get count of unsent emails
        unsent_emails = len(df[~df['Email_Sent']])
        print(f"\nPreparing to send emails for {company}")
        print(f"Found {unsent_emails} unsent emails")

        # Check daily limit
        DAILY_LIMIT = 300  # Reduced daily limit to stay safe
        if unsent_emails > DAILY_LIMIT:
            print(f"Warning: You have {unsent_emails} emails to send, but daily limit is set to {DAILY_LIMIT}")
            print("The script will stop after reaching the daily limit")
            print("You can run the script again tomorrow to continue - it will resume where it left off")

        # Initialize counters
        emails_sent_today = 0
        emails_sent_minute = 0
        minute_start = time.time()

        # Send emails to each recruiter
        for idx, row in df.iterrows():
            if pd.isna(row['Email_Sent']) or not row['Email_Sent']:
                # Check daily limit
                if emails_sent_today >= DAILY_LIMIT:
                    remaining = len(df[~df['Email_Sent']]) - emails_sent_today
                    print(f"\nReached daily limit of {DAILY_LIMIT} emails")
                    print(f"Still have {remaining} emails remaining to send")
                    print("Run the script again tomorrow to continue sending")
                    break

                # Check rate limit (20 emails per minute to be safe)
                current_time = time.time()
                if current_time - minute_start >= 60:
                    # Reset minute counter
                    minute_start = current_time
                    emails_sent_minute = 0
                elif emails_sent_minute >= 20:
                    # Wait for the remainder of the minute
                    wait_time = 60 - (current_time - minute_start)
                    print(f"\nReached rate limit. Waiting {wait_time:.0f} seconds...")
                    time.sleep(wait_time)
                    minute_start = time.time()
                    emails_sent_minute = 0

                print(f"\nSending email to: {row['Full Name']} ({row['Email']})")
                print(f"Emails sent today: {emails_sent_today}/{DAILY_LIMIT}")

                if sender.send_email(
                        to_email=row['Email'],
                        recruiter_name=row['First Name'],
                        company_name=company
                ):
                    df.at[idx, 'Email_Sent'] = True
                    df.at[idx, 'Email_Sent_Date'] = pd.Timestamp.now()
                    # Save after each successful send
                    df.to_excel(file_path, index=False)
                    print("Email sent successfully!")

                    # Update counters
                    emails_sent_today += 1
                    emails_sent_minute += 1

                    # Add delay between emails
                    if idx < len(df) - 1:  # Don't delay after last email
                        delay = 5  # 5 seconds between emails
                        print(f"Waiting {delay} seconds before next email...")
                        time.sleep(delay)
                else:
                    print("Failed to send email")

        # Print summary
        sent_count = df['Email_Sent'].sum()
        remaining = len(df) - sent_count
        print(f"\nEmail sending complete for {company}")
        print(f"Successfully sent: {sent_count}/{len(df)} emails")
        if remaining > 0:
            print(f"Remaining emails to send: {remaining}")
            print("Run the script again tomorrow to continue")
        return True

    except Exception as e:
        print(f"Error in send_mails: {str(e)}")
        return False

def print_usage():
    print("""
    LinkedIn Recruiter Email Automation Tool
    
    Usage:
        python3 autobot.py scrape <company_name>         - Scrape recruiter information from LinkedIn
        python3 autobot.py generate_mails <company_name> - Generate email addresses and drafts
        python3 autobot.py send_mails <company_name>     - Send emails to recruiters
    
    Examples:
        # Scrape recruiters from Google:
        python3 autobot.py scrape Google
    
        # Generate email drafts for Google recruiters:
        python3 autobot.py generate_mails Google
    
        # Send test emails:
        python3 autobot.py send_mails test
    
    Note:
        - Use 'test' as company_name to use test data
        - Emails are limited to 300 per day
        - Check data/<company_name>/drafts/preview.html to review drafts
        """)


def main():
    if len(sys.argv) != 3:
        print_usage()
        return

    command = sys.argv[1].lower()
    company = sys.argv[2]

    # Validate command
    valid_commands = {
        "scrape": scrape_recruiters,
        "generate_mails": generate_mails,
        "send_mails": send_mails
    }

    if command not in valid_commands:
        print(f"Error: Unknown command '{command}'")
        print_usage()
        return

    # Execute command
    try:
        print(f"\nExecuting '{command}' for company '{company}'...")
        success = valid_commands[command](company)

        if success:
            print(f"\nSuccessfully completed '{command}' for {company}")
        else:
            print(f"\nFailed to complete '{command}' for {company}")

    except Exception as e:
        print(f"\nError executing {command}: {str(e)}")
        print("Please check the usage instructions and try again")

if __name__ == "__main__":
    main()