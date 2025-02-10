from genderize import Genderize

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