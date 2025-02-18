# src/emailDraftManager.py
import os
import json
import pandas as pd
from datetime import datetime

class EmailDraftManager:
    def __init__(self):
        self.template = """
<div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #000;">
    <p>Hey {Recruiter_Name},</p>

    <p>I am Krishnna from Boston. I recently graduated from Northeastern University with a master's degree in computer software engineering.</p>

    <p>I am reaching out to express my strong interest in joining {Company_Name} as a Software Engineer. I would love to learn more about and be considered for any open positions that you might currently be recruiting for. If not, I would greatly appreciate it if you could forward my profile to someone who might be.</p>

    <p>I have attached my resume to this email for your review. Beyond my resume, I have been learning more about Gen AI and its integration with software through personal projects. I am always excited to tackle problems and hungry for experience and learning in the process.</p>

    <p>I am excited by the work {Company_Name} is doing, and I truly believe my hard work and grit can make a difference there.</p>

    <p>Thank you for taking the time and looking forward to speaking with you,<br>
    Krishnna Sarrdah</p>

    <p style="font-style: italic;">P.S I understand if you do not appreciate being contacted this way, and apologize for the same</p>
</div>
"""

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
                "drafts": []
            }

            # Add Email_Draft column to Excel if it doesn't exist
            if 'Email_Draft' not in df.columns:
                df['Email_Draft'] = None

            # Generate drafts for each recruiter
            for idx, row in df.iterrows():
                recruiter_name = self.format_name(row['First Name'])
                draft = self.template.format(
                    Recruiter_Name=recruiter_name,
                    Company_Name=company
                )

                # Store draft in Excel
                df.at[idx, 'Email_Draft'] = draft

                # Add to quick-copy format
                drafts_data["drafts"].append({
                    "recruiter_name": row['Full Name'],
                    "email": row['Email'],
                    "draft": draft
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
            with open(preview_file, 'w', encoding='utf-8') as f:
                f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .draft-container {{
            margin: 20px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .draft-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #eee;
        }}
        .receiver-info {{
            margin: 0;
            color: #333;
        }}
        .copy-button {{
            background-color: #0066cc;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }}
        .copy-button:hover {{
            background-color: #0052a3;
            transform: translateY(-1px);
        }}
        .copy-button.copied {{
            background-color: #4CAF50;
        }}
        .email-content {{
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            line-height: 1.6;
        }}
        h1 {{
            color: #333;
            margin-bottom: 30px;
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 2px solid #0066cc;
        }}
    </style>
</head>
<body>
    <h1>Email Drafts for {company}</h1>
""")

                # Add drafts
                for idx, draft in enumerate(drafts_data["drafts"]):
                    plain_text = f"""Hey {draft['recruiter_name'].split()[0]},

I am Krishnna from Boston. I recently graduated from Northeastern University with a master's degree in computer software engineering.

I am reaching out to express my strong interest in joining {company} as a Software Engineer. I would love to learn more about and be considered for any open positions that you might currently be recruiting for. If not, I would greatly appreciate it if you could forward my profile to someone who might be.

I have attached my resume to this email for your review. Beyond my resume, I have been learning more about Gen AI and its integration with software through personal projects. I am always excited to tackle problems and hungry for experience and learning in the process.

I am excited by the work {company} is doing, and I truly believe my hard work and grit can make a difference there.

Thank you for taking the time and looking forward to speaking with you,
Krishnna Sarrdah

P.S I understand if you do not appreciate being contacted this way, and apologize for the same"""

                    f.write(f"""
    <div class="draft-container">
        <div class="draft-header">
            <h3 class="receiver-info">To: {draft['recruiter_name']} ({draft['email']})</h3>
            <button class="copy-button" onclick="copyToClipboard(this, `{plain_text.replace('`', '\\`')}`)">
                Copy Draft
            </button>
        </div>
        <div class="email-content">
            {draft['draft']}
        </div>
    </div>
""")

                # Add copy script at the end
                f.write("""
    <script>
        function copyToClipboard(button, text) {
            navigator.clipboard.writeText(text).then(function() {
                button.textContent = 'Copied!';
                button.classList.add('copied');
                setTimeout(function() {
                    button.textContent = 'Copy Draft';
                    button.classList.remove('copied');
                }, 2000);
            }).catch(function(err) {
                console.error('Failed to copy:', err);
                button.textContent = 'Failed to copy';
                setTimeout(function() {
                    button.textContent = 'Copy Draft';
                }, 2000);
            });
        }
    </script>
</body>
</html>
""")
            print(f"Generated preview file at {preview_file}")
            return True

        except Exception as e:
            print(f"Error generating drafts: {str(e)}")
            return False

def generate_company_drafts(company):
    """Function to be called from main script"""
    try:
        manager = EmailDraftManager()
        return manager.generate_drafts(company)
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    # Test draft generation
    generate_company_drafts("test")