# src/utils/templateManager.py
import os
import json
from pathlib import Path


class TemplateManager:
    """Manages email templates and company data"""

    def __init__(self):
        self.templates = {}
        self.company_data = {}
        self.email_formats = {}
        # Change the root directory to src/ instead of project root
        self.root_dir = Path(__file__).parent.parent

        # Load templates and company data
        self._load_templates()
        self._load_company_data()
        self._load_email_formats()

    def _load_templates(self):
        """Load all templates from src/data/templates directory"""
        template_dir = self.root_dir / 'data' / 'templates'

        if not template_dir.exists():
            print(f"Error: Template directory not found: {template_dir}")
            return

        for file_path in template_dir.glob('*.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                    template_name = file_path.stem  # Get filename without extension
                    self.templates[template_name] = template
                    print(f"Loaded template: {template_name}")
            except Exception as e:
                print(f"Error loading template {file_path}: {e}")

    def _load_company_data(self):
        """Load company keywords and focus areas"""
        company_data_path = self.root_dir / 'data' / 'company_keywords.json'

        if not company_data_path.exists():
            print(f"Error: Company data file not found: {company_data_path}")
            return

        try:
            with open(company_data_path, 'r', encoding='utf-8') as f:
                self.company_data = json.load(f)
                print(f"Loaded data for {len(self.company_data)} companies")
        except Exception as e:
            print(f"Error loading company data: {e}")

    def _load_email_formats(self):
        """Load company email formats from a Python dictionary in a text file"""
        formats_path = self.root_dir.parent / 'companies.txt'  # This is still in project root

        if not formats_path.exists():
            print(f"Error: Email formats file not found: {formats_path}")
            return

        try:
            with open(formats_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

                # Extract the dictionary part
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1

                if start_idx >= 0 and end_idx > start_idx:
                    dict_content = content[start_idx:end_idx]

                    # Convert Python dictionary string to actual dictionary
                    # We're using a safer approach than eval
                    email_formats = {}

                    # Parse the dictionary manually
                    import re

                    # Extract key-value pairs using regex
                    pattern = r'"([^"]+)"\s*:\s*(\[[^\]]*\])'
                    matches = re.findall(pattern, dict_content)

                    for company, format_info in matches:
                        # Clean up the format info
                        if format_info.strip() == "[]":
                            email_formats[company] = []
                        else:
                            # Extract the format type and domain
                            format_parts = format_info.strip('[]').split(',')
                            if len(format_parts) >= 2:
                                try:
                                    format_type = int(format_parts[0].strip())
                                    domain = format_parts[1].strip().strip('"\'')
                                    email_formats[company] = [format_type, domain]
                                except (ValueError, IndexError):
                                    email_formats[company] = []

                    self.email_formats = email_formats
                    print(f"Loaded email formats for {len(self.email_formats)} companies")
                else:
                    print("Error: Could not find dictionary content in companies.txt")
                    self.email_formats = {}
        except Exception as e:
            print(f"Warning: Error parsing email formats: {e}")
            # Initialize as empty dict to avoid errors
            self.email_formats = {}

    def get_template(self, template_name):
        """Get a template by name - no fallback"""
        if template_name not in self.templates:
            print(f"Error: Template '{template_name}' not found")
            return None
        return self.templates[template_name]

    def get_company_data(self, company_name):
        """Get company-specific data including focus areas and keywords"""
        # Normalize company name for lookup
        normalized_name = company_name.strip()

        # Try to find an exact match first
        company_info = self.company_data.get(normalized_name)

        # If no exact match, try case-insensitive
        if company_info is None:
            for name, data in self.company_data.items():
                if name.lower() == normalized_name.lower():
                    company_info = data
                    break

        # No fallback, return None if not found
        return company_info

    def get_email_format(self, company_name):
        """Get email format for company"""
        # Normalize company name for lookup
        normalized_name = company_name.strip()

        # Try to find an exact match first
        format_info = self.email_formats.get(normalized_name)

        # If no exact match, try case-insensitive
        if format_info is None:
            for name, data in self.email_formats.items():
                if name.lower() == normalized_name.lower():
                    format_info = data
                    break

        # No fallback, return None if not found
        return format_info


# src/utils/templateManager.py

    def format_template(self, template_name, recruiter_name, company_name):
        """
        Format a template with recruiter and company data

        Args:
            template_name: Name of the template to use
            recruiter_name: Name of the recruiter
            company_name: Name of the company

        Returns:
            dict: Formatted template with subject, html and plain text or None if template not found
        """
        template = self.get_template(template_name)
        if not template:
            return None

        company_data = self.get_company_data(company_name)
        if not company_data:
            # Use generic values if company data is not found
            company_data = {
                "focus": "innovative technology",
                "keywords": {
                    "tech_focus": "software development",
                    "company_focus": "technology innovation"
                },
                "project_examples": ""
            }

        # Prepare data for formatting
        formatting_data = {
            "recruiter_name": recruiter_name,
            "company_name": company_name,
            "company_focus": company_data.get("focus"),
            "tech_focus": company_data.get("keywords", {}).get("tech_focus"),
            "company_focus_area": company_data.get("keywords", {}).get("company_focus"),
            "project_examples": company_data.get("project_examples")
        }

        # Format the template
        subject = template.get("subject", "")
        html_content = template.get("html_content", "")
        plain_content = template.get("plain_content", "")

        # Replace special characters with proper HTML entities in the template
        html_content = html_content.replace("—", "&mdash;")  # Em dash
        plain_content = plain_content.replace("—", "--")  # Em dash for plain text

        # Format the subject
        for key, value in formatting_data.items():
            if value is not None:  # Only replace if value exists
                placeholder = "{{" + key + "}}"
                subject = subject.replace(placeholder, str(value))

        # Replace all placeholders in the content
        for key, value in formatting_data.items():
            if value is not None:  # Only replace if value exists
                placeholder = "{{" + key + "}}"
                html_content = html_content.replace(placeholder, str(value))
                plain_content = plain_content.replace(placeholder, str(value))

        return {
            "subject": subject,
            "html": html_content,
            "plain": plain_content
        }

# Create a singleton instance for easier imports
template_manager = TemplateManager()

# Example usage
if __name__ == "__main__":
    # Format a template for a recruiter
    email = template_manager.format_template(
        template_name="enhanced",
        recruiter_name="John",
        company_name="OpenAI"
    )

    if email:
        print("Subject:", email["subject"])
        print("\nHTML Content:")
        print(email["html"])