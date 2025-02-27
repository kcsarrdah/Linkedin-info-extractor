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

        # Ensure proper data types and handle NA values
        string_columns = ['Full Name', 'First Name', 'Last Name', 'Title', 'Email',
                          'Email Status', 'Email Source', 'LinkedIn URL', 'Company', 'Headline']
        for col in string_columns:
            if col not in df.columns:
                df[col] = ''
            # Fill NA values with empty strings to avoid boolean ambiguity
            df[col] = df[col].fillna('')

        # Initialize Apollo client
        apollo_client = ApolloClient()
        stats = {'apollo': 0, 'fallback': 0, 'error': 0, 'skipped': 0, 'skipped_unavailable': 0}
        total_to_process = len(df)
        already_processed = 0

        print(f"\nStarting email generation for {company}")
        print(f"Total records to check: {total_to_process}")

        for index, row in df.iterrows():
            # Skip records that already have a valid email
            if row['Email'] != '':
                stats['skipped'] += 1
                print(f"Skipping {row['Full Name']} - Already has email: {row['Email']}")
                already_processed += 1
                continue

            # Skip records that were previously marked as unavailable
            if row['Email Status'] == 'unavailable' or row['Email Source'] == 'apollo':
                stats['skipped_unavailable'] += 1
                print(f"Skipping {row['Full Name']} - Previously marked unavailable")
                already_processed += 1
                continue

            # Generate email for this record
            person_data = apollo_client.fetch_apollo_data(
                first_name=row['First Name'],
                last_name=row['Last Name'],
                organization_name=company,
                domain=f"@{company.lower().replace(' ', '')}.com"
            )

            if 'error' in person_data:
                if 'limit reached' in person_data['error'] or 'rate limit' in person_data['error'].lower():
                    print(f"Rate limit reached: {person_data['error']}")
                    # Save progress before stopping
                    df.to_excel(file_path, index=False)
                    print(f"\nProgress before stopping: {already_processed}/{total_to_process}")
                    print(f"Apollo API: {stats['apollo']}")
                    print(f"Fallback Method: {stats['fallback']}")
                    print(f"Skipped (has email): {stats['skipped']}")
                    print(f"Skipped (unavailable): {stats['skipped_unavailable']}")
                    print(f"Errors: {stats['error']}")
                    return True

                stats['error'] += 1
                print(f"Generated (error): {row['Full Name']} -> None")
                already_processed += 1
                continue

            person = person_data.get('person', {})

            # Update all available fields
            df.at[index, 'Email'] = person.get('email', '')
            df.at[index, 'Email Status'] = person.get('email_status', 'fallback')
            df.at[index, 'Email Source'] = 'apollo'
            df.at[index, 'LinkedIn URL'] = person.get('linkedin_url', row['LinkedIn URL'])  # Keep existing if not found
            df.at[index, 'First Name'] = person.get('first_name', row['First Name'])  # Keep existing if not found
            df.at[index, 'Last Name'] = person.get('last_name', row['Last Name'])  # Keep existing if not found
            df.at[index, 'Title'] = person.get('title', row['Title'])
            df.at[index, 'Headline'] = person.get('headline', '')
            df.at[index, 'Last Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            status = 'apollo' if person.get('email') else 'error'
            stats[status] += 1

            print(f"Generated ({status}): {row['Full Name']} -> {person.get('email', 'No email found')}")
            already_processed += 1

            # Save progress periodically (every 10 records)
            if already_processed % 10 == 0:
                df.to_excel(file_path, index=False)
                print(f"Progress saved at {already_processed}/{total_to_process} records")

        # Save final results
        df.to_excel(file_path, index=False)

        print(f"\nEmail Generation Summary:")
        print(f"Apollo API: {stats['apollo']}")
        print(f"Fallback Method: {stats['fallback']}")
        print(f"Skipped (has email): {stats['skipped']}")
        print(f"Skipped (unavailable): {stats['skipped_unavailable']}")
        print(f"Errors: {stats['error']}")

        return True

    except Exception as e:
        import traceback
        print(f"Error generating emails: {e}")
        print(traceback.format_exc())  # Print full traceback for debugging

        # Try to save progress even if there's an error
        try:
            df.to_excel(file_path, index=False)
            print("Saved progress despite error")
        except:
            pass

        return False