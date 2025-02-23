import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime


# Load environment variables from .env file
load_dotenv()

class ApolloClient:
    def __init__(self):
        self.api_key = os.getenv("APOLLO_API_KEY")
        if not self.api_key:
            raise ValueError("APOLLO_API_KEY not found in .env file")
        self.base_url = "https://api.apollo.io/v1/people/match"
        self.headers = {
            "accept": "application/json",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }
        self.daily_limit = 600
        self.hourly_limit = 200
        self.minute_limit = 50

        self._reset_usage_counters()

    def _reset_usage_counters(self):
        """Reset usage tracking"""
        self.daily_usage = 0
        self.hourly_usage = 0
        self.minute_usage = 0
        self.last_reset_day = datetime.now()
        self.last_reset_hour = datetime.now()
        self.last_reset_minute = datetime.now()

    def _update_usage(self, response_headers):
        """Update usage from API response headers"""
        self.daily_usage = int(response_headers.get('x-24-hour-usage', 0))
        self.hourly_usage = int(response_headers.get('x-hourly-usage', 0))
        self.minute_usage = int(response_headers.get('x-minute-usage', 0))

    def _check_rate_limits(self) -> tuple[bool, str]:
        """Check if we've hit any rate limits"""
        now = datetime.now()

        # Reset counters if time windows have passed
        if (now - self.last_reset_day).days >= 1:
            self.daily_usage = 0
            self.last_reset_day = now
        if (now - self.last_reset_hour).seconds >= 3600:
            self.hourly_usage = 0
            self.last_reset_hour = now
        if (now - self.last_reset_minute).seconds >= 60:
            self.minute_usage = 0
            self.last_reset_minute = now

        # Check limits
        if self.daily_usage >= self.daily_limit:
            return False, "Daily limit reached"
        if self.hourly_usage >= self.hourly_limit:
            return False, "Hourly limit reached"
        if self.minute_usage >= self.minute_limit:
            return False, "Minute limit reached"

        return True, ""

    def fetch_apollo_data(self, first_name: str, last_name: str, organization_name: str, domain: str) -> dict:
        """
        Fetch person data from Apollo API using name, company, and domain.
        Returns the API response as a dictionary or an error dict if failed.
        """
        try:
            can_make_request, limit_message = self._check_rate_limits()
            if not can_make_request:
                return {"error": limit_message}
            params = {
                "first_name": first_name,
                "last_name": last_name,
                "organization_name": organization_name,
                "domain": domain.strip('@') if domain else None,
                "reveal_personal_emails": True,
                "reveal_phone_number": False
            }

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=params
            )
            if response.headers:
                self._update_usage(response.headers)

            if response.status_code == 429:
                return {"error": "Rate limit exceeded"}

            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

# Example usage (for testing purposes)
if __name__ == "__main__":
    client = ApolloClient()
    test_response = client.fetch_apollo_data(
        first_name="John",
        last_name="Doe",
        organization_name="Glean",
        domain="glean.com"
    )
    print(json.dumps(test_response, indent=2))