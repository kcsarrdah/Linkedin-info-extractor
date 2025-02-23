import pytest
import os
import json
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """Return the path to the test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def sample_companies_data():
    """Sample company email format data."""
    return {
        "TestCompany": [1, "@testcompany.com"],
        "Google": [1, "@google.com"],
        "Microsoft": [3, "@microsoft.com"],
        "Empty": []
    }


@pytest.fixture(scope="session")
def sample_recruiter_data():
    """Sample recruiter data for testing."""
    return [
        {
            "name": "John Doe",
            "title": "Technical Recruiter",
            "linkedin_url": "https://linkedin.com/in/johndoe"
        },
        {
            "name": "Jane Smith",
            "title": "Senior Technical Recruiter",
            "linkedin_url": "https://linkedin.com/in/janesmith"
        },
        {
            "name": "LinkedIn Member",  # Should be filtered out
            "title": "Recruiter",
            "linkedin_url": ""
        }
    ]


@pytest.fixture(scope="session")
def sample_apollo_response():
    """Sample Apollo API response."""
    return {
        "person": {
            "id": "test_id",
            "first_name": "John",
            "last_name": "Doe",
            "name": "John Doe",
            "email": "john.doe@testcompany.com",
            "email_status": "verified",
            "title": "Technical Recruiter",
            "linkedin_url": "https://linkedin.com/in/johndoe"
        }
    }


@pytest.fixture(scope="function")
def temp_excel_file(tmp_path):
    """Create a temporary Excel file for testing."""
    import pandas as pd

    # Sample data
    data = {
        'Full Name': ['John Doe', 'Jane Smith'],
        'First Name': ['John', 'Jane'],
        'Last Name': ['Doe', 'Smith'],
        'Title': ['Technical Recruiter', 'Senior Recruiter'],
        'Email': ['', ''],
        'Email Status': ['', ''],
        'Email Source': ['', ''],
        'LinkedIn URL': ['https://linkedin.com/in/johndoe', 'https://linkedin.com/in/janesmith']
    }

    # Create DataFrame and save to temp file
    df = pd.DataFrame(data)
    file_path = tmp_path / "test_recruiters.xlsx"
    df.to_excel(file_path, index=False)

    return file_path


@pytest.fixture(scope="function")
def mock_linkedin_page(playwright):
    """Create a mock LinkedIn page for testing."""
    browser = playwright.chromium.launch()
    context = browser.new_context()
    page = context.new_page()

    yield page

    # Cleanup
    context.close()
    browser.close()


@pytest.fixture(scope="session")
def sample_html_content():
    """Sample HTML content for testing the HTML parser."""
    return """
    <div class="presence-entity">
        <img alt="John Doe" src="profile.jpg">
        <div class="entity-result__item">
            <div class="entity-result__primary-subtitle">Technical Recruiter at TestCompany</div>
        </div>
    </div>
    <div class="presence-entity">
        <img alt="Jane Smith" src="profile.jpg">
        <div class="entity-result__item">
            <div class="entity-result__primary-subtitle">Senior Technical Recruiter</div>
        </div>
    </div>
    """


@pytest.fixture(scope="function")
def sample_html_file(tmp_path, sample_html_content):
    """Create a temporary HTML file with sample content."""
    file_path = tmp_path / "test_page.html"
    file_path.write_text(sample_html_content)
    return file_path


def pytest_configure(config):
    """Create test data directories if they don't exist."""
    test_data_dir = Path(__file__).parent / "data"

    # Create directory structure
    for dir_name in ["html", "pdf", "excel", "mock_responses"]:
        (test_data_dir / dir_name).mkdir(parents=True, exist_ok=True)