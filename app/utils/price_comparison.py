import sys
import os
import json
import time
import subprocess
from datetime import datetime
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('price_comparison.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class PriceComparison:
    def __init__(self):
        self.citilink_products = []
        self.dns_products = []
        self.comparison_results = []
        
        # Get directory paths
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.citilink_parser_dir = os.path.join(self.current_dir, 'Citi_parser')
        self.dns_parser_dir = os.path.join(self.current_dir, 'DNS_parsing')
    
    def load_citilink_data(self, category):
        """Load Citilink product data by running the parser for a specific category"""
        try:
            # First check if we have category-specific data
            if category:
                category_products_file = os.path.join(self.citilink_parser_dir, 'data', category, 'Товары.json')
                if os.path.exists(category_products_file):
                    try:
                        logging.info(f"Trying to load category-specific data for: {category}")
                        with open(category_products_file, 'r', encoding='utf-8') as f:
                            try:
                                content = f.read()
                                # Remove the trailing comma if it exists
                                if content.endswith(',\n]'):
                                    content = content.replace(',\n]', '\n]')
                                self.citilink_products = json.loads(content)
                                logging.info(f"Loaded {len(self.citilink_products)} products from category-specific file: {category}")
                                return self.citilink_products
                            except json.JSONDecodeError as e:
                                logging.error(f"JSON decode error when loading category data: {str(e)}")
                    except Exception as e:
                        logging.error(f"Error loading category-specific data: {str(e)}")

            # If no category-specific data found, try loading from the main file
            try:
                # First try to load existing data without running the parser
                logging.info(f"Trying to load existing Citilink data for category: {category}")
                with open(os.path.join(self.citilink_parser_dir, 'Товары.json'), 'r', encoding='utf-8') as f:
                    try:
                        content = f.read()
                        # Remove the trailing comma if it exists
                        if content.endswith(',\n]'):
                            content = content.replace(',\n]', '\n]')
                        self.citilink_products = json.loads(content)
                        logging.info(f"Loaded {len(self.citilink_products)} existing products from Citilink")
                        
                        # If we have products and don't need to filter by category, return immediately
                        if not category or category == '':
                            return self.citilink_products
                    except json.JSONDecodeError as e:
                        logging.error(f"JSON decode error when loading existing data: {str(e)}")
            except Exception as e:
                logging.error(f"Error loading existing Citilink data: {str(e)}")
            
            # If we don't have existing data, run the parser for the specified category
            # Set environment variable for Citilink parser
            os.environ['CATEGORY'] = category
            
            # Change to Citilink parser directory
            os.chdir(self.citilink_parser_dir)
            
            # Run the Citilink parser as a subprocess
            logging.info(f"Running Citilink parser for category: {category}")
            process = subprocess.Popen(['python', 'main.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if stderr:
                stderr_text = stderr.decode('utf-8', errors='replace')
                logging.error(f"Citilink parser error: {stderr_text}")
            
            if stdout:
                stdout_text = stdout.decode('utf-8', errors='replace')
                logging.info(f"Citilink parser output: {stdout_text}")
            
            # Change back to original directory
            os.chdir(self.current_dir)
            
            # Check for category-specific data first
            if category:
                category_products_file = os.path.join(self.citilink_parser_dir, 'data', category, 'Товары.json')
                if os.path.exists(category_products_file):
                    try:
                        with open(category_products_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Handle potential JSON format issues
                            if content.endswith(',\n]'):
                                content = content.replace(',\n]', '\n]')
                            self.citilink_products = json.loads(content)
                            logging.info(f"Loaded {len(self.citilink_products)} products from category-specific file after parsing")
                            return self.citilink_products
                    except Exception as e:
                        logging.error(f"Error reading category-specific parser results: {str(e)}")
            
            # Fall back to the main file
            # Read the results from the JSON file
            try:
                with open(os.path.join(self.citilink_parser_dir, 'Товары.json'), 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Handle potential JSON format issues
                    if content.endswith(',\n]'):
                        content = content.replace(',\n]', '\n]')
                    self.citilink_products = json.loads(content)
                    logging.info(f"Loaded {len(self.citilink_products)} products from Citilink")
            except Exception as e:
                logging.error(f"Error reading Citilink parser results: {str(e)}")
                self.citilink_products = []
            
            return self.citilink_products
        except Exception as e:
            logging.error(f"Error in load_citilink_data: {str(e)}")
            self.citilink_products = []
            return self.citilink_products
    
    def load_dns_data(self, category_name=None):
        """
        Load DNS product data by running the parser
        category_name: Optional category name to filter results
        """
        try:
            # First try to load existing data without running the parser
            try:
                logging.info(f"Trying to load existing DNS data" + (f" for category: {category_name}" if category_name else ""))
                with open(os.path.join(self.dns_parser_dir, 'product_data.json'), 'r', encoding='utf-8') as f:
                    self.dns_products = json.load(f)
                    logging.info(f"Loaded {len(self.dns_products)} existing products from DNS")
                    
                    # Filter by category if specified
                    if category_name:
                        filtered_products = []
                        for product in self.dns_products:
                            # Check if product has a category and if it matches the desired category
                            if 'category' in product and category_name.lower() in product['category'].lower():
                                filtered_products.append(product)
                            # Additional check for video cards that might have "Видеокарта" in the name
                            elif category_name.lower() == 'видеокарты' and 'name' in product and 'видеокарта' in product['name'].lower():
                                filtered_products.append(product)
                        
                        if filtered_products:
                            self.dns_products = filtered_products
                            logging.info(f"Filtered to {len(self.dns_products)} products from category {category_name}")
                            
                            # Log the first product after filtering
                            if len(self.dns_products) > 0:
                                logging.info(f"First DNS product after filtering: {self.dns_products[0].get('name', 'No name')}")
                        else:
                            logging.warning(f"No products found for category {category_name} after filtering")
                        
                    return self.dns_products
            except Exception as e:
                logging.error(f"Error loading existing DNS data: {str(e)}")
            
            # Change to DNS parser directory
            os.chdir(self.dns_parser_dir)
            
            # Run the DNS parser as a subprocess - no need to modify any files since
            # categories are already in categories.json
            logging.info(f"Running DNS parser")
            process = subprocess.Popen(['python', 'main.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if stderr:
                logging.error(f"DNS parser error: {stderr.decode('utf-8')}")
            
            # Read the generated JSON file
            with open('product_data.json', 'r', encoding='utf-8') as f:
                self.dns_products = json.load(f)
            
            # Filter by category if specified
            if category_name:
                filtered_products = []
                for product in self.dns_products:
                    if 'category' in product and category_name.lower() in product['category'].lower():
                        filtered_products.append(product)
                
                if filtered_products:
                    self.dns_products = filtered_products
                    logging.info(f"Filtered to {len(self.dns_products)} products from category {category_name}")
            
            logging.info(f"Loaded {len(self.dns_products)} products from DNS")
            
            # Change back to original directory
            os.chdir(self.current_dir)
            
            return self.dns_products
        except Exception as e:
            logging.error(f"Error loading DNS data: {str(e)}")
            # Change back to original directory in case of error
            os.chdir(self.current_dir)
            return []
    
    def get_available_dns_categories(self):
        """Get a list of categories available from the DNS parser"""
        try:
            # Change to DNS parser directory
            os.chdir(self.dns_parser_dir)
            
            # Check if categories.json exists
            if os.path.exists('categories.json'):
                with open('categories.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Transform the complex category structure into a simple list
                categories = []
                
                # Parse the complex structure
                for item in data:
                    if 'categories' in item:
                        for category_key, category_data in item['categories'].items():
                            # Map technical names to human-readable names
                            category_names = {
                                'videokarty': 'Видеокарты',
                                'processory': 'Процессоры',
                                'materinskie-platy': 'Материнские платы',
                                'operativnaya-pamyat': 'Оперативная память',
                                'bloki-pitaniya': 'Блоки питания',
                                'kulery': 'Кулеры',
                                'zhestkie-diski': 'Жесткие диски',
                                'ssd-m2': 'SSD накопители',
                                'korpusa': 'Корпуса'
                            }
                            
                            # Get human-readable name or use the key if not found
                            name = category_names.get(category_key, category_key.replace('-', ' ').title())
                            categories.append({"name": name})
                
                # If no categories were found in the complex structure, use defaults
                if not categories:
                    categories = [
                        {"name": "Видеокарты"},
                        {"name": "Процессоры"},
                        {"name": "Материнские платы"},
                        {"name": "Оперативная память"},
                        {"name": "Блоки питания"},
                        {"name": "Кулеры"},
                        {"name": "Жесткие диски"},
                        {"name": "SSD накопители"},
                        {"name": "Корпуса"}
                    ]
                    
                # Change back to original directory
                os.chdir(self.current_dir)
                
                return categories
            else:
                logging.warning("categories.json not found in DNS parser directory")
                # Return default categories
                categories = [
                    {"name": "Видеокарты"},
                    {"name": "Процессоры"},
                    {"name": "Материнские платы"},
                    {"name": "Оперативная память"},
                    {"name": "Блоки питания"},
                    {"name": "Кулеры"},
                    {"name": "Жесткие диски"},
                    {"name": "SSD накопители"},
                    {"name": "Корпуса"}
                ]
                # Change back to original directory
                os.chdir(self.current_dir)
                return categories
                
        except Exception as e:
            logging.error(f"Error loading DNS categories: {str(e)}")
            # Change back to original directory in case of error
            os.chdir(self.current_dir)
            # Return default categories
            return [
                {"name": "Видеокарты"},
                {"name": "Процессоры"},
                {"name": "Материнские платы"},
                {"name": "Оперативная память"},
                {"name": "Блоки питания"},
                {"name": "Кулеры"},
                {"name": "Жесткие диски"},
                {"name": "SSD накопители"},
                {"name": "Корпуса"}
            ]
    
    def find_matching_products(self):
        """Find matching products between Citilink and DNS based on name similarity"""
        self.comparison_results = []
        
        if not self.citilink_products or not self.dns_products:
            logging.warning("Cannot compare products: data not loaded")
            logging.warning(f"Citilink products: {len(self.citilink_products)}, DNS products: {len(self.dns_products)}")
            return []
            
        logging.info("Starting product comparison...")
        logging.info(f"Analyzing {len(self.citilink_products)} products from Citilink and {len(self.dns_products)} products from DNS")
        
        # Log sample of products for debugging
        for i in range(min(3, len(self.citilink_products))):
            logging.info(f"Citilink product {i+1}: {self.citilink_products[i].get('name', 'No name')}")
        for i in range(min(3, len(self.dns_products))):
            logging.info(f"DNS product {i+1}: {self.dns_products[i].get('name', 'No name')}")
        
        matched_count = 0
        
        # This is a simple comparison approach based on product name
        # A more sophisticated approach would use text similarity algorithms
        for citi_product in self.citilink_products:
            # Use name field from Citilink products
            citi_name = citi_product.get('name', '').lower()
            if not citi_name:
                continue
                
            # Skip products with very short names
            if len(citi_name) < 5:
                continue
            
            # Extract key product identifiers
            citi_model = self._extract_model_number(citi_name)
            if citi_model:
                logging.debug(f"Extracted model number from Citilink product: {citi_model}")
                
            # For each Citilink product, find the best matching DNS product
            best_match = None
            best_score = 0
            
            for dns_product in self.dns_products:
                dns_name = dns_product.get('name', '').lower()
                if not dns_name:
                    continue
                
                # Extract key product identifiers from DNS product
                dns_model = self._extract_model_number(dns_name)
                
                # Calculate similarity score
                similarity_score = self._calculate_similarity(citi_name, dns_name, citi_model, dns_model)
                
                # Keep track of the best match
                if similarity_score > best_score:
                    best_score = similarity_score
                    best_match = dns_product
            
            # If we found a good match
            if best_match and best_score >= 0.5:  # Increased threshold for better accuracy
                matched_count += 1
                dns_name = best_match.get('name', '').lower()
                logging.info(f"Found match: {citi_name} <==> {dns_name} (score: {best_score:.2f})")
                
                # Extract prices
                citi_price = float(citi_product.get('price', 0) or 0)
                dns_price = float(best_match.get('price_discounted', 0) or best_match.get('price_original', 0) or 0)
                
                # Skip if either price is 0
                if citi_price == 0 or dns_price == 0:
                    continue
                
                # Calculate price difference
                price_diff = citi_price - dns_price
                price_diff_percent = (price_diff / dns_price) * 100 if dns_price > 0 else 0
                
                # Get product categories
                citi_category = ''
                if citi_product.get('categories') and len(citi_product['categories']) > 1:
                    citi_category = citi_product['categories'][1].get('name', '')
                
                dns_category = best_match.get('category', '')
                
                # Get ratings if available
                citi_rating = citi_product.get('rating', {})
                if isinstance(citi_rating, dict):
                    citi_rating_value = citi_rating.get('value', 0)
                else:
                    citi_rating_value = 0
                    
                dns_rating = best_match.get('rating', 0)
                
                # Create a more descriptive name for the product
                display_name = citi_name
                if citi_model and citi_model.lower() in citi_name.lower():
                    # If the model number is in the name, it's usually a good identifier
                    cleaned_name = self._clean_product_name(citi_name)
                    display_name = cleaned_name.title()
                
                self.comparison_results.append({
                    'name': display_name,
                    'citilink_price': citi_price,
                    'dns_price': dns_price,
                    'price_difference': price_diff,
                    'price_difference_percent': price_diff_percent,
                    'citilink_url': citi_product.get('url', ''),
                    'dns_url': best_match.get('url', ''),
                    'citilink_id': citi_product.get('id', ''),
                    'dns_id': best_match.get('id', ''),
                    'citilink_category': citi_category,
                    'dns_category': dns_category,
                    'model_number': citi_model or dns_model,
                    'similarity_score': best_score,
                    'citilink_rating': citi_rating_value,
                    'dns_rating': dns_rating
                })
        
        logging.info(f"Matched {matched_count} products from different stores")
        
        # Sort by price difference percent by default
        self.comparison_results.sort(key=lambda x: abs(x['price_difference_percent']), reverse=True)
        
        logging.info(f"Found {len(self.comparison_results)} matching products with valid prices")
        return self.comparison_results
    
    def _calculate_similarity(self, name1, name2, model1=None, model2=None):
        """Calculate similarity score between two product names"""
        # Start with a base score
        score = 0.0
        
        # If both have model numbers and they match, high score
        if model1 and model2:
            if model1.lower() == model2.lower():
                score += 0.9  # Exact model match is very strong evidence
            elif len(model1) >= 5 and model1.lower() in model2.lower():
                score += 0.7
            elif len(model2) >= 5 and model2.lower() in model1.lower():
                score += 0.7
        
        # Extract key product identifiers - GPU models and CPU models
        # For RTX/GTX series and other GPU types
        gpu_patterns = [
            r'((?:rtx|gtx)\s*\d{4}\s*(?:ti|super)?)', # NVIDIA cards
            r'(rx\s*\d{4}\s*(?:xt)?)', # AMD cards
            r'(arc\s*\w+\s*\d+)' # Intel Arc cards
        ]
        
        for pattern in gpu_patterns:
            match1 = re.search(pattern, name1, re.IGNORECASE)
            match2 = re.search(pattern, name2, re.IGNORECASE)
            
            if match1 and match2:
                gpu1 = match1.group(1).lower().replace(' ', '')
                gpu2 = match2.group(1).lower().replace(' ', '')
                if gpu1 == gpu2:
                    score += 0.6
                    break
                
        # For CPU models (Intel Core i5/i7/i9, AMD Ryzen)
        cpu_patterns = [
            r'(i\d-\d{4,5}[a-z]*)', # Intel Core
            r'(ryzen\s*\d\s*\d{4}[a-z]*)', # AMD Ryzen
        ]
        
        for pattern in cpu_patterns:
            match1 = re.search(pattern, name1, re.IGNORECASE)
            match2 = re.search(pattern, name2, re.IGNORECASE)
            
            if match1 and match2:
                cpu1 = match1.group(1).lower().replace(' ', '')
                cpu2 = match2.group(1).lower().replace(' ', '')
                if cpu1 == cpu2:
                    score += 0.6
                    break
        
        # Manufacturer match gives a bonus
        manufacturers = ['gigabyte', 'asus', 'msi', 'palit', 'gainward', 'evga', 'zotac', 
                       'sapphire', 'asrock', 'inno3d', 'pny', 'amd', 'intel', 'nvidia']
        
        for mfr in manufacturers:
            if mfr in name1.lower() and mfr in name2.lower():
                score += 0.2
                break
                
        # Memory size match for GPUs/RAM (e.g., 8GB, 16GB)
        mem_match1 = re.search(r'(\d+)\s*(?:gb|гб)', name1, re.IGNORECASE)
        mem_match2 = re.search(r'(\d+)\s*(?:gb|гб)', name2, re.IGNORECASE)
        
        if mem_match1 and mem_match2 and mem_match1.group(1) == mem_match2.group(1):
            score += 0.2
        
        # Clean and compare names
        clean_name1 = self._clean_product_name(name1)
        clean_name2 = self._clean_product_name(name2)
        
        # Convert both names to lowercase and split into words
        words1 = set(clean_name1.lower().split())
        words2 = set(clean_name2.lower().split())
        
        # Calculate word overlap
        common_words = words1.intersection(words2)
        
        # Calculate overlap score
        min_name_len = min(len(words1), len(words2))
        if min_name_len > 0:
            overlap_ratio = len(common_words) / min_name_len
            score += overlap_ratio * 0.3
        
        # Bonus for having multiple common words
        if len(common_words) >= 3:
            score += 0.1
        if len(common_words) >= 5:
            score += 0.2
        
        return score
    
    def _extract_model_number(self, name):
        """Extract model number from a product name, usually in square brackets"""
        # Look for text in square brackets that might be a model number
        bracket_match = re.search(r'\[(.*?)\]', name)
        if bracket_match:
            model = bracket_match.group(1).strip()
            # Normalize model number format (remove spaces, convert to lowercase)
            model = re.sub(r'\s+', '', model).lower()
            return model
        
        # Look for text in parentheses
        paren_match = re.search(r'\((.*?)\)', name)
        if paren_match:
            model = paren_match.group(1).strip()
            # If it looks like a model number (contains digits and letters)
            if re.search(r'[a-z].*\d|\d.*[a-z]', model, re.IGNORECASE):
                return model.lower().replace(' ', '')
        
        # Special case for RTX/GTX series - look for common patterns
        rtx_match = re.search(r'(rtx\s*\d{4}\s*(?:ti|super)?)', name, re.IGNORECASE)
        if rtx_match:
            model = rtx_match.group(1).strip()
            return model
            
        # Look for patterns that look like model numbers (alphanumeric with dashes)
        model_match = re.search(r'([a-zA-Z0-9]+-[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*)', name)
        if model_match:
            model = model_match.group(1).strip()
            # Normalize model number format
            model = re.sub(r'\s+', '', model).lower()
            return model
            
        return None
    
    def _clean_product_name(self, name):
        """Remove common filler words and standardize product names"""
        # Convert to lowercase
        name = name.lower()
        
        # Remove text in brackets
        name = re.sub(r'\[.*?\]', '', name)
        
        # Remove common filler words
        filler_words = [
            'видеокарта', 'ret', 'oem', 'видеокарты', 'ret,', 'oem,',
            'для', 'компьютера', 'пк', 'ПК', 'шт', 'штук', 'шт.',
            'ггц', 'ггб', 'гб', 'мб', 'тб', 'nvidia', 'amd', 'intel',
            'oc', 'ос', 'oc,', 'ос,', 'gddr7', 'gddr6', 'gddr6x', 'gddr5',
            '32гб', '24гб', '16гб', '12гб', '8гб', '6гб', '4гб', 
            '32gb', '24gb', '16gb', '12gb', '8gb', '6gb', '4gb',
            'gamerock', 'gaming', 'gaming,', 'gamerock,', 'rog', 'strix', 'rog,', 'strix,',
            'dual', 'dual,', 'turbo', 'turbo,', 'eagle', 'eagle,'
        ]
        
        for word in filler_words:
            # Replace word with space to ensure words don't get merged
            name = re.sub(r'\b' + re.escape(word) + r'\b', ' ', name)
            
        # Special handling for RTX/GTX series to preserve them in the name
        rtx_matches = re.findall(r'(rtx\s*\d{4}\s*(?:ti|super)?)', name, re.IGNORECASE)
        
        # Clean up multiple spaces
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Make sure we preserve important product identifiers
        if rtx_matches:
            # Make sure the RTX model is in the cleaned name
            if not any(rtx.lower() in name.lower() for rtx in rtx_matches):
                name = f"{name} {rtx_matches[0]}"
        
        return name
    
    def save_comparison_results(self, filename='price_comparison.json'):
        """Save comparison results to a JSON file"""
        if not self.comparison_results:
            logging.warning("No comparison results to save")
            return
            
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.comparison_results, f, ensure_ascii=False, indent=4)
            logging.info(f"Saved comparison results to {filename}")
        except Exception as e:
            logging.error(f"Error saving comparison results: {str(e)}")
    
    def get_best_deals(self, limit=10):
        """Get the products with the biggest price difference (best deals)"""
        if not self.comparison_results:
            return []
            
        # Sort by absolute price difference
        sorted_results = sorted(self.comparison_results, key=lambda x: abs(x['price_difference']), reverse=True)
        return sorted_results[:limit]

def run_price_comparison(citilink_category=None, dns_category=None):
    """Run the complete price comparison process
    
    Args:
        citilink_category: Category path for Citilink parser
        dns_category: Category name for filtering DNS products
    """
    comparison = PriceComparison()
    
    # Use videokarty (graphics cards) as the default category if none specified
    if not citilink_category:
        citilink_category = "videokarty"
        logging.info("No category specified, defaulting to 'videokarty' (graphics cards)")
    
    # Map between Citilink categories and DNS category names
    category_mapping = {
        'videokarty': 'Видеокарты',
        'processory': 'Процессоры',
        'materinskie-platy': 'Материнские платы',
        'operativnaya-pamyat': 'Оперативная память',
        'moduli-pamyati': 'Модули памяти',
        'bloki-pitaniya': 'Блоки питания',
        'kulery': 'Кулеры',
        'ventilyatory-dlya-korpusa': 'Вентиляторы',
        'zhestkie-diski': 'Жесткие диски',
        'ssd-nakopiteli': 'SSD накопители',
        'korpusa': 'Корпуса'
    }
    
    # If DNS category not specified, try to map from Citilink category
    if not dns_category and citilink_category in category_mapping:
        dns_category = category_mapping[citilink_category]
        logging.info(f"Mapped Citilink category '{citilink_category}' to DNS category '{dns_category}'")
    
    # Load data from Citilink
    citilink_products = comparison.load_citilink_data(citilink_category)
    logging.info(f"Loaded {len(citilink_products)} products from Citilink in category '{citilink_category}'")
    
    # Load data from DNS
    dns_products = comparison.load_dns_data(dns_category)
    logging.info(f"Loaded {len(dns_products)} products from DNS" + (f" in category '{dns_category}'" if dns_category else ""))
    
    # Check if we have products to compare
    if len(citilink_products) == 0 or len(dns_products) == 0:
        logging.warning("Not enough products to compare: " +
                      f"Citilink: {len(citilink_products)}, DNS: {len(dns_products)}")
        return []
    
    # Find matching products
    results = comparison.find_matching_products()
    
    # Save results
    comparison.save_comparison_results()
    
    return results

if __name__ == "__main__":
    run_price_comparison() 