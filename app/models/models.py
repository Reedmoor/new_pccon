from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' или 'admin'
    
    configurations = db.relationship('Configuration', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'

# Unified product model for all components
class UnifiedProduct(db.Model):
    __tablename__ = 'unified_products'
    
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False)
    price_discounted = db.Column(db.Float, nullable=True)
    price_original = db.Column(db.Float, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    number_of_reviews = db.Column(db.Integer, nullable=True)
    vendor = db.Column(db.String(100), nullable=False)  # Source of the product (e.g., Citilink, DNS)
    images = db.Column(db.Text, nullable=True)  # Stored as JSON string
    characteristics = db.Column(db.Text, nullable=False)  # Stored as JSON string
    availability = db.Column(db.Boolean, default=True)
    product_url = db.Column(db.String(500), nullable=False)
    category = db.Column(db.Text, nullable=True)  # Stored as JSON string
    product_type = db.Column(db.String(50), nullable=False)  # Type of component (motherboard, cpu, gpu, etc.)
    
    # Relationships for configurations
    motherboard_configs = db.relationship('Configuration', foreign_keys='Configuration.motherboard_id', backref='motherboard')
    power_supply_configs = db.relationship('Configuration', foreign_keys='Configuration.supply_id', backref='power_supply')
    processor_configs = db.relationship('Configuration', foreign_keys='Configuration.cpu_id', backref='processor')
    graphics_card_configs = db.relationship('Configuration', foreign_keys='Configuration.gpu_id', backref='graphics_card')
    cooler_configs = db.relationship('Configuration', foreign_keys='Configuration.cooler_id', backref='cooler')
    ram_configs = db.relationship('Configuration', foreign_keys='Configuration.ram_id', backref='ram')
    hard_drive_configs = db.relationship('Configuration', foreign_keys='Configuration.hdd_id', backref='hard_drive')
    case_configs = db.relationship('Configuration', foreign_keys='Configuration.frame_id', backref='case')
    
    def set_images(self, images_list):
        self.images = json.dumps(images_list)
        
    def get_images(self):
        return json.loads(self.images) if self.images else []
    
    def set_characteristics(self, characteristics_dict):
        self.characteristics = json.dumps(characteristics_dict)
        
    def get_characteristics(self):
        return json.loads(self.characteristics) if self.characteristics else {}
    
    def set_category(self, category_list):
        self.category = json.dumps(category_list)
        
    def get_category(self):
        return json.loads(self.category) if self.category else []
    
    # Helper methods for compatibility checks
    def get_socket(self):
        chars = self.get_characteristics()
        if self.product_type == 'motherboard':
            return chars.get('socket', '')
        elif self.product_type == 'processor':
            return chars.get('socket', '')
        return None
    
    def get_memory_type(self):
        chars = self.get_characteristics()
        if self.product_type == 'motherboard':
            return chars.get('memory_type', '')
        elif self.product_type == 'ram':
            return chars.get('memory_type', '')
        return None
    
    def get_memory_form_factor(self):
        """Get memory form factor (DIMM, SO-DIMM, etc.)"""
        chars = self.get_characteristics()
        if self.product_type == 'motherboard':
            return chars.get('memory_form_factor', '')
        elif self.product_type == 'ram':
            return chars.get('memory_form_factor', '')
        return None
    
    def get_power_use(self):
        chars = self.get_characteristics()
        if self.product_type in ['processor', 'graphics_card', 'cooler', 'ram']:
            return chars.get('power_consumption', 0)
        return 0
    
    def get_form_factor(self):
        chars = self.get_characteristics()
        if self.product_type == 'motherboard':
            return chars.get('form_factor', '')
        elif self.product_type == 'case':
            return chars.get('supported_form_factors', [])
        return None
    
    # Compatibility check methods
    def is_compatible_with(self, other_product):
        """Check if this product is compatible with another product"""
        if not other_product:
            return True
            
        # CPU and Motherboard compatibility
        if (self.product_type == 'processor' and other_product.product_type == 'motherboard') or \
           (self.product_type == 'motherboard' and other_product.product_type == 'processor'):
            result = self.check_socket_compatibility(other_product)
            if result is not True:  # If result is an error message
                return result
            
        # RAM and Motherboard compatibility
        if (self.product_type == 'ram' and other_product.product_type == 'motherboard') or \
           (self.product_type == 'motherboard' and other_product.product_type == 'ram'):
            result = self.check_memory_compatibility(other_product)
            if result is not True:  # If result is an error message
                return result
            
            # Check memory form factor compatibility (DIMM vs SO-DIMM)
            result = self.check_memory_form_factor_compatibility(other_product)
            if result is not True:  # If result is an error message
                return result
            
        # Case and Motherboard compatibility
        if (self.product_type == 'case' and other_product.product_type == 'motherboard') or \
           (self.product_type == 'motherboard' and other_product.product_type == 'case'):
            result = self.check_form_factor_compatibility(other_product)
            if result is not True:  # If result is an error message
                return result
            
        # GPU and Case compatibility (length check)
        if (self.product_type == 'graphics_card' and other_product.product_type == 'case') or \
           (self.product_type == 'case' and other_product.product_type == 'graphics_card'):
            result = self.check_gpu_case_compatibility(other_product)
            if result is not True:  # If result is an error message
                return result
            
        # Power supply compatibility with all components
        if self.product_type == 'power_supply' or other_product.product_type == 'power_supply':
            result = self.check_power_compatibility(other_product)
            if result is not True:  # If result is an error message
                return result
            
        return True  # Default to compatible if no specific check
    
    def check_socket_compatibility(self, other_product):
        """Check if CPU socket is compatible with motherboard socket"""
        my_socket = self.get_socket()
        other_socket = other_product.get_socket()
        
        if not my_socket or not other_socket:
            return True  # No socket info, assume compatible
        
        # Normalize socket names to handle common variations
        def normalize_socket(socket_name):
            if not socket_name:
                return ""
            
            # Convert to lowercase for case-insensitive comparison
            socket_name = socket_name.lower()
            
            # Remove "socket" prefix if present
            if socket_name.startswith("socket"):
                socket_name = socket_name[6:].strip()
                
            # Handle other common variations
            replacements = {
                "lga ": "lga",
                "am ": "am",
                "fm ": "fm",
                "tr ": "tr"
            }
            
            for prefix, replacement in replacements.items():
                if socket_name.startswith(prefix):
                    socket_name = socket_name.replace(prefix, replacement)
                    
            return socket_name
        
        # Normalize both socket names
        normalized_my_socket = normalize_socket(my_socket)
        normalized_other_socket = normalize_socket(other_socket)
            
        # Compare normalized socket names
        if normalized_my_socket != normalized_other_socket:
            # Return detailed error message instead of just True/False
            if self.product_type == 'motherboard':
                return f"Несовместимые сокеты: материнская плата имеет сокет {my_socket}, а процессор — {other_socket}"
            else:
                return f"Несовместимые сокеты: процессор имеет сокет {my_socket}, а материнская плата — {other_socket}"
        return True
    
    def check_memory_compatibility(self, other_product):
        """Check if RAM is compatible with motherboard"""
        my_memory_type = self.get_memory_type()
        other_memory_type = other_product.get_memory_type()
        
        if not my_memory_type or not other_memory_type:
            return True  # No memory type info, assume compatible
            
        # Simple exact match for now
        if my_memory_type.lower() != other_memory_type.lower():
            # Return detailed error message
            if self.product_type == 'motherboard':
                return f"Несовместимые типы памяти: материнская плата поддерживает {my_memory_type}, а оперативная память — {other_memory_type}"
            else:
                return f"Несовместимые типы памяти: оперативная память типа {my_memory_type}, а материнская плата поддерживает {other_memory_type}"
        return True
    
    def check_memory_form_factor_compatibility(self, other_product):
        """Check if RAM form factor is compatible with motherboard"""
        my_memory_form_factor = self.get_memory_form_factor()
        other_memory_form_factor = other_product.get_memory_form_factor()
        
        if not my_memory_form_factor or not other_memory_form_factor:
            return True  # No form factor info, assume compatible
        
        # Normalize form factor names for comparison
        def normalize_form_factor(form_factor):
            if not form_factor:
                return ""
            form_factor = form_factor.lower().strip()
            # Handle common variations
            if form_factor in ['dimm', 'udimm', 'unbuffered dimm']:
                return 'dimm'
            elif form_factor in ['so-dimm', 'sodimm', 'so dimm']:
                return 'so-dimm'
            elif form_factor in ['ecc', 'registered', 'rdimm']:
                return 'rdimm'
            return form_factor
        
        # Normalize both form factors
        normalized_my_ff = normalize_form_factor(my_memory_form_factor)
        normalized_other_ff = normalize_form_factor(other_memory_form_factor)
        
        # Check compatibility
        if normalized_my_ff != normalized_other_ff:
            # Return detailed error message
            if self.product_type == 'motherboard':
                return f"Несовместимый форм-фактор памяти: материнская плата поддерживает {my_memory_form_factor}, а оперативная память — {other_memory_form_factor}"
            else:
                return f"Несовместимый форм-фактор памяти: оперативная память типа {my_memory_form_factor}, а материнская плата поддерживает {other_memory_form_factor}"
        return True
    
    def check_form_factor_compatibility(self, other_product):
        """Check if motherboard form factor is compatible with case"""
        if self.product_type == 'motherboard':
            mobo_form_factor = self.get_form_factor()
            case_supported_form_factors = other_product.get_form_factor()
        else:
            mobo_form_factor = other_product.get_form_factor()
            case_supported_form_factors = self.get_form_factor()
            
        if not mobo_form_factor or not case_supported_form_factors:
            return True  # No form factor info, assume compatible
            
        # Check if motherboard form factor is in case's supported form factors
        if isinstance(case_supported_form_factors, list):
            if mobo_form_factor.lower() not in [ff.lower() for ff in case_supported_form_factors]:
                return f"Несовместимый форм-фактор: материнская плата {mobo_form_factor}, а корпус поддерживает {', '.join(case_supported_form_factors)}"
            return True
        else:
            if mobo_form_factor.lower() != case_supported_form_factors.lower():
                return f"Несовместимый форм-фактор: материнская плата {mobo_form_factor}, а корпус поддерживает {case_supported_form_factors}"
            return True
    
    def check_gpu_case_compatibility(self, other_product):
        """Check if GPU length is compatible with case"""
        chars = self.get_characteristics()
        other_chars = other_product.get_characteristics()
        
        if self.product_type == 'graphics_card':
            gpu_length = chars.get('length', 0)
            max_gpu_length = other_chars.get('max_gpu_length', 0)
        else:
            gpu_length = other_chars.get('length', 0)
            max_gpu_length = chars.get('max_gpu_length', 0)
            
        if not gpu_length or not max_gpu_length:
            return True  # No length info, assume compatible
            
        # Convert to integers if they're strings
        try:
            gpu_length = int(gpu_length) if isinstance(gpu_length, str) else gpu_length
            max_gpu_length = int(max_gpu_length) if isinstance(max_gpu_length, str) else max_gpu_length
            
            if gpu_length > max_gpu_length:
                return f"Видеокарта слишком длинная: длина видеокарты {gpu_length} мм, максимальная поддерживаемая длина корпуса {max_gpu_length} мм"
            return True
        except (ValueError, TypeError):
            return True  # Conversion error, assume compatible
    
    def check_power_compatibility(self, other_product):
        """Check if power supply wattage is sufficient for the component"""
        chars = self.get_characteristics()
        other_chars = other_product.get_characteristics()
        
        if self.product_type == 'power_supply':
            psu_wattage = chars.get('wattage', 0)
            component_power = other_product.get_power_use()
            component_type = other_product.product_type
        else:
            psu_wattage = other_chars.get('wattage', 0)
            component_power = self.get_power_use()
            component_type = self.product_type
            
        if not psu_wattage or not component_power:
            return True  # No power info, assume compatible
            
        # Convert to integers if they're strings
        try:
            psu_wattage = int(psu_wattage) if isinstance(psu_wattage, str) else psu_wattage
            component_power = int(component_power) if isinstance(component_power, str) else component_power
            
            if psu_wattage < component_power:
                component_type_ru = {
                    'processor': 'процессора',
                    'graphics_card': 'видеокарты',
                    'cooler': 'кулера',
                    'ram': 'оперативной памяти'
                }.get(component_type, component_type)
                
                return f"Недостаточная мощность блока питания: требуется {component_power}Вт для {component_type_ru}, а блок питания обеспечивает только {psu_wattage}Вт"
            return True
        except (ValueError, TypeError):
            return True  # Conversion error, assume compatible

class Configuration(db.Model):
    __tablename__ = 'configurations'
    
    conf_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # All foreign keys now point to unified_products
    motherboard_id = db.Column(db.Integer, db.ForeignKey('unified_products.id'), nullable=True)
    supply_id = db.Column(db.Integer, db.ForeignKey('unified_products.id'), nullable=True)
    cpu_id = db.Column(db.Integer, db.ForeignKey('unified_products.id'), nullable=True)
    gpu_id = db.Column(db.Integer, db.ForeignKey('unified_products.id'), nullable=True)
    cooler_id = db.Column(db.Integer, db.ForeignKey('unified_products.id'), nullable=True)
    ram_id = db.Column(db.Integer, db.ForeignKey('unified_products.id'), nullable=True)
    hdd_id = db.Column(db.Integer, db.ForeignKey('unified_products.id'), nullable=True)
    frame_id = db.Column(db.Integer, db.ForeignKey('unified_products.id'), nullable=True)
    
    def total_price(self):
        """Рассчитывает общую стоимость конфигурации."""
        total = 0
        components = [
            self.motherboard, self.power_supply, self.processor, 
            self.graphics_card, self.cooler, self.ram, 
            self.hard_drive, self.case
        ]
        for component in components:
            if component:
                # Используем discounted цену, если доступна, иначе original
                price = component.price_discounted if component.price_discounted is not None else component.price_original
                if price is not None:
                    total += price
        return round(total, 2)
    
    def check_compatibility(self):
        """Check compatibility between all components in the configuration"""
        components = [
            self.motherboard, self.power_supply, self.processor,
            self.graphics_card, self.cooler, self.ram,
            self.hard_drive, self.case
        ]
        
        # Filter out None components
        components = [c for c in components if c]
        
        issues = []
        
        # Check each component against every other component
        for i, comp1 in enumerate(components):
            for comp2 in components[i+1:]:
                compatibility_result = comp1.is_compatible_with(comp2)
                if compatibility_result is not True:
                    # If compatibility_result is a string, it's an error message
                    issues.append(compatibility_result)
        
        return issues if issues else None
        
    def compatibility_check(self):
        """Alias for check_compatibility to maintain compatibility with templates"""
        return self.check_compatibility()