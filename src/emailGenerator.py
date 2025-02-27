import json
import re
import requests
from pathlib import Path
from typing import Optional, Dict, Tuple
import time
from datetime import datetime, timedelta

class RateLimitManager:
    def __init__(self):
        self.daily_limit = 600
        self.hourly_limit = 200
        self.minute_limit = 50

        self.daily_usage = 0
        self.hourly_usage = 0
        self.minute_usage = 0

        self.last_reset_day = datetime.now()
        self.last_reset_hour = datetime.now()
        self.last_reset_minute = datetime.now()

    def update_limits(self, headers):
        """Update usage from API response headers"""
        self.daily_usage = int(headers.get('x-24-hour-usage', 0))
        self.hourly_usage = int(headers.get('x-hourly-usage', 0))
        self.minute_usage = int(headers.get('x-minute-usage', 0))

        # Update timestamps if needed
        current_time = datetime.now()
        if current_time - self.last_reset_day > timedelta(days=1):
            self.daily_usage = 0
            self.last_reset_day = current_time
        if current_time - self.last_reset_hour > timedelta(hours=1):
            self.hourly_usage = 0
            self.last_reset_hour = current_time
        if current_time - self.last_reset_minute > timedelta(minutes=1):
            self.minute_usage = 0
            self.last_reset_minute = current_time

    def can_make_request(self) -> Tuple[bool, Optional[float]]:
        """Check if we can make a request, return (can_request, wait_time)"""
        current_time = datetime.now()

        print(f"DEBUG: Current usage - Daily: {self.daily_usage}/{self.daily_limit}, "
              f"Hourly: {self.hourly_usage}/{self.hourly_limit}, "
              f"Minute: {self.minute_usage}/{self.minute_limit}")

        # Check daily limit
        if self.daily_usage >= self.daily_limit:
            print("DEBUG: Daily limit reached. Stopping operations.")
            return False, None

        # Check hourly limit
        if self.hourly_usage >= self.hourly_limit:
            wait_time = 3600 - (current_time - self.last_reset_hour).seconds
            print(f"DEBUG: Hourly limit reached. Wait time: {wait_time} seconds")
            return False, wait_time

        # Check minute limit
        if self.minute_usage >= self.minute_limit:
            wait_time = 60 - (current_time - self.last_reset_minute).seconds
            print(f"DEBUG: Minute limit reached. Wait time: {wait_time} seconds")
            return False, wait_time

        print("DEBUG: Rate limits OK, can make request")
        return True, 0


class EmailGenerator:
    def __init__(self):
        # Load company formats for fallback
        self.root_dir = Path(__file__).parent.parent
        company_file = self.root_dir / 'companies.txt'
        with open(company_file, 'r') as f:
            self.company_formats = json.load(f)

        # Get Apollo API key from environment variables
        from dotenv import load_dotenv
        import os

        load_dotenv()
        self.api_key = os.getenv("APOLLO_API_KEY")
        if not self.api_key:
            raise ValueError("APOLLO_API_KEY not found in environment variables")

        self.api_url = "https://api.apollo.io/api/v1/people/match"
        self.rate_limit_manager = RateLimitManager()

    def clean_name(self, name: str) -> str:
        """Remove LinkedIn status phrases, commas and special characters but preserve necessary spaces"""
        remove_phrases = [
            " is hiring",
            " is looking",
            " is seeking",
            " is recruiting",
            " is actively hiring",
            " is actively",
            " is open"
        ]

        for phrase in remove_phrases:
            name = name.replace(phrase, "")

        name = name.split(',')[0]
        name = re.sub(r'[^a-zA-Z\s]', ' ', name)
        name = ' '.join(name.split())
        return name.lower()

    def get_person_data(self, first_name: str, last_name: str, company: str, domain: str) -> Dict:
        """Get person data from Apollo API with improved rate limit handling and retry logic"""
        max_retries = 3
        retry_count = 0

        while retry_count <= max_retries:
            # Check if we can make a request
            can_request, wait_time = self.rate_limit_manager.can_make_request()

            if not can_request:
                if wait_time is None:
                    print("Daily limit reached. Cannot process more requests today.")
                    return {"error": "daily_limit_reached"}

                print(f"Rate limit reached. Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                print("Wait completed. Trying again...")  # Add this line
                # Continue to next loop iteration to check limits again after waiting
                continue

            # We can make a request, prepare and send it
            headers = {
                "accept": "application/json",
                "Cache-Control": "no-cache",
                "Content-Type": "application/json",
                "x-api-key": self.api_key
            }

            params = {
                "first_name": first_name,
                "last_name": last_name,
                "organization_name": company,
                "domain": domain,
                "reveal_personal_emails": True,
                "reveal_phone_number": False
            }

            try:
                response = requests.post(self.api_url, headers=headers, json=params)
                self.rate_limit_manager.update_limits(response.headers)

                # Check for rate limit response from API (HTTP 429)
                if response.status_code == 429:
                    retry_count += 1

                    # Get retry-after header if available, otherwise use default wait time
                    retry_after = int(response.headers.get('retry-after', 60))
                    print(
                        f"API rate limit hit (429). Waiting {retry_after} seconds before retry {retry_count}/{max_retries}...")

                    time.sleep(retry_after)
                    continue

                # Successful API call
                if response.status_code == 200:
                    data = response.json()
                    person = data.get('person', {})
                    return {
                        "email": person.get('email'),
                        "email_status": person.get('email_status'),
                        "title": person.get('title'),
                        "headline": person.get('headline'),
                        "linkedin_url": person.get('linkedin_url'),
                        "source": "apollo"
                    }

                # If we get here, it's a different API error
                error_msg = f"api_error_{response.status_code}"
                print(f"API returned error: {error_msg}")

                # For other errors, increment retry counter and try again
                retry_count += 1
                if retry_count <= max_retries:
                    print(f"Will retry request ({retry_count}/{max_retries}) after 5 seconds...")
                    time.sleep(5)
                    continue
                else:
                    return {"error": error_msg}

            except Exception as e:
                print(f"API error: {str(e)}")
                retry_count += 1
                if retry_count <= max_retries:
                    print(f"Retrying request ({retry_count}/{max_retries}) after 5 seconds...")
                    time.sleep(5)  # Wait 5 seconds before retry on connection errors
                    continue
                else:
                    return {"error": "api_error_max_retries"}

        # If we've exhausted all retries (shouldn't get here normally)
        return {"error": "api_error_max_retries"}

    def generate_fallback_email(self, first_name: str, last_name: str, company: str) -> str:
        """Generate email using traditional format"""
        try:
            format_type, domain = self.company_formats.get(company, [None, None])
            if not format_type or not domain:
                return ""

            first_name = first_name.lower().strip()
            last_name = last_name.lower().strip()
            first_initial = first_name[0] if first_name else ""

            if format_type == 1:
                return f"{first_initial}{last_name}{domain}"
            elif format_type == 2:
                return f"{first_name}{last_name}{domain}"
            elif format_type == 3:
                return f"{first_name}.{last_name}{domain}"
            elif format_type == 4:
                return f"{first_name}{domain}"
            elif format_type == 5:
                return f"{first_initial}.{last_name}{domain}"
            elif format_type == 6:
                return f"{first_name}_{last_name}{domain}"
            return None

        except Exception as e:
            print(f"Fallback email generation error: {e}")
            return None

    def generate_email(self, first_name: str, last_name: str, company: str) -> Dict:
        """Generate email and return additional data"""
        try:
            first_name = first_name.lower().strip()
            last_name = last_name.lower().strip()
            domain = self.company_formats.get(company, [None, None])[1]
            if domain:
                domain = domain.strip('@')

            if not domain:
                return {
                    "email": "",
                    "source": "error",
                    "error": "no_domain_format"
                }

            # Try Apollo API
            person_data = self.get_person_data(first_name, last_name, company, domain)

            if "error" in person_data:
                error = person_data["error"]
                if error == "daily_limit_reached":
                    return {"error": "daily_limit_reached"}
                elif error.startswith("api_error"):
                    return {
                        "email": self.generate_fallback_email(first_name, last_name, company),
                        "source": "fallback",
                        "error": error
                    }

            return person_data

        except Exception as e:
            print(f"Error generating email: {e}")
            return {"error": "general_error"}