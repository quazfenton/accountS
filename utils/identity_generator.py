import random
import string
import itertools
import json
import os
from collections import defaultdict
from pathlib import Path
import faker # Import faker here for seeding

class IdentityGenerator:
    def __init__(self):
        self.word_list = self.load_word_list()
        self.name_data = self.load_name_data()
        self.used_combinations = set()
        self.traversal_path = []
        self.fake = faker.Faker() # Initialize Faker here
        
    def set_seed(self, seed):
        """Set seed for reproducible identity generation."""
        random.seed(seed)
        faker.Faker.seed(seed)
        
    def load_name_data(self):
        """Load realistic name data from JSON file"""
        try:
            data_path = Path(__file__).parent.parent / "data" / "common_names.json"
            with open(data_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load name data: {e}")
            # Fallback to basic data
            return {
                "first_names": {
                    "male": ["John", "James", "Robert", "Michael", "David"],
                    "female": ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth"]
                },
                "last_names": ["Smith", "Johnson", "Williams", "Brown", "Jones"],
                "username_words": ["alpha", "beta", "gamma", "delta", "epsilon"],
                "adjectives": ["swift", "mighty", "brave", "clever", "wise"]
            }
    
    def load_word_list(self):
        """Load a comprehensive word list for username generation"""
        # Load from name data if available
        if hasattr(self, 'name_data') and self.name_data:
            return self.name_data.get('username_words', [])
        
        # Fallback to hardcoded list
        return [
            'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 
            'theta', 'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi',
            'omicron', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi',
            'chi', 'psi', 'omega', 'nexus', 'matrix', 'cyber', 'synth',
            'quantum', 'digital', 'fusion', 'vortex', 'zenith', 'nova',
            'echo', 'blaze', 'spark', 'glide', 'pulse', 'orbit', 'flux'
        ]
    
    def generate_realistic_name(self):
        """Generate a realistic first and last name"""
        gender = random.choice(['male', 'female'])
        first_name = random.choice(self.name_data['first_names'][gender])
        last_name = random.choice(self.name_data['last_names'])
        return first_name, last_name, gender
    
    def generate_username(self, min_length=8, num_count=2, style='mixed'):
        """Generate username with various realistic styles"""
        while True:
            if style == 'name_based':
                username = self._generate_name_based_username()
            elif style == 'word_based':
                username = self._generate_word_based_username()
            elif style == 'mixed':
                username = random.choice([
                    self._generate_name_based_username(),
                    self._generate_word_based_username()
                ])
            else:
                username = self._generate_word_based_username()
            
            # Apply common transformations
            username = self._apply_username_transformations(username, num_count)
            
            # Ensure minimum length
            if len(username) < min_length:
                padding = ''.join(random.choices(string.ascii_lowercase, k=min_length-len(username)))
                username += padding
            
            # Clean up and validate
            username = ''.join(c for c in username if c.isalnum() or c in '_-.')
            username = username[:20]  # Limit length for practicality
            
            if username and username not in self.used_combinations:
                self.used_combinations.add(username)
                self.traversal_path.append(username)
                return username
    
    def _generate_name_based_username(self):
        """Generate username based on realistic names"""
        first_name, last_name, _ = self.generate_realistic_name()
        
        patterns = [
            lambda f, l: f.lower() + l.lower(),
            lambda f, l: f.lower() + '_' + l.lower(),
            lambda f, l: f.lower() + '.' + l.lower(),
            lambda f, l: f[0].lower() + l.lower(),
            lambda f, l: f.lower() + l[0].lower(),
            lambda f, l: f.lower()[:3] + l.lower()[:3],
            lambda f, l: l.lower() + f[0].lower(),
            lambda f, l: f.lower() + l.lower()[:3]
        ]
        
        pattern = random.choice(patterns)
        return pattern(first_name, last_name)
    
    def _generate_word_based_username(self):
        """Generate username based on words and adjectives"""
        word_count = random.randint(1, 2)
        
        if word_count == 1:
            # Single word with possible adjective
            if random.random() < 0.4:  # 40% chance of adjective
                adjective = random.choice(self.name_data.get('adjectives', ['cool']))
                word = random.choice(self.word_list)
                base = adjective + word
            else:
                base = random.choice(self.word_list)
        else:
            # Two words
            words = random.sample(self.word_list, 2)
            base = ''.join(words)
        
        return base.lower()
    
    def _apply_username_transformations(self, username, num_count):
        """Apply various transformations to make username more realistic"""
        transformations = [
            lambda s: s,  # No change
            lambda s: s.capitalize(),  # Capitalize first letter
            lambda s: self._apply_leetspeak(s),  # Leetspeak
            lambda s: s + random.choice(['_', '-', '.']),  # Add separator
        ]
        
        # Apply random transformation
        username = random.choice(transformations)(username)
        
        # Add numbers if requested
        if num_count > 0:
            numbers = self._generate_realistic_numbers(num_count)
            insert_patterns = [
                lambda u, n: u + n,  # Suffix (most common)
                lambda u, n: n + u,  # Prefix
                lambda u, n: u + '_' + n,  # Underscore separator
                lambda u, n: u + '.' + n,  # Dot separator
            ]
            
            pattern = random.choice(insert_patterns)
            username = pattern(username, numbers)
        
        return username
    
    def _apply_leetspeak(self, text):
        """Apply leetspeak transformations selectively"""
        leet_map = {
            'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5',
            'A': '4', 'E': '3', 'I': '1', 'O': '0', 'S': '5'
        }
        
        # Only apply to some characters to keep it readable
        result = ""
        for char in text:
            if char in leet_map and random.random() < 0.3:  # 30% chance
                result += leet_map[char]
            else:
                result += char
        
        return result
    
    def _generate_realistic_numbers(self, count):
        """Generate realistic number patterns"""
        patterns = [
            lambda c: ''.join(random.choices(string.digits, k=c)),  # Random digits
            lambda c: str(random.randint(1980, 2005)),  # Birth year range
            lambda c: str(random.randint(1, 99)),  # Small numbers
            lambda c: str(random.randint(100, 999)),  # Medium numbers
        ]
        
        if count <= 2:
            return str(random.randint(1, 99))
        elif count <= 4:
            return random.choice([
                str(random.randint(1980, 2005)),  # Year
                str(random.randint(1000, 9999)),  # 4-digit number
                ''.join(random.choices(string.digits, k=count))
            ])
        else:
            return ''.join(random.choices(string.digits, k=count))
    
    def generate_password(self, length=12):
        """Generate strong password with required character types using advanced techniques."""
        # Ensure minimum requirements are met
        min_uppercase = 1
        min_lowercase = 1
        min_digits = 1
        min_specials = 1
        
        # Generate characters for each type
        password_chars = []
        password_chars.extend(random.choices(string.ascii_uppercase, k=min_uppercase))
        password_chars.extend(random.choices(string.ascii_lowercase, k=min_lowercase))
        password_chars.extend(random.choices(string.digits, k=min_digits))
        password_chars.extend(random.choices('!@#$%^&*', k=min_specials))
        
        # Fill the rest of the length with random characters
        all_chars = string.ascii_letters + string.digits + '!@#$%^&*'
        remaining_length = length - len(password_chars)
        password_chars.extend(random.choices(all_chars, k=remaining_length))
        
        random.shuffle(password_chars)
        password = ''.join(password_chars)
        
        # Apply more sophisticated transformations (e.g., common substitutions)
        transformations = [
            lambda s: s,
            lambda s: s.replace('a', '@').replace('A', '4').replace('e', '3').replace('E', '3').replace('i', '1').replace('I', '1').replace('o', '0').replace('O', '0').replace('s', '5').replace('S', '5'),
            lambda s: ''.join(c.upper() if random.random() < 0.2 else c for c in s), # Random casing
            lambda s: ''.join(c if random.random() > 0.1 else random.choice('!@#$%^&*') for c in s) # Random special char insertion
        ]
        
        password = random.choice(transformations)(password)
        
        # Ensure final password meets length and character type requirements after transformations
        if (len(password) >= length and
            any(c.isupper() for c in password) and
            any(c.islower() for c in password) and
            any(c.isdigit() for c in password) and
            any(c in '!@#$%^&*' for c in password)):
            return password
        else:
            # If transformations broke requirements, regenerate (simple retry)
            return self.generate_password(length)
    
    def generate_identity(self):
        """Generate consistent identity profile with realistic names"""
        # Generate realistic name first
        first_name, last_name, gender = self.generate_realistic_name()
        
        # Generate username that might be based on the name
        username = self.generate_username(style='mixed')
        
        # Generate email with realistic domain
        email_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com']
        email_username = random.choice([
            username,
            self._generate_name_based_username(),
            first_name.lower() + last_name.lower()[:3],
            first_name.lower() + str(random.randint(1, 999))
        ])
        email = f"{email_username}@{random.choice(email_domains)}"
        
        identity = {
            'username': username,
            'password': self.generate_password(),
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'gender': gender,
            'province': self.fake.state()
        }
        return identity
    
    def traverse_namespace(self, base_profile, profile_manager, depth=5, variation_strength='medium'):
        """Traverse through identity space using BFS-like approach, generating related profiles."""
        identity_graph = defaultdict(list)
        queue = [base_profile]
        visited_usernames = set()
        self.traversal_path = [] # Reset traversal path for each call
        
        while queue and len(visited_usernames) < depth:
            current_profile = queue.pop(0)
            current_username = current_profile['basic']['username']
            
            if current_username in visited_usernames:
                continue
                
            visited_usernames.add(current_username)
            self.traversal_path.append(current_username)
            
            # Generate related identities (children in traversal) using ProfileManager's variations
            # Generate 1 to 3 variations per node
            num_variations = random.randint(1, 3) 
            new_profiles = profile_manager.generate_profile_variations(
                current_profile, 
                count=num_variations, 
                variation_strength=variation_strength
            )
            
            for new_profile in new_profiles:
                new_username = new_profile['basic']['username']
                if new_username not in visited_usernames:
                    identity_graph[current_username].append(new_username)
                    queue.append(new_profile)
        
        return identity_graph, self.traversal_path
    
    def generate_name_variations(self, base_name, count=5):
        """Generate variations of a base name using more sophisticated techniques."""
        variations = []
        for i in range(count):
            strategy = random.choice([
                'add_numbers', 'camel_case', 'leet_speak', 'swap_chars', 'add_separator'
            ])
            
            if strategy == 'add_numbers':
                variations.append(f"{base_name}{random.randint(10,999)}")
            elif strategy == 'camel_case':
                parts = base_name.split()
                variations.append(''.join(p.capitalize() for p in parts))
            elif strategy == 'leet_speak':
                leet_map = {'a':'4', 'e':'3', 'i':'1', 'o':'0', 's':'5'}
                variations.append(''.join(leet_map.get(c.lower(), c) for c in base_name))
            elif strategy == 'swap_chars':
                name_list = list(base_name)
                if len(name_list) > 1:
                    idx1, idx2 = random.sample(range(len(name_list)), 2)
                    name_list[idx1], name_list[idx2] = name_list[idx2], name_list[idx1]
                variations.append(''.join(name_list))
            elif strategy == 'add_separator':
                separator = random.choice(['_', '-', '.'])
                insert_pos = random.randint(1, len(base_name) - 1)
                variations.append(f"{base_name[:insert_pos]}{separator}{base_name[insert_pos:]}")
        
        # Ensure uniqueness for variations
        unique_variations = list(set(variations))
        # If not enough unique variations, generate more simple ones
        while len(unique_variations) < count:
            unique_variations.append(f"{base_name}{random.randint(1000,9999)}")
            unique_variations = list(set(unique_variations))
            
        return unique_variations[:count]
