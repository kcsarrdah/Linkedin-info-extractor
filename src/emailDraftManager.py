# src/emailDraftManager.py
import os
import json
import pandas as pd
from datetime import datetime
from src.utils.templateManager import template_manager
from src.utils.html_templates import get_preview_html_template, get_draft_container_template


class EmailDraftManager:
    def __init__(self, template_name="enhanced"):
        # Instead of hardcoding the template, we'll use the template manager
        self.template_name = template_name

    def format_name(self, name: str) -> str:
        """Ensure proper capitalization of name"""
        if not name:
            return ""
        name_parts = name.strip().split()
        capitalized_parts = [part.capitalize() for part in name_parts]
        return " ".join(capitalized_parts)

    def generate_drafts(self, company):
        """Generate email drafts for a company"""
        try:
            # Read recruiter data
            file_path = f"data/{company}/recruiters.xlsx"
            if not os.path.exists(file_path):
                print(f"No recruiter data found for {company}")
                return False

            df = pd.read_excel(file_path)
            print(f"Generating drafts for {len(df)} recruiters...")

            # Create drafts directory
            drafts_dir = f"data/{company}/drafts"
            os.makedirs(drafts_dir, exist_ok=True)

            # Generate quick-copy format
            drafts_data = {
                "company": company,
                "generated_at": datetime.now().isoformat(),
                "template_used": self.template_name,
                "drafts": []
            }

            # Add Email_Draft column to Excel if it doesn't exist
            if 'Email_Draft' not in df.columns:
                df['Email_Draft'] = None

            # Ensure Email_Draft column is of object type to store HTML content
            if df['Email_Draft'].dtype != 'object':
                df['Email_Draft'] = df['Email_Draft'].astype('object')

            # Generate drafts for each recruiter
            for idx, row in df.iterrows():
                recruiter_name = self.format_name(row['First Name'])

                # Use template manager to format the template
                formatted_email = template_manager.format_template(
                    template_name=self.template_name,
                    recruiter_name=recruiter_name,
                    company_name=company
                )

                if not formatted_email:
                    print(f"Error: Could not format email template for {recruiter_name}")
                    continue

                draft_html = formatted_email["html"]
                draft_plain = formatted_email["plain"]
                subject = formatted_email["subject"]

                # Store draft in Excel
                df.at[idx, 'Email_Draft'] = draft_html

                # Add to quick-copy format
                drafts_data["drafts"].append({
                    "recruiter_name": row['Full Name'],
                    "email": row['Email'],
                    "subject": subject,
                    "draft_html": draft_html,
                    "draft_plain": draft_plain
                })

            # Save updated Excel file
            df.to_excel(file_path, index=False)
            print(f"Updated {file_path} with draft emails")

            # Save quick-copy format
            drafts_file = f"{drafts_dir}/drafts.json"
            with open(drafts_file, 'w', encoding='utf-8') as f:
                json.dump(drafts_data, f, indent=2, ensure_ascii=False)
            print(f"Saved quick-copy drafts to {drafts_file}")

            # Generate preview file
            preview_file = f"{drafts_dir}/preview.html"
            preview_template = get_preview_html_template()
            draft_container_template = get_draft_container_template()

            # Build all draft containers
            # Build all draft containers
            draft_containers = ""
            for draft in drafts_data["drafts"]:
                try:
                    # Ensure all values are strings and handle NaN values
                    recruiter_name = str(draft['recruiter_name']) if not pd.isna(draft['recruiter_name']) else ""

                    # Handle NaN in email
                    email = draft['email']
                    if pd.isna(email):
                        email = ""
                        email_display = ""
                    else:
                        email = str(email)
                        email_display = f"({email})"

                    subject = str(draft['subject']) if not pd.isna(draft['subject']) else ""
                    draft_html = str(draft['draft_html']) if not pd.isna(draft['draft_html']) else ""
                    draft_plain = str(draft['draft_plain']) if not pd.isna(draft['draft_plain']) else ""

                    # Escape special characters in the plain text
                    escaped_plain = draft_plain.replace('`', '\\`').replace('\\', '\\\\').replace('\n', '\\n')

                    # Format the draft container
                    container = draft_container_template
                    container = container.replace("{{recruiter_name}}", recruiter_name)
                    container = container.replace("{{email_display}}", email_display)
                    container = container.replace("{{draft_plain}}", escaped_plain)
                    container = container.replace("{{subject}}", subject)
                    container = container.replace("{{draft_html}}", draft_html)

                    draft_containers += container
                except Exception as e:
                    print(f"Error formatting draft for {draft.get('recruiter_name', 'unknown')}: {str(e)}")
                    continue

            # Format the full preview HTML
            preview_html = preview_template
            preview_html = preview_html.replace("{{company}}", company)
            preview_html = preview_html.replace("{{template_name}}", self.template_name)
            preview_html = preview_html.replace("{{draft_containers}}", draft_containers)

            # Write the full HTML to the preview file
            with open(preview_file, 'w', encoding='utf-8') as f:
                f.write(preview_html)

            print(f"Generated preview file at {preview_file}")
            return True

        except Exception as e:
            print(f"Error generating drafts: {str(e)}")
            return False


def generate_company_drafts(company, template_name="enhanced"):
    """Function to be called from main script"""
    try:
        manager = EmailDraftManager(template_name=template_name)
        return manager.generate_drafts(company)
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


if __name__ == "__main__":
    # Test draft generation
    generate_company_drafts("test")