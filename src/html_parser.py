from typing import List, Dict
from bs4 import BeautifulSoup


class HTMLProcessor:
    def __init__(self):
        self.selectors = {
            'container': 'div.presence-entity',
            'name': 'img[alt]',
            'title': '.entity-result__primary-subtitle'
        }

    def process_file(self, file_path: str) -> List[Dict[str, str]]:
        """Process a LinkedIn HTML file and extract recruiter information"""
        try:
            print(f"Processing HTML file: {file_path}")
            recruiters = []
            seen_names = set()  # To track duplicates

            # Read and parse the HTML file
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')

            # Find all presence-entity divs (profile containers)
            containers = soup.find_all('div', class_='presence-entity')
            print(f"Found {len(containers)} profile containers")

            for container in containers:
                # Get name from img alt attribute
                img = container.find('img')
                if img and img.get('alt'):
                    name = img.get('alt').strip()

                    # Skip if it's your own name or LinkedIn Member or we've seen it before
                    if (name != "LinkedIn Member" and
                            name != "Krishna Sarda" and
                            name not in seen_names):

                        # Get title by traversing up and finding subtitle
                        parent_container = container.find_parent('div', class_='entity-result__item')
                        title = ""
                        if parent_container:
                            title_elem = parent_container.find('div', class_='entity-result__primary-subtitle')
                            if title_elem:
                                title = title_elem.get_text(strip=True)

                        recruiter = {
                            'name': name,
                            'title': title
                        }
                        recruiters.append(recruiter)
                        seen_names.add(name)
                        print(f"Found person: {name} - {title}")

            print(f"Successfully extracted {len(recruiters)} unique recruiters")
            return recruiters

        except Exception as e:
            print(f"Error processing HTML file: {e}")
            return []


# Test code
if __name__ == "__main__":
    processor = HTMLProcessor()
    results = processor.process_file('./data/Recruiters/raw_technical_recruiter_page_1.html')

    if results:
        print("\nFound recruiters:")
        for r in results:
            print(f"- {r['name']}: {r['title']}")
    else:
        print("No recruiters found")