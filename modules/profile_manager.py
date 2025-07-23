import random
import faker
from datetime import datetime, timedelta
from ..utils.identity_generator import IdentityGenerator

class ProfileManager:
    def __init__(self):
        self.fake = faker.Faker()
        self.identity_gen = IdentityGenerator()
        self.countries = ['US', 'UK', 'CA', 'AU', 'DE', 'FR']
        self.timezones = ['America/New_York', 'Europe/London', 'Australia/Sydney', 
                          'Europe/Paris', 'Asia/Tokyo', 'America/Los_Angeles']
    
    def generate_birthdate(self, min_age=18, max_age=65, base_date=None, year_offset=0):
        """Generate realistic birthdate within age range, with optional offset from a base date."""
        if base_date:
            # Adjust base_date by year_offset
            adjusted_year = base_date.year + year_offset
            # Ensure the adjusted year is within a reasonable range for datetime
            adjusted_year = max(1900, min(datetime.now().year, adjusted_year))
            base_date = base_date.replace(year=adjusted_year)
            
            # Generate a date around the base_date, within a small window
            start_date = base_date - timedelta(days=365)
            end_date = base_date + timedelta(days=365)
            return self.fake.date_between_dates(start_date, end_date)
        else:
            end_date = datetime.now() - timedelta(days=min_age*365)
            start_date = end_date - timedelta(days=(max_age-min_age)*365)
            return self.fake.date_between_dates(start_date, end_date)
    
    def generate_address(self, country_code='US', base_address=None, proximity_level='city'):
        """Generate realistic address for specified country, with optional proximity to a base address."""
        if base_address and proximity_level == 'city':
            # Attempt to generate an address in the same city or a nearby one
            return {
                'street': self.fake.street_address(),
                'city': base_address['city'], # Keep same city for high proximity
                'state': base_address['state'],
                'zip_code': self.fake.zipcode(), # New zipcode within same city
                'country': country_code
            }
        elif base_address and proximity_level == 'state':
            # Generate an address in the same state/province but a different city
            return {
                'street': self.fake.street_address(),
                'city': self.fake.city(),
                'state': base_address['state'],
                'zip_code': self.fake.zipcode(),
                'country': country_code
            }
        else:
            return {
                'street': self.fake.street_address(),
                'city': self.fake.city(),
                'state': self.fake.state() if country_code == 'US' else self.fake.province(),
                'zip_code': self.fake.zipcode(),
                'country': country_code
            }
    
    def generate_phone(self, country_code='US', base_phone=None, digit_change_prob=0.2):
        """Generate phone number with country code, with optional slight variations from a base phone."""
        if base_phone:
            # Introduce slight variations to the base phone number
            phone_digits = list(base_phone.replace('+', '').replace('-', '').replace(' ', ''))
            for i in range(len(phone_digits)):
                if random.random() < digit_change_prob:
                    phone_digits[i] = str(random.randint(0, 9))
            return f"+{phone_digits[0]}{''.join(phone_digits[1:])}" # Assuming first digit is country code
        elif country_code == 'US':
            return f"+1{self.fake.phone_number()[1:].replace('-', '')}"
        elif country_code == 'UK':
            return f"+44{self.fake.phone_number()[1:].replace(' ', '')}"
        else:
            return f"+{random.randint(1, 99)}{self.fake.phone_number().replace(' ', '').replace('-', '')}"
    
    def generate_security_question_variation(self, base_question):
        """Generate a semantically similar but syntactically different security question."""
        keywords = base_question.lower().split()
        if "pet's name" in base_question:
            return random.choice([
                f"What was the name of your first pet? {self.fake.first_name()}",
                f"Your first pet's name? {self.fake.first_name()}",
                f"Name of your childhood pet? {self.fake.first_name()}"
            ])
        elif "street" in base_question and "grow up" in base_question:
            return random.choice([
                f"What was the name of the street you grew up on? {self.fake.street_name()}",
                f"The street you lived on as a child? {self.fake.street_name()}",
                f"Your childhood street name? {self.fake.street_name()}"
            ])
        return self.fake.sentence() # Fallback for unknown patterns
    
    def generate_full_profile(self, seed=None):
        """Generate comprehensive identity profile with realistic details.
        
        Args:
            seed (int, optional): Seed for reproducible profile generation. Defaults to None.
        """
        if seed is not None:
            faker.Faker.seed(seed)
            random.seed(seed)
            self.identity_gen.set_seed(seed)

        identity = self.identity_gen.generate_identity()
        country = random.choice(self.countries)
        
        return {
            'basic': identity,
            'personal': {
                'birthdate': self.generate_birthdate(),
                'gender': random.choice(['Male', 'Female', 'Non-binary']),
                'nationality': country
            },
            'contact': {
                'phone': self.generate_phone(country),
                'address': self.generate_address(country),
                'timezone': random.choice(self.timezones)
            },
            'digital': {
                'security_question1': self.generate_security_question_variation(f"What was your first pet's name? {self.fake.first_name()}"),
                'security_question2': self.generate_security_question_variation(f"What street did you grow up on? {self.fake.street_name()}"),
                'recovery_email': f"recovery_{identity['email']}"
            }
        }
    
    def generate_profile_variations(self, base_profile, count=3, variation_strength='medium'):
        """Generate variations of a base profile for identity traversal.
        
        Args:
            base_profile (dict): The base profile to generate variations from.
            count (int): Number of variations to generate.
            variation_strength (str): 'low', 'medium', or 'high' to control the degree of variation.
        """
        variations = []
        for i in range(count):
            # Use a new seed for each variation based on the base profile's hash and iteration
            variation_seed = hash(frozenset(base_profile['basic'].items())) + i
            faker.Faker.seed(variation_seed)
            random.seed(variation_seed)
            self.identity_gen.set_seed(variation_seed)

            variation = base_profile.copy()
            
            # Modify basic information
            variation['basic']['first_name'] = self.fake.first_name()
            variation['basic']['last_name'] = self.fake.last_name()
            variation['basic']['username'] = self.identity_gen.generate_name_variations(
                base_profile['basic']['username'], 1
            )[0]
            variation['basic']['email'] = f"{variation['basic']['username']}@{self.fake.free_email_domain()}"
            
            # Modify personal information
            year_offset = 0
            if variation_strength == 'low':
                year_offset = random.randint(-1, 1)
            elif variation_strength == 'medium':
                year_offset = random.randint(-3, 3)
            elif variation_strength == 'high':
                year_offset = random.randint(-7, 7)
            
            variation['personal']['birthdate'] = self.generate_birthdate(
                base_date=base_profile['personal']['birthdate'],
                year_offset=year_offset
            )
            variation['personal']['gender'] = random.choice(['Male', 'Female', 'Non-binary']) # Randomize gender
            
            # Modify contact information
            phone_digit_change_prob = 0.0
            address_proximity = 'city'
            if variation_strength == 'low':
                phone_digit_change_prob = 0.1
                address_proximity = 'city'
            elif variation_strength == 'medium':
                phone_digit_change_prob = 0.3
                address_proximity = 'state'
            elif variation_strength == 'high':
                phone_digit_change_prob = 0.5
                address_proximity = 'country' # Completely new address
            
            variation['contact']['phone'] = self.generate_phone(
                base_profile['personal']['nationality'],
                base_phone=base_profile['contact']['phone'],
                digit_change_prob=phone_digit_change_prob
            )
            variation['contact']['address'] = self.generate_address(
                base_profile['personal']['nationality'],
                base_address=base_profile['contact']['address'],
                proximity_level=address_proximity
            )
            variation['contact']['timezone'] = random.choice(self.timezones) # Randomize timezone
            
            # Modify digital information
            variation['digital']['security_question1'] = self.generate_security_question_variation(
                base_profile['digital']['security_question1']
            )
            variation['digital']['security_question2'] = self.generate_security_question_variation(
                base_profile['digital']['security_question2']
            )
            variation['digital']['recovery_email'] = f"recovery_{variation['basic']['username']}@{self.fake.free_email_domain()}"
            
            variations.append(variation)
        
        return variations
