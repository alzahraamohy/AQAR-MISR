# Property and User classes
from datetime import datetime

# user class for auth
class User:
    def __init__(self, user_id, name, email, password_hash):
        # User Properties (constructor parameters)
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password_hash = password_hash  
        self.favorites = []              
        self.joined_at = datetime.now().isoformat()

    # Method 1-> Converts the User object to dict for JSON storage. because json.dump don't know
    # how to save objects, we need to convert it to dict first.
    # Converts the User object to a dictionary so it can be saved in a JSON file
    def to_dict(self):
        user_dictionary = {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "password_hash": self.password_hash,
            "favorites": self.favorites,
            "joined_at": self.joined_at,
        }
        return user_dictionary

    # Adds or removes a property ID from the user's favorites list
    def toggle_favorite(self, prop_id):
        if prop_id in self.favorites:
            self.favorites.remove(prop_id)
            return False
        else:
            self.favorites.append(prop_id)
            return True

    # Returns only the first name of the user for a cleaner look in the navbar
    def get_display_name(self):
        if self.name:
            name_parts = self.name.split()
            return name_parts[0]
        else:
            return "User"


# property class
class Property:
    def __init__(self, prop_id, title, price, area, prop_type,
                 bedrooms, bathrooms, image_url,
                 description="", why_choose=""):
        # Properties
        self.prop_id = prop_id
        self.title= title
        self.price = price
        self.area= area
        self.prop_type = prop_type
        self.bedrooms = bedrooms
        self.bathrooms = bathrooms
        self.image_url = image_url
        self.description = description
        self.why_choose = why_choose
        self.listed_at= datetime.now().isoformat()

    # Returns a short text summary of the property details
    def get_summary(self):
        summary_text = f"{self.bedrooms} bed {self.prop_type} in {self.area} for EGP {self.price:,}"
        return summary_text

    # Converts the Property object to a dictionary for JSON storage
    def to_dict(self):
        prop_dict = {
            "prop_id": self.prop_id,
            "title":  self.title,
            "price":self.price,
            "area": self.area,
            "prop_type":self.prop_type,
            "bedrooms":self.bedrooms,
            "bathrooms":self.bathrooms,
            "image_url":self.image_url,
            "description":self.description,
            "why_choose":self.why_choose,
            "listed_at":self.listed_at,
        }
        return prop_dict

    # Checks if this property matches the search filters provided by the user
    def matches_filter(self, area=None, prop_type=None, max_price=None):
        # Check if the area matches 
        if area:
            if self.area.lower() != area.lower():
                return False
        
        # Check if the property type matches
        if prop_type:
            if self.prop_type.lower() != prop_type.lower():
                return False
        
        # Check if the price is within the user's budget
        if max_price:
            if self.price > max_price:
                return False

        return True