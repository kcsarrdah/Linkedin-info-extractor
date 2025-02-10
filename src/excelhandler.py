# src/excelhandler.py
import pandas as pd
import os
from .emailGenerator import EmailGenerator

def split_name(full_name: str) -> tuple:
    email_generator = EmailGenerator()
    cleaned_name = email_generator.clean_name(full_name)
    parts = cleaned_name.split()
    if len(parts) >= 2:
        return parts[0], ' '.join(parts[1:])
    return full_name, ''

def save_recruiter_data(recruiters: list, company: str) -> bool:
    try:
        data = []
        for recruiter in recruiters:
            first_name, last_name = split_name(recruiter['name'])
            data.append({
                'Full Name': recruiter['name'],
                'First Name': first_name,
                'Last Name': last_name,
                'Title': recruiter.get('title', ''),
                'Email': '',  # Will be filled by generate_emails
                'Company': company,
                'LinkedIn Profile': '',
                'Status': 'New'
            })

        df = pd.DataFrame(data)
        os.makedirs(f"data/{company}", exist_ok=True)
        file_path = f"data/{company}/recruiters.xlsx"
        df.to_excel(file_path, index=False)
        print(f"\nSaved {len(data)} recruiters to {file_path}")
        return True

    except Exception as e:
        print(f"Error saving data: {e}")
        return False

def generate_emails(company: str) -> bool:
    """Generate emails for recruiters in Excel file"""
    try:
        file_path = f"data/{company}/recruiters.xlsx"
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False

        df = pd.read_excel(file_path)
        email_generator = EmailGenerator()
        emails_generated = 0

        for index, row in df.iterrows():
            if pd.isna(row['Email']) or row['Email'] == '':
                email = email_generator.generate_email(
                    row['First Name'],
                    row['Last Name'],
                    company
                )
                if email:
                    df.at[index, 'Email'] = email
                    emails_generated += 1
                    print(f"Generated: {row['Full Name']} -> {email}")

        df.to_excel(file_path, index=False)
        print(f"\nGenerated {emails_generated} emails")
        return True

    except Exception as e:
        print(f"Error generating emails: {e}")
        return False