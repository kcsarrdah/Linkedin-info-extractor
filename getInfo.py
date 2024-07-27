from playwright.sync_api import sync_playwright
import time
import pandas as pd
name_email_map = {}
import re
from genderize import Genderize
from openpyxl import load_workbook
import json
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

linkedin_email = os.getenv("LINKEDIN_EMAIL")
linkedin_password = os.getenv("LINKEDIN_PASSWORD")

print(linkedin_email, linkedin_password)
df = pd.DataFrame(columns=["Full Name", "First Name", "Recipient", "Company"])

def get_gender_from_name(name):
    """
    Determines the gender of a person based on their first name using the Genderize API.
    Parameters:
    - name (str): The first name of the person.
    Returns:
    - str: The gender of the person ('male', 'female', or 'other'). Defaults to 'female' if gender cannot be determined or in case of an error.
    """
    try:
        gender = Genderize().get([name])[0]['gender']
        if gender == None:
            return "female"
        return gender
    except:
        return "female"

def login():
    global page
    try:
        print("Attempting to log in...")

        # Select "Sign in using email"
        email_sign_in = page.wait_for_selector('text="Sign in with email"', timeout=10000)
        email_sign_in.click()
        print("Selected 'Sign in using email'")

        # Wait for the next screen to load
        time.sleep(2)

        # Click on "Sign in" button on the home page
        sign_in_button = page.wait_for_selector('text="Sign in"', timeout=10000)
        sign_in_button.click()
        print("Clicked 'Sign in' button")

        # Wait for the email and password fields to be visible
        email_field = page.wait_for_selector('input[name="session_key"]', timeout=10000)
        print("Email field located")
        password_field = page.wait_for_selector('input[name="session_password"]', timeout=10000)
        print("Password field located")

        # Fill in email and password
        email_field.fill(linkedin_email)
        print("Filled email")
        password_field.fill(linkedin_password)
        print("Filled password")

        # Click the sign-in button
        sign_in = page.wait_for_selector('button[type="submit"]', timeout=10000)
        sign_in.click()
        print("Login submitted")

        # Add a wait to ensure login completes
        page.wait_for_selector('#global-nav-typeahead', timeout=10000)
        print("Login successful")
    except Exception as e:
        print(f"Login failed: {e}")

    
def search(searchText):
    """
    Performs a search on LinkedIn using the provided search text. It navigates to the search bar, enters the search query, and presses Enter to initiate the search. After the search, it selects the 'People' filter to narrow down results to individuals.
    Parameters:
    - searchText (str): The text to be searched on LinkedIn.
    """
    search_field = page.wait_for_selector('//*[@id="global-nav-typeahead"]/input')
    search_field.fill(searchText)
    page.keyboard.press('Enter')
    time.sleep(2)
    #.search-reusables__primary-filter:nth-child(1)
    people_results = page.wait_for_selector('//*[@id="search-reusables__filters-bar"]/ul/li[1]/button')
    people_results.click()
    time.sleep(2)

def filter_recruiters():
    global page
    try:
        print("Applying filters...")

        # Wait for and click on the location filter
        location_field = page.wait_for_selector('//*[@id="searchFilter_geoUrn"]', timeout=10000)
        location_field.click()
        print("Location field clicked")
        time.sleep(2)  # Add delay to ensure the location options are loaded

        # Wait for and select United States
        us_location = page.wait_for_selector('.t-14:has-text("United States")', timeout=10000)
        us_location.click()
        print("United States location selected")
        time.sleep(2)  # Ensure selection is processed

        # Click on "Show results" to apply the location filter within the dropdown
        location_dropdown = page.wait_for_selector('div.artdeco-hoverable-content--visible', timeout=10000)
        show_results_button = location_dropdown.query_selector('button:has-text("Show results")')
        show_results_button.click()
        print("Show results button clicked for location filter")
        page.wait_for_selector('div.search-results-container', timeout=10000)
        print("Results updated for location filter")

        time.sleep(5)  # Ensure results are updated before applying the next filter

        # Wait for and click on the current company filter
        current_company_field = page.wait_for_selector('//*[@id="searchFilter_currentCompany"]', timeout=10000)
        current_company_field.click()
        print("Current company filter clicked")
        time.sleep(2)  # Add delay to ensure the company options are loaded

        # Wait for and select the company
        search_given_company = page.wait_for_selector('#hoverable-outlet-current-company-filter-value .search-basic-typeahead input', timeout=10000)
        search_given_company.fill(company)
        print(f"Filled company: {company}")
        time.sleep(2)  # Ensure company suggestions are loaded

        # Check if the company appears in the suggestions
        current_company_suggestion = page.wait_for_selector('#hoverable-outlet-current-company-filter-value .basic-typeahead__selectable', timeout=10000)
        current_company_suggestion.click()
        print("Current company selected from suggestions")

        # Click on "Show results" to apply the current company filter within the dropdown
        company_dropdown = page.wait_for_selector('div.artdeco-hoverable-content--visible', timeout=10000)
        show_results_button = company_dropdown.query_selector('button:has-text("Show results")')
        show_results_button.click()
        print("Show results button clicked for company filter")
        page.wait_for_selector('div.search-results-container', timeout=10000)
        print("Results updated for company filter")

        time.sleep(5)  # Ensure results are updated before applying the next filter

        print("Filters applied and dropdown closed")

    except Exception as e:
        print(f"Filter application failed: {e}")

def select_person(varsize):
    """
    Selects people from the search results up to a specified number and generates fake email addresses for them. Each person's name and generated email are added to a global dictionary and saved to an Excel file.
    Parameters:
    - varsize (int): The maximum number of people to select.
    Returns:
    - bool: False if the maximum number of people has been reached or if navigating to the next page is not possible, True otherwise.
    """
    time.sleep(2)
    people = page.query_selector_all('.reusable-search__result-container .entity-result__title-text .app-aware-link :nth-child(1) :nth-child(1)')
    for p in people:
        if len(name_email_map)>=varsize:
            return False
        time.sleep(1)
        print(p.text_content())
        name = p.text_content()
        name_email_map[name] = generate_fake_email(name)
        appendAndSaveToExcel(name, name_email_map[name])
    return gotoNextPage()

def gotoNextPage():
    """
    Attempts to navigate to the next page of search results on LinkedIn.
    Returns:
    - bool: False if unable to navigate to the next page, True otherwise.
    """
    time.sleep(1)
    page.keyboard.press('PageDown')
    page.keyboard.press('PageDown')
    time.sleep(1)
    try:
        nextPage = page.wait_for_selector('.artdeco-pagination__button:nth-child(4) .artdeco-button__icon')
        nextPage.scroll_into_view_if_needed()
    except Exception as e:
        return False
    if not nextPage:
        print("returning false")
        return False
    nextPage.click()
    time.sleep(1)
    return True

def appendAndSaveToExcel(name, email):
    """
    Appends a new row with the person's name, first name, email, and company to the DataFrame and saves it to an Excel file.
    Parameters:
    - name (str): The full name of the person.
    - email (str): The email address of the person.
    """
    data = [[name, name.split()[0], email.lower(), company]]
    new_df = pd.DataFrame(data, columns=["Full Name", "First Name", "Recipient", "Company"])
    global df
    df = pd.concat([df, new_df], ignore_index=True)
    df.to_excel(excel_file_path)

def generate_fake_email(full_name):
    """
    Generates a fake email address for a given full name based on predefined patterns associated with the company.
    Parameters:
    - full_name (str): The full name of the person.
    Returns:
    - str: The generated fake email address.
    """
    names = full_name.split()
    first_name = names[0]
    first_name = re.sub(r'\W+', '', first_name)
    last_name = names[1]
    last_name = re.sub(r'\W+', '', last_name)
    first_initial = first_name[0].lower()
    last_name_parts = re.split(r'[,.\-s]+', last_name)
    last = " ".join(last_name_parts).lower()
    last = last.replace(" ","")  
    
    mailFormat = companyDict[company][1]
    type = companyDict[company][0]
    first = first_name
    if type == 1:
        fake_email = f"{first_initial}{last}{mailFormat}"
    if type == 2:
         fake_email = f"{first}{last}{mailFormat}"
    if type == 3:
         fake_email = f"{first}.{last}{mailFormat}" 
    if type == 4:
         fake_email = f"{first}{mailFormat}"
    if type == 5:
        fake_email = f"{first_initial}.{last}{mailFormat}"        
    if type == 6:
       fake_email = f"{first}_{last}{mailFormat}"     
    return fake_email

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto('https://linkedin.com')
    page.reload()
    time.sleep(1)
    
    with open('companies.txt') as f: 
        data = f.read() 
    companyDict = json.loads(data) 

    company = "DoorDash" #change
    searchText = company + " technical recruiter" #change
    searchTextEngineeringManager = company + " engineering manager" #change
    searchtextUniversityRecruiter = company + " university recruiter" #change
    
    login()
    search(searchText)
    filter_recruiters()
    time.sleep(2)
    excel_file_path = "./Recruiters/" + searchText + ".xlsx"
    df.to_excel(excel_file_path, index=False)

    varsize=150
    flag = True
    while len(name_email_map)<=varsize and flag:
        time.sleep(1)
        flag = select_person(varsize)