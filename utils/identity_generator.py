import random
import string
import itertools
from collections import defaultdict
import faker # Import faker here for seeding

class IdentityGenerator:
    def __init__(self):
        self.word_list = self.load_word_list()
        self.used_combinations = set()
        self.traversal_path = []
        self.fake = faker.Faker() # Initialize Faker here
        
    def set_seed(self, seed):
        """Set seed for reproducible identity generation."""
        random.seed(seed)
        faker.Faker.seed(seed)
        
    def load_word_list(self):
        """Load a comprehensive word list for username generation"""
        # In a real implementation, this would load from a file/API
        return [
            'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 
            'theta', 'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi',
            'omicron', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi',
            'chi', 'psi', 'omega', 'nexus', 'matrix', 'cyber', 'synth',
            'quantum', 'digital', 'fusion', 'vortex', 'zenith', 'nova',
            'echo', 'blaze', 'spark', 'glide', 'pulse', 'orbit', 'flux'
        ]
    
    def generate_username(self, min_length=8, num_count=2):
        """Generate username from word combinations with numbers and more realistic transformations."""
        while True:
            word_count = random.randint(1, 2) # Use 1-2 words for more common usernames
            words = random.sample(self.word_list, word_count)
            
            base = ''.join(words).lower()
            
            transformations = [
                lambda s: s, # No change
                lambda s: s.capitalize(), # Capitalize first letter
                lambda s: ''.join(w.capitalize() for w in words), # PascalCase
                lambda s: s.replace('a', '4').replace('e', '3').replace('i', '1').replace('o', '0').replace('s', '5'), # Leetspeak
                lambda s: f"{s}{random.choice(['_', '-'])}", # Add separator
                lambda s: f"{s}{self.fake.random_int(min=1, max=99)}" # Add small number suffix
            ]
            
            username = random.choice(transformations)(base)
            
            # Ensure numbers are added if num_count > 0
            if num_count > 0:
                numbers = ''.join(random.choices(string.digits, k=num_count))
                insert_pattern = random.choice([
                    lambda u, n: u + n,          # Suffix numbers (most common)
                    lambda u, n: u[:len(u)//2] + n + u[len(u)//2:],  # Middle insertion
                ])
                username = insert_pattern(username, numbers)
            
            # Ensure minimum length
            if len(username) < min_length:
                padding = ''.join(random.choices(string.ascii_lowercase, k=min_length-len(username)))
                username += padding
            
            # Remove spaces or special characters introduced by transformations if any
            username = ''.join(filter(str.isalnum, username))

            if username not in self.used_combinations:
                self.used_combinations.add(username)
                self.traversal_path.append(username)
                return username
    
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
        """Generate consistent identity profile"""
        identity = {
            'username': self.generate_username(),
            'password': self.generate_password(),
            'email': f"{self.generate_username()}@{self.fake.free_email_domain()}", # Use faker for email domain
            'first_name': self.fake.first_name(), # Use faker for more diverse names
            'last_name': self.fake.last_name() # Use faker for more diverse names
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
