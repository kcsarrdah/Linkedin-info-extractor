import re


class NameCleaner:
    # Compile patterns on class initialization
    PATTERNS = {
        'status': re.compile(
            r'\s+(?:is hiring|is looking|is seeking|is recruiting|is actively hiring|is actively|is open|open to work|is open to work)$'),
        'credentials': re.compile(
            r',.*$|(?:\s+(?:PHD|PhD|MS|MBA|CPA|PMP|MSHR|AIRS-CDR|CPLP|CLC|CPTD|[A-Z]{2,}(?:\-[A-Z]+)?))(?:\s|$)'),
        'pronouns': re.compile(r'\s*\([^)]*\)'),
        # Only remove specific special characters we don't want
        'special_chars': re.compile(r'[!@#$%^&*+=<>?/:;"|\\{}\[\]~`]')
    }

    # Invalid names
    INVALID_NAMES = {'all things talent', 'talent acquisition', 'recruiter',
                     'recruiting', 'hr', 'human resources', 'talent', 'creator'}

    @staticmethod
    def clean_name(name: str) -> dict:
        """
        Clean name and split into components.
        Returns None if invalid, otherwise returns dict with name components
        """
        if not isinstance(name, str) or not name.strip():
            return None

        # Initial cleaning
        cleaned = name.strip()

        # Apply each cleaning pattern
        for pattern in NameCleaner.PATTERNS.values():
            cleaned = pattern.sub('', cleaned)

        # Clean up spaces
        cleaned = ' '.join(part for part in cleaned.split() if part)

        # Validate
        if not cleaned or cleaned.lower() in NameCleaner.INVALID_NAMES:
            return None

        # Split name parts
        parts = cleaned.split()
        if len(parts) == 1:
            return {
                'full_name': cleaned,
                'first_name': parts[0],
                'middle_name': '',
                'last_name': ''
            }
        elif len(parts) == 2:
            return {
                'full_name': cleaned,
                'first_name': parts[0],
                'middle_name': '',
                'last_name': parts[1]
            }
        else:
            return {
                'full_name': cleaned,
                'first_name': parts[0],
                'middle_name': parts[1],
                'last_name': ' '.join(parts[2:])
            }

    @staticmethod
    def clean_title(title: str) -> str:
        """Clean a title by removing repetitions and standardizing format"""
        if not isinstance(title, str):
            return ""

        title = title.strip()
        # Remove repetitive "3rd+"
        title = re.sub(r'(\b3rd\+\s*)+', '3rd+ ', title)
        # Remove common unnecessary suffixes
        title = re.sub(r'\b(career mentor|at work|looking|hiring|open|actively)\b.*$', '', title, flags=re.IGNORECASE)
        return title.strip()