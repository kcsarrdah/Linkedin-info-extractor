# LinkedIn Info Extractor & Email Sender

A tool to scrape recruiter information from LinkedIn and send automated emails.

## Setup

### 1. Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration Files

#### A. Create .env file
Create a `.env` file in the root directory with the following contents:
```
LINKEDIN_EMAIL=your.linkedin.email@gmail.com
LINKEDIN_PASSWORD=your_linkedin_password

GMAIL_EMAIL=your.sending.email@gmail.com
GMAIL_PASSWORD=your_gmail_app_password
```

#### B. Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app"
   - Download the JSON file
   - Rename it to `credentials.json` and place it in the root directory

#### C. Resume Setup
1. Create a `resume` directory in the root folder:
```bash
mkdir resume
```
2. Place your resume in the directory:
```bash
cp path/to/your/resume.pdf resume/resume.pdf
```

## Usage

### 1. Scraping Recruiter Information
```bash
python3 autobot.py scrape company_name
```
This will:
- Login to LinkedIn
- Search for recruiters at the specified company
- Save recruiter information to an Excel file

### 2. Generating Emails
```bash
python3 autobot.py generate_mails company_name
```
This will:
- Read the scraped recruiter data
- Generate email addresses based on company format
- Save updated information with email addresses

### 3. Sending Emails
```bash
python3 autobot.py send_emails company_name
```
This will:
- Send test email to verify setup
- Use the email template with your resume attached


## File Formats

### companies.txt
Contains company email formats. Format types:
1. `firstname.lastname@domain.com`
2. `firstnamelastname@domain.com`
3. `firstname.l@domain.com`
...etc.

## Features
- Scrape LinkedIn recruiter information
- Generate company-specific email addresses
- Send automated emails with resume attachment
- Support for various company email formats

## Planned Features
- Collect data for software engineers from same college/school
- Collect engineering manager data
- Email verification
- Scheduled email sending

## Notes
- Keep companies.txt updated with new company email formats
- Test email sending with a test account first
- Respect rate limits and LinkedIn's terms of service

## Troubleshooting
- If emails aren't sending, check Gmail App Password
- If LinkedIn scraping fails, verify credentials
- For OAuth issues, ensure credentials.json is properly set up
