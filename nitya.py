from playwright.sync_api import sync_playwright
import time
import pandas as pd
name_email_map = {}
import re
from genderize import Genderize
from openpyxl import load_workbook
import json

df = pd.DataFrame(columns=["Full Name", "First Name", "Recipient", "Company"])

def get_gender_from_name(name):
    try:
        gender = Genderize().get([name])[0]['gender']
        if gender == None:
            return "female"
        return gender
    except:
        return "female"

def login():
    email_field = page.wait_for_selector('//*[@id="session_key"]')
    email_field.fill("")
    password_field = page.wait_for_selector('//*[@id="session_password"]')
    password_field.fill("")
    sign_in = page.wait_for_selector('//*[@id="main-content"]/section[1]/div/div/form/div[2]/button')
    sign_in.click()
    
def search(searchText):
    search_field = page.wait_for_selector('//*[@id="global-nav-typeahead"]/input')
    search_field.fill(searchText)
    page.keyboard.press('Enter')
    time.sleep(2)
    #.search-reusables__primary-filter:nth-child(1)
    people_results = page.wait_for_selector('//*[@id="search-reusables__filters-bar"]/ul/li[1]/button')
    people_results.click()
    time.sleep(2)

def filter_recruiters():
    location_field = page.wait_for_selector('//*[@id="searchFilter_geoUrn"]')
    location_field.click()
    us_location = page.wait_for_selector('.t-14:has-text("United States")')
    us_location.click()    
    current_company_field = page.wait_for_selector('//*[@id="searchFilter_currentCompany"]')
    current_company_field.click()
    current_company_field = page.wait_for_selector('//*[@id="searchFilter_currentCompany"]')
    current_company_field.click()
    search_given_company = page.wait_for_selector('#hoverable-outlet-current-company-filter-value .search-basic-typeahead input')
    search_given_company.fill(company)
    time.sleep(2)
    current_company = page.wait_for_selector('#hoverable-outlet-current-company-filter-value .display-flex .t-14')
    current_company.click()
    select_company = page.wait_for_selector('//*[@id="searchFilter_geoUrn"]')
    select_company.click()   

def select_person(varsize):
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
    data = [[name, name.split()[0], email.lower(), company]]
    new_df = pd.DataFrame(data, columns=["Full Name", "First Name", "Recipient", "Company"])
    global df
    df = pd.concat([df, new_df], ignore_index=True)
    df.to_excel(excel_file_path)

def generate_fake_email(full_name):
    names = full_name.split()
    first_name = names[0]
    first_name = re.sub('\W+','', first_name)
    last_name = names[1]
    last_name = re.sub('\W+','', last_name)
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

    company = ""
    
    searchText = company + " technical recruiter" #change
    
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