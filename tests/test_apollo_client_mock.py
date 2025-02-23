import pytest
import responses
import json
from src.utils.apollo_client import ApolloClient

@pytest.fixture
def apollo_client():
    """Create Apollo client instance"""
    return ApolloClient()

@pytest.fixture
def sample_response():
    """Load our stored sample response"""
    with open("tests/data/mock_responses/apollo_sample_response.json", "r") as f:
        return json.load(f)

@responses.activate
def test_successful_api_call(apollo_client, sample_response):
    """Test successful API call with normal rate limits"""
    responses.add(
        responses.POST,
        "https://api.apollo.io/v1/people/match",
        json=sample_response['response'],
        status=200,
        headers={
            'x-24-hour-usage': '10',
            'x-hourly-usage': '5',
            'x-minute-usage': '1'
        }
    )

    response = apollo_client.fetch_apollo_data(
        first_name="Test",
        last_name="User",
        organization_name="Adobe",
        domain="adobe.com"
    )

    assert "error" not in response
    assert apollo_client.daily_usage == 10
    assert apollo_client.hourly_usage == 5
    assert apollo_client.minute_usage == 1

@responses.activate
def test_rate_limit_exceeded(apollo_client):
    """Test when rate limit is exceeded"""
    # Mock response with rate limit exceeded
    responses.add(
        responses.POST,
        "https://api.apollo.io/v1/people/match",
        status=429,  # HTTP 429 Too Many Requests
        headers={
            'x-24-hour-usage': '600',  # Daily limit
            'x-hourly-usage': '200',   # Hourly limit
            'x-minute-usage': '50'     # Minute limit
        }
    )

    response = apollo_client.fetch_apollo_data(
        first_name="Test",
        last_name="User",
        organization_name="Adobe",
        domain="adobe.com"
    )

    assert "error" in response
    assert "rate limit exceeded" in response["error"].lower()
    assert apollo_client.daily_usage == 600

@responses.activate
def test_api_error(apollo_client):
    """Test handling of API errors"""
    responses.add(
        responses.POST,
        "https://api.apollo.io/v1/people/match",
        json={"error": "Invalid API key"},
        status=401
    )

    response = apollo_client.fetch_apollo_data(
        first_name="Test",
        last_name="User",
        organization_name="Adobe",
        domain="adobe.com"
    )

    assert "error" in response
    assert "API request failed" in response["error"]

@responses.activate
def test_multiple_calls_rate_tracking(apollo_client):
    """Test rate limit tracking across multiple calls"""
    # First call
    responses.add(
        responses.POST,
        "https://api.apollo.io/v1/people/match",
        json={"result": "success"},
        status=200,
        headers={
            'x-24-hour-usage': '48',
            'x-hourly-usage': '20',
            'x-minute-usage': '5'
        }
    )

    # Second call - higher usage
    responses.add(
        responses.POST,
        "https://api.apollo.io/v1/people/match",
        json={"result": "success"},
        status=200,
        headers={
            'x-24-hour-usage': '49',
            'x-hourly-usage': '21',
            'x-minute-usage': '6'
        }
    )

    # Make first call
    apollo_client.fetch_apollo_data(
        first_name="Test1",
        last_name="User1",
        organization_name="Adobe",
        domain="adobe.com"
    )

    # Verify first call limits
    assert apollo_client.daily_usage == 48
    assert apollo_client.hourly_usage == 20
    assert apollo_client.minute_usage == 5

    # Make second call
    apollo_client.fetch_apollo_data(
        first_name="Test2",
        last_name="User2",
        organization_name="Adobe",
        domain="adobe.com"
    )

    # Verify updated limits
    assert apollo_client.daily_usage == 49
    assert apollo_client.hourly_usage == 21
    assert apollo_client.minute_usage == 6