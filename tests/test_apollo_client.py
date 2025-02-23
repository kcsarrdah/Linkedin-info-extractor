import pytest
import pandas as pd
import json
import os
from src.utils.apollo_client import ApolloClient
from datetime import datetime


def test_single_api_call():
    """Test a single real API call and store the response"""
    try:
        # Read the test data file
        df = pd.read_excel("tests/data/excel/recruiters.xlsx")

        # Get the first row of data
        test_row = df.iloc[0]

        # Initialize Apollo client
        client = ApolloClient()

        # Make the API call
        response = client.fetch_apollo_data(
            first_name=test_row['First Name'],
            last_name=test_row['Last Name'],
            organization_name="Adobe",
            domain="@adobe.com"
        )

        # Print response for inspection
        print("\nAPI Response:")
        print(f"Input name: {test_row['First Name']} {test_row['Last Name']}")
        print(f"Response: {response}")

        # Store the response
        mock_response = {
            "input": {
                "first_name": test_row['First Name'],
                "last_name": test_row['Last Name'],
                "organization": "Adobe",
                "domain": "@adobe.com"
            },
            "response": response,
            "timestamp": datetime.now().isoformat()
        }

        # Create mock_responses directory if it doesn't exist
        os.makedirs("tests/data/mock_responses", exist_ok=True)

        # Save to file
        with open("tests/data/mock_responses/apollo_sample_response.json", "w") as f:
            json.dump(mock_response, f, indent=2)

        # Basic validation
        assert isinstance(response, dict), "Response should be a dictionary"
        assert "error" not in response, f"Got error in response: {response.get('error', '')}"

    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, '-v'])