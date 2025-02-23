import pytest
import pandas as pd
import os
from src.utils.NameCleaner import NameCleaner
import warnings
from datetime import datetime, UTC

# Filter out the specific DeprecationWarnings from openpyxl
warnings.filterwarnings('ignore', category=DeprecationWarning,
                        module='openpyxl.packaging.core')
warnings.filterwarnings('ignore', category=DeprecationWarning,
                        module='openpyxl.writer.excel')


def test_name_cleaning_from_excel():
    """Test name cleaning with real data from Excel file"""
    try:
        # Read the original Excel file
        input_file = "tests/data/excel/recruiters.xlsx"
        df = pd.read_excel(input_file)

        # Create name cleaner instance
        cleaner = NameCleaner()

        # Process each name and store results
        results = []
        for _, row in df.iterrows():
            cleaned = cleaner.clean_name(row['Full Name'])
            if cleaned:  # Only add if name is valid
                results.append({
                    'Original Name': row['Full Name'],
                    'Full Name': cleaned['full_name'],
                    'First Name': cleaned['first_name'],
                    'Middle Name': cleaned['middle_name'],
                    'Last Name': cleaned['last_name'],
                    'Last Updated': datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')
                })

        # Create new DataFrame with results
        results_df = pd.DataFrame(results)

        # Save to new Excel file
        output_dir = "tests/data/excel"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "cleaned_names.xlsx")

        # Save with modern datetime handling
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            results_df.to_excel(output_file, index=False)

        # Assertions
        assert len(results) > 0, "No names were processed"
        assert len(results) <= len(df), "More results than input names"
        assert all(r['Full Name'] for r in results), "Some names are empty"

    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")


def test_specific_cases():
    """Test specific edge cases"""
    cleaner = NameCleaner()
    test_cases = [
        ("Teju K is hiring", {
            'full_name': "Teju K",
            'first_name': "Teju",
            'middle_name': "",
            'last_name': "K"
        }),
        ("Kelly Pyper Trout", {
            'full_name': "Kelly Pyper Trout",
            'first_name': "Kelly",
            'middle_name': "Pyper",
            'last_name': "Trout"
        }),
        ("Ritika Jain, PHR, SHRM-CP", {
            'full_name': "Ritika Jain",
            'first_name': "Ritika",
            'middle_name': "",
            'last_name': "Jain"
        }),
        ("Creator", None),  # Should be filtered out
        ("Nitya Kohli (she/her)", {
            'full_name': "Nitya Kohli",
            'first_name': "Nitya",
            'middle_name': "",
            'last_name': "Kohli"
        }),
        ("Brigita Ujpál (Grbin)", {
            'full_name': "Brigita Ujpál",
            'first_name': "Brigita",
            'middle_name': "",
            'last_name': "Ujpál"
        }),
        ("Emilian Călina", {
            'full_name': "Emilian Călina",
            'first_name': "Emilian",
            'middle_name': "",
            'last_name': "Călina"
        }),
        ("José María García", {
            'full_name': "José María García",
            'first_name': "José",
            'middle_name': "María",
            'last_name': "García"
        })
    ]

    for input_name, expected in test_cases:
        result = cleaner.clean_name(input_name)
        assert result == expected, f"Failed for input: {input_name}"


if __name__ == "__main__":
    pytest.main([__file__, '-v'])