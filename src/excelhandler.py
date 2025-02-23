import pandas as pd
import os
from .emailGenerator import EmailGenerator
from .utils.NameCleaner import NameCleaner
import time
from datetime import datetime
import re
from src.utils.apollo_client import ApolloClient


def save_recruiter_data(recruiters: list, company: str) -> bool:
    """Save initial recruiter data to Excel with cleaning"""

    try:
        cleaner = NameCleaner()
        data = []
        for recruiter in recruiters:
            cleaned_name = cleaner.clean_name(recruiter['name'])
            if cleaned_name:
                data.append({
                    'Full Name': cleaned_name['full_name'],
                    'First Name': cleaned_name['first_name'],
                    'Middle Name': cleaned_name['middle_name'],
                    'Last Name': cleaned_name['last_name'],
                    'Title': cleaner.clean_title(recruiter.get('title', '')),
                    'Role': '',
                    'Email': '',
                    'Email Status': '',  # verified, unavailable, or fallback
                    'Email Source': '',  # apollo or fallback
                    'LinkedIn URL': recruiter.get('linkedin_url', ''),
                    'Headline': '',
                    'Company': company,
                    'Status': 'New',
                    'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

        # Create DataFrame and handle duplicates
        df = pd.DataFrame(data)
        df = df.drop_duplicates(subset=['Full Name'], keep='first')

        # Ensure proper data types
        string_columns = ['Full Name', 'First Name', 'Middle Name', 'Last Name',
                         'Title', 'Email', 'Email Status', 'Email Source',
                         'LinkedIn URL', 'Company']
        for col in string_columns:
            df[col] = df[col].astype('string')

        # Save file
        os.makedirs(f"data/{company}", exist_ok=True)
        file_path = f"data/{company}/recruiters.xlsx"
        df.to_excel(file_path, index=False)

        print(f"\nSaved {len(df)} unique recruiters to {file_path}")
        return True

    except Exception as e:
        print(f"Error saving data: {e}")
        return False


def get_mails_from_apollo(company: str) -> bool:
    """Generate emails for recruiters using Apollo API with rate limiting"""
    try:
        file_path = f"data/{company}/recruiters.xlsx"
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False

        # Read and clean data
        df = pd.read_excel(file_path)
        df = df.drop_duplicates(subset=['Full Name'], keep='first')

        # Ensure proper data types
        string_columns = ['Full Name', 'First Name', 'Last Name', 'Title', 'Email',
                          'Email Status', 'Email Source', 'LinkedIn URL', 'Company', 'Headline']
        for col in string_columns:
            df[col] = df[col].astype('string')

        # Initialize Apollo client
        apollo_client = ApolloClient()
        stats = {'apollo': 0, 'fallback': 0, 'error': 0}

        for index, row in df.iterrows():
            if pd.isna(row['Email']) or row['Email'] == '':
                person_data = apollo_client.fetch_apollo_data(
                    first_name=row['First Name'],
                    last_name=row['Last Name'],
                    organization_name=company,
                    domain=f"@{company.lower().replace(' ', '')}.com"
                )

                if 'error' in person_data:
                    if 'limit reached' in person_data['error']:
                        print(f"Rate limit reached: {person_data['error']}")
                        break
                    stats['error'] += 1
                    continue

                person = person_data.get('person', {})

                # Update all available fields
                df.at[index, 'Email'] = person.get('email', '')
                df.at[index, 'Email Status'] = person.get('email_status', 'fallback')
                df.at[index, 'Email Source'] = 'apollo'
                df.at[index, 'LinkedIn URL'] = person.get('linkedin_url',row['LinkedIn URL'])  # Keep existing if not found
                df.at[index, 'First Name'] = person.get('first_name', row['First Name'])  # Keep existing if not found
                df.at[index, 'Last Name'] = person.get('last_name', row['Last Name'])  # Keep existing if not found
                df.at[index, 'Title'] = person.get('title', row['Title'])
                df.at[index, 'Headline'] = person.get('headline', '')
                df.at[index, 'Last Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                status = 'apollo' if person_data.get('person', {}).get('email') else 'error'
                stats[status] += 1

                print(
                    f"Generated ({status}): {row['Full Name']} -> {person_data.get('person', {}).get('email', 'No email found')}")

        df.to_excel(file_path, index=False)
        print(f"\nEmail Generation Summary:")
        print(f"Apollo API: {stats['apollo']}")
        print(f"Fallback Method: {stats['fallback']}")
        print(f"Errors: {stats['error']}")
        return True

    except Exception as e:
        print(f"Error generating emails: {e}")
        return False