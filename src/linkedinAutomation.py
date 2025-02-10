import time
from playwright.sync_api import Page
from src.config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD

def login(page):
    try:
        print("Attempting to log in...")

        # Fill in email and password
        email_field = page.wait_for_selector('input[name="session_key"]', timeout=10000)
        print("Email field located")
        password_field = page.wait_for_selector('input[name="session_password"]', timeout=10000)
        print("Password field located")

        email_field.fill(LINKEDIN_EMAIL)
        print("Filled email")
        password_field.fill(LINKEDIN_PASSWORD)
        print("Filled password")
        # Click sign in
        sign_in = page.wait_for_selector('button[type="submit"]', timeout=10000)
        sign_in.click()
        print("Login submitted")

        # Wait for successful login
        page.wait_for_selector('#global-nav-typeahead', timeout=10000)
        print("Login successful")
    except Exception as e:
        print(f"Login failed: {e}")
        raise e


def search(page: Page, search_text: str):
    try:
        print(f"Attempting to search for: {search_text}")
        search_field = page.wait_for_selector('//*[@id="global-nav-typeahead"]/input')
        search_field.fill(search_text)
        print(f"Filled search field with: {search_text}")

        page.keyboard.press('Enter')
        print("Pressed Enter")
        time.sleep(3)  # Give search time to complete

        # Look for the People button without waiting for network idle
        try:
            # From your error output, we can see the actual button text
            people_button = page.wait_for_selector('button:has-text("People")', timeout=10000)
            if people_button:
                people_button.click()
                print("Successfully clicked People filter")
                time.sleep(2)
            else:
                print("People button found but null")
                page.screenshot(path="null_button.png")
        except Exception as e:
            print(f"Failed to click People filter: {str(e)}")
            page.screenshot(path="people_filter_error.png")
            raise e

    except Exception as e:
        print(f"Search failed: {str(e)}")
        page.screenshot(path="search_error.png")
        raise e

def filter_recruiters(page: Page, company: str):
    try:
        print("Applying filters...")

        location_field = page.wait_for_selector('//*[@id="searchFilter_geoUrn"]', timeout=10000)
        location_field.click()
        print("Location field clicked")
        time.sleep(2)

        us_location = page.wait_for_selector('.t-14:has-text("United States")', timeout=10000)
        us_location.click()
        print("United States location selected")
        time.sleep(2)

        location_dropdown = page.wait_for_selector('div.artdeco-hoverable-content--visible', timeout=10000)
        show_results_button = location_dropdown.query_selector('button:has-text("Show results")')
        show_results_button.click()
        print("Show results button clicked for location filter")
        page.wait_for_selector('div.search-results-container', timeout=10000)
        print("Results updated for location filter")

        time.sleep(5)

        current_company_field = page.wait_for_selector('//*[@id="searchFilter_currentCompany"]', timeout=10000)
        current_company_field.click()
        print("Current company filter clicked")
        time.sleep(2)

        search_given_company = page.wait_for_selector('#hoverable-outlet-current-company-filter-value .search-basic-typeahead input', timeout=10000)
        search_given_company.fill(company)
        print(f"Filled company: {company}")
        time.sleep(2)

        current_company_suggestion = page.wait_for_selector('#hoverable-outlet-current-company-filter-value .basic-typeahead__selectable', timeout=10000)
        current_company_suggestion.click()
        print("Current company selected from suggestions")

        company_dropdown = page.wait_for_selector('div.artdeco-hoverable-content--visible', timeout=10000)
        show_results_button = company_dropdown.query_selector('button:has-text("Show results")')
        show_results_button.click()
        print("Show results button clicked for company filter")
        page.wait_for_selector('div.search-results-container', timeout=10000)
        print("Results updated for company filter")

        time.sleep(5)

        print("Filters applied and dropdown closed")
    except Exception as e:
        print(f"Filter application failed: {e}")


def goto_next_page(page: Page) -> bool:
    """Navigate to the next page of search results"""
    try:
        print("Attempting to go to next page...")

        # First check if there are more pages
        page_state = page.query_selector('.artdeco-pagination__page-state')
        if page_state:
            text = page_state.inner_text()
            print(f"Found pagination state: {text}")
            if "Page 1 of 1" in text:
                print("Only one page available")
                return False

        # Scroll to ensure pagination is in view
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)

        # Look for the next button using exact classes
        next_button = page.query_selector(
            'button.artdeco-pagination__button--next.artdeco-button--muted'
        )

        if not next_button:
            print("Next button not found")
            return False

        # Check if button is disabled
        is_disabled = next_button.get_attribute('disabled')
        if is_disabled:
            print("Next button is disabled")
            return False

        # Click the button
        print("Clicking next button")
        next_button.click()

        # Wait for page state to update
        time.sleep(2)

        # Verify we moved to next page by checking page state again
        new_page_state = page.query_selector('.artdeco-pagination__page-state')
        if new_page_state:
            new_text = new_page_state.inner_text()
            print(f"New page state: {new_text}")

        return True

    except Exception as e:
        print(f"Error navigating to next page: {e}")
        page.screenshot(path="next_page_error.png")
        return False
