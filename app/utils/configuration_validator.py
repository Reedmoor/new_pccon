"""
Configuration building and validation utilities.
Integrates characteristic filters into the configuration workflow.
"""

from app.models.models import UnifiedProduct, Configuration
from app.utils.standardization.characteristic_filters import (
    apply_filter,
    get_required_characteristics,
    get_important_characteristics,
)
import logging

logger = logging.getLogger(__name__)


class ConfigurationValidator:
    """Validates component compatibility with filtered characteristics"""
    
    @staticmethod
    def get_filtered_characteristics(product):
        """
        Get normalized characteristics for a product
        
        Args:
            product (UnifiedProduct): Product to get characteristics for
            
        Returns:
            dict: Filtered and normalized characteristics
        """
        if not product:
            return {}
        
        chars = product.get_characteristics()
        if not chars:
            return {}
        
        try:
            filtered = apply_filter(product.product_type, chars)
            return filtered
        except Exception as e:
            logger.warning(f"Error filtering characteristics for {product.product_name}: {e}")
            return chars
    
    @staticmethod
    def validate_component(product):
        """
        Validate component has required characteristics
        
        Args:
            product (UnifiedProduct): Component to validate
            
        Returns:
            dict: {'valid': bool, 'missing': list, 'warnings': list}
        """
        if not product:
            return {'valid': False, 'missing': [], 'warnings': ['Product is None']}
        
        product_type = product.product_type
        if not product_type or product_type == 'other':
            return {'valid': False, 'missing': [], 'warnings': ['Unknown product type']}
        
        chars = ConfigurationValidator.get_filtered_characteristics(product)
        required = get_required_characteristics(product_type)
        
        missing = []
        for field in required:
            if field not in chars or chars[field] is None:
                missing.append(field)
        
        warnings = []
        important = get_important_characteristics(product_type)
        for field in important:
            if field not in chars or chars[field] is None:
                warnings.append(f"Missing important characteristic: {field}")
        
        return {
            'valid': len(missing) == 0,
            'missing': missing,
            'warnings': warnings
        }
    
    @staticmethod
    def check_cpu_motherboard_compatibility(cpu, motherboard):
        """
        Check CPU and motherboard socket compatibility using filtered data
        
        Args:
            cpu (UnifiedProduct): CPU component
            motherboard (UnifiedProduct): Motherboard component
            
        Returns:
            dict: {'compatible': bool, 'reason': str, 'cpu_socket': str, 'mb_socket': str}
        """
        if not cpu or not motherboard:
            return {'compatible': True, 'reason': 'Components not selected', 'cpu_socket': None, 'mb_socket': None}
        
        cpu_chars = ConfigurationValidator.get_filtered_characteristics(cpu)
        mb_chars = ConfigurationValidator.get_filtered_characteristics(motherboard)
        
        cpu_socket = cpu_chars.get('socket', '')
        mb_socket = mb_chars.get('socket', '')
        
        if not cpu_socket or not mb_socket:
            return {
                'compatible': True,
                'reason': 'Socket information missing',
                'cpu_socket': cpu_socket,
                'mb_socket': mb_socket
            }
        
        # Compare sockets
        if cpu_socket.upper() == mb_socket.upper():
            return {
                'compatible': True,
                'reason': 'Socket compatible',
                'cpu_socket': cpu_socket,
                'mb_socket': mb_socket
            }
        else:
            return {
                'compatible': False,
                'reason': f'Socket mismatch: {cpu_socket} (CPU) vs {mb_socket} (Motherboard)',
                'cpu_socket': cpu_socket,
                'mb_socket': mb_socket
            }
    
    @staticmethod
    def check_ram_motherboard_compatibility(ram, motherboard):
        """
        Check RAM and motherboard memory compatibility using filtered data
        
        Args:
            ram (UnifiedProduct): RAM component
            motherboard (UnifiedProduct): Motherboard component
            
        Returns:
            dict: {'compatible': bool, 'reason': str, 'details': dict}
        """
        if not ram or not motherboard:
            return {'compatible': True, 'reason': 'Components not selected', 'details': {}}
        
        ram_chars = ConfigurationValidator.get_filtered_characteristics(ram)
        mb_chars = ConfigurationValidator.get_filtered_characteristics(motherboard)
        
        ram_type = ram_chars.get('memory_type', '')
        mb_type = mb_chars.get('memory_type', '')
        ram_form_factor = ram_chars.get('memory_form_factor', '')
        mb_form_factor = mb_chars.get('memory_form_factor', '')
        
        issues = []
        
        # Check memory type
        if ram_type and mb_type:
            if ram_type.upper() != mb_type.upper():
                issues.append(f"Memory type mismatch: {ram_type} (RAM) vs {mb_type} (Motherboard)")
        
        # Check form factor
        if ram_form_factor and mb_form_factor:
            if ram_form_factor.upper() != mb_form_factor.upper():
                issues.append(f"Form factor mismatch: {ram_form_factor} (RAM) vs {mb_form_factor} (Motherboard)")
        
        return {
            'compatible': len(issues) == 0,
            'reason': '; '.join(issues) if issues else 'Memory compatible',
            'details': {
                'ram_type': ram_type,
                'mb_type': mb_type,
                'ram_form_factor': ram_form_factor,
                'mb_form_factor': mb_form_factor
            }
        }
    
    @staticmethod
    def check_gpu_case_compatibility(gpu, case):
        """
        Check GPU and case compatibility (length)
        
        Args:
            gpu (UnifiedProduct): Graphics card
            case (UnifiedProduct): Case component
            
        Returns:
            dict: {'compatible': bool, 'reason': str, 'gpu_length': int, 'max_length': int}
        """
        if not gpu or not case:
            return {'compatible': True, 'reason': 'Components not selected', 'gpu_length': None, 'max_length': None}
        
        gpu_chars = ConfigurationValidator.get_filtered_characteristics(gpu)
        case_chars = ConfigurationValidator.get_filtered_characteristics(case)
        
        gpu_length = gpu_chars.get('length')
        max_length = case_chars.get('max_gpu_length')
        
        if gpu_length is None or max_length is None:
            return {
                'compatible': True,
                'reason': 'Length information missing',
                'gpu_length': gpu_length,
                'max_length': max_length
            }
        
        # Try to convert to int if strings
        try:
            gpu_length = int(gpu_length) if isinstance(gpu_length, str) else gpu_length
            max_length = int(max_length) if isinstance(max_length, str) else max_length
        except (ValueError, TypeError):
            return {
                'compatible': True,
                'reason': 'Could not parse length values',
                'gpu_length': gpu_length,
                'max_length': max_length
            }
        
        if gpu_length <= max_length:
            return {
                'compatible': True,
                'reason': f'GPU length OK: {gpu_length}mm ≤ {max_length}mm',
                'gpu_length': gpu_length,
                'max_length': max_length
            }
        else:
            return {
                'compatible': False,
                'reason': f'GPU too long: {gpu_length}mm > {max_length}mm',
                'gpu_length': gpu_length,
                'max_length': max_length
            }
    
    @staticmethod
    def check_cooler_case_compatibility(cooler, case):
        """
        Check CPU cooler and case compatibility (height)
        
        Args:
            cooler (UnifiedProduct): CPU cooler
            case (UnifiedProduct): Case component
            
        Returns:
            dict: {'compatible': bool, 'reason': str, 'cooler_height': int, 'max_height': int}
        """
        if not cooler or not case:
            return {'compatible': True, 'reason': 'Components not selected', 'cooler_height': None, 'max_height': None}
        
        cooler_chars = ConfigurationValidator.get_filtered_characteristics(cooler)
        case_chars = ConfigurationValidator.get_filtered_characteristics(case)
        
        cooler_height = cooler_chars.get('cooler_height')
        max_height = case_chars.get('max_cooler_height')
        
        if cooler_height is None or max_height is None:
            return {
                'compatible': True,
                'reason': 'Height information missing',
                'cooler_height': cooler_height,
                'max_height': max_height
            }
        
        # Try to convert to int if strings
        try:
            cooler_height = int(cooler_height) if isinstance(cooler_height, str) else cooler_height
            max_height = int(max_height) if isinstance(max_height, str) else max_height
        except (ValueError, TypeError):
            return {
                'compatible': True,
                'reason': 'Could not parse height values',
                'cooler_height': cooler_height,
                'max_height': max_height
            }
        
        if cooler_height <= max_height:
            return {
                'compatible': True,
                'reason': f'Cooler height OK: {cooler_height}mm ≤ {max_height}mm',
                'cooler_height': cooler_height,
                'max_height': max_height
            }
        else:
            return {
                'compatible': False,
                'reason': f'Cooler too tall: {cooler_height}mm > {max_height}mm',
                'cooler_height': cooler_height,
                'max_height': max_height
            }
    
    @staticmethod
    def validate_configuration(config):
        """
        Validate complete configuration using filtered characteristics
        
        Args:
            config (Configuration): Configuration to validate
            
        Returns:
            dict: {
                'valid': bool,
                'compatibility_issues': list,
                'validation_issues': list,
                'warnings': list
            }
        """
        compatibility_issues = []
        validation_issues = []
        warnings = []
        
        components = {
            'motherboard': config.motherboard,
            'cpu': config.processor,
            'gpu': config.graphics_card,
            'ram': config.ram,
            'cooler': config.cooler,
            'hdd': config.hard_drive,
            'psu': config.power_supply,
            'case': config.case,
        }
        
        # Validate each component
        for comp_name, component in components.items():
            if component:
                validation = ConfigurationValidator.validate_component(component)
                if not validation['valid']:
                    validation_issues.append(f"{comp_name}: Missing {', '.join(validation['missing'])}")
                warnings.extend(validation['warnings'])
        
        # Check CPU-Motherboard compatibility
        if config.processor and config.motherboard:
            result = ConfigurationValidator.check_cpu_motherboard_compatibility(config.processor, config.motherboard)
            if not result['compatible']:
                compatibility_issues.append(result['reason'])
        
        # Check RAM-Motherboard compatibility
        if config.ram and config.motherboard:
            result = ConfigurationValidator.check_ram_motherboard_compatibility(config.ram, config.motherboard)
            if not result['compatible']:
                compatibility_issues.append(result['reason'])
        
        # Check GPU-Case compatibility
        if config.graphics_card and config.case:
            result = ConfigurationValidator.check_gpu_case_compatibility(config.graphics_card, config.case)
            if not result['compatible']:
                compatibility_issues.append(result['reason'])
        
        # Check Cooler-Case compatibility
        if config.cooler and config.case:
            result = ConfigurationValidator.check_cooler_case_compatibility(config.cooler, config.case)
            if not result['compatible']:
                compatibility_issues.append(result['reason'])
        
        return {
            'valid': len(validation_issues) == 0 and len(compatibility_issues) == 0,
            'compatibility_issues': compatibility_issues,
            'validation_issues': validation_issues,
            'warnings': warnings
        }


class ConfigurationComponentFilter:
    """Filters and ranks components for configuration selection"""

    @staticmethod
    def _product_ids(products):
        return {p.id for p in products}

    @staticmethod
    def get_compatible_cpus_for_motherboard(motherboard):
        """Get CPUs compatible with a motherboard socket."""
        if not motherboard or motherboard.product_type != 'motherboard':
            return UnifiedProduct.query.filter_by(product_type='processor').all()

        mb_chars = ConfigurationValidator.get_filtered_characteristics(motherboard)
        mb_socket = mb_chars.get('socket', '')
        if not mb_socket:
            return UnifiedProduct.query.filter_by(product_type='processor').all()

        compatible = []
        for cpu in UnifiedProduct.query.filter_by(product_type='processor').all():
            cpu_chars = ConfigurationValidator.get_filtered_characteristics(cpu)
            cpu_socket = cpu_chars.get('socket', '')
            if cpu_socket and cpu_socket.upper() == mb_socket.upper():
                compatible.append(cpu)
        return compatible
    
    @staticmethod
    def get_compatible_motherboards_for_cpu(cpu):
        """
        Get motherboards compatible with a CPU
        
        Args:
            cpu (UnifiedProduct): CPU component
            
        Returns:
            list: Compatible motherboards ranked by relevance
        """
        if not cpu or cpu.product_type != 'processor':
            return UnifiedProduct.query.filter_by(product_type='motherboard').all()
        
        cpu_chars = ConfigurationValidator.get_filtered_characteristics(cpu)
        cpu_socket = cpu_chars.get('socket', '')
        
        if not cpu_socket:
            return UnifiedProduct.query.filter_by(product_type='motherboard').all()
        
        # Get all motherboards with matching socket
        all_motherboards = UnifiedProduct.query.filter_by(product_type='motherboard').all()
        compatible = []
        
        for mb in all_motherboards:
            mb_chars = ConfigurationValidator.get_filtered_characteristics(mb)
            mb_socket = mb_chars.get('socket', '')
            
            if mb_socket.upper() == cpu_socket.upper():
                compatible.append(mb)
        
        return compatible
    
    @staticmethod
    def get_compatible_ram_for_motherboard(motherboard):
        """
        Get RAM compatible with a motherboard
        
        Args:
            motherboard (UnifiedProduct): Motherboard component
            
        Returns:
            list: Compatible RAM modules
        """
        if not motherboard or motherboard.product_type != 'motherboard':
            return UnifiedProduct.query.filter_by(product_type='ram').all()
        
        mb_chars = ConfigurationValidator.get_filtered_characteristics(motherboard)
        mb_type = mb_chars.get('memory_type', '')
        mb_form_factor = mb_chars.get('memory_form_factor', '')
        
        all_ram = UnifiedProduct.query.filter_by(product_type='ram').all()
        compatible = []
        
        for ram in all_ram:
            ram_chars = ConfigurationValidator.get_filtered_characteristics(ram)
            ram_type = ram_chars.get('memory_type', '')
            ram_form_factor = ram_chars.get('memory_form_factor', '')
            
            # Check type match
            if mb_type and ram_type and ram_type.upper() != mb_type.upper():
                continue
            
            # Check form factor match
            if mb_form_factor and ram_form_factor and ram_form_factor.upper() != mb_form_factor.upper():
                continue
            
            compatible.append(ram)
        
        return compatible
    
    @staticmethod
    def get_compatible_gpus_for_case(case):
        """
        Get GPUs that fit in a case
        
        Args:
            case (UnifiedProduct): Case component
            
        Returns:
            list: Compatible GPUs
        """
        if not case or case.product_type != 'case':
            return UnifiedProduct.query.filter_by(product_type='graphics_card').all()
        
        case_chars = ConfigurationValidator.get_filtered_characteristics(case)
        max_length = case_chars.get('max_gpu_length')
        
        if max_length is None:
            return UnifiedProduct.query.filter_by(product_type='graphics_card').all()
        
        try:
            max_length = int(max_length) if isinstance(max_length, str) else max_length
        except (ValueError, TypeError):
            return UnifiedProduct.query.filter_by(product_type='graphics_card').all()
        
        all_gpus = UnifiedProduct.query.filter_by(product_type='graphics_card').all()
        compatible = []
        
        for gpu in all_gpus:
            gpu_chars = ConfigurationValidator.get_filtered_characteristics(gpu)
            gpu_length = gpu_chars.get('length')
            
            if gpu_length is None:
                compatible.append(gpu)  # Unknown length, include it
                continue
            
            try:
                gpu_length = int(gpu_length) if isinstance(gpu_length, str) else gpu_length
                if gpu_length <= max_length:
                    compatible.append(gpu)
            except (ValueError, TypeError):
                compatible.append(gpu)  # Unparseable, include it
        
        return compatible
    
    @staticmethod
    def get_compatible_coolers_for_case(case):
        """
        Get coolers that fit in a case
        
        Args:
            case (UnifiedProduct): Case component
            
        Returns:
            list: Compatible coolers
        """
        if not case or case.product_type != 'case':
            return UnifiedProduct.query.filter_by(product_type='cooler').all()
        
        case_chars = ConfigurationValidator.get_filtered_characteristics(case)
        max_height = case_chars.get('max_cooler_height')
        
        if max_height is None:
            return UnifiedProduct.query.filter_by(product_type='cooler').all()
        
        try:
            max_height = int(max_height) if isinstance(max_height, str) else max_height
        except (ValueError, TypeError):
            return UnifiedProduct.query.filter_by(product_type='cooler').all()
        
        all_coolers = UnifiedProduct.query.filter_by(product_type='cooler').all()
        compatible = []
        
        for cooler in all_coolers:
            cooler_chars = ConfigurationValidator.get_filtered_characteristics(cooler)
            cooler_height = cooler_chars.get('cooler_height')
            
            if cooler_height is None:
                compatible.append(cooler)  # Unknown height, include it
                continue
            
            try:
                cooler_height = int(cooler_height) if isinstance(cooler_height, str) else cooler_height
                if cooler_height <= max_height:
                    compatible.append(cooler)
            except (ValueError, TypeError):
                compatible.append(cooler)  # Unparseable, include it
        
        return compatible

    @staticmethod
    def filter_products_for_context(product_type, products, context):
        """
        Filter product list based on already selected configuration components.
        """
        if not products or not context:
            return products

        allowed_ids = None
        cpu_id = context.get('cpu_id') or 0
        motherboard_id = context.get('motherboard_id') or 0
        ram_id = context.get('ram_id') or 0
        case_id = context.get('case_id') or context.get('frame_id') or 0

        if product_type == 'motherboard' and cpu_id:
            cpu = UnifiedProduct.query.get(cpu_id)
            if cpu:
                allowed_ids = ConfigurationComponentFilter._product_ids(
                    ConfigurationComponentFilter.get_compatible_motherboards_for_cpu(cpu)
                )
        elif product_type == 'processor' and motherboard_id:
            motherboard = UnifiedProduct.query.get(motherboard_id)
            if motherboard:
                allowed_ids = ConfigurationComponentFilter._product_ids(
                    ConfigurationComponentFilter.get_compatible_cpus_for_motherboard(motherboard)
                )
        elif product_type == 'ram' and motherboard_id:
            motherboard = UnifiedProduct.query.get(motherboard_id)
            if motherboard:
                allowed_ids = ConfigurationComponentFilter._product_ids(
                    ConfigurationComponentFilter.get_compatible_ram_for_motherboard(motherboard)
                )
        elif product_type == 'graphics_card' and case_id:
            case = UnifiedProduct.query.get(case_id)
            if case:
                allowed_ids = ConfigurationComponentFilter._product_ids(
                    ConfigurationComponentFilter.get_compatible_gpus_for_case(case)
                )
        elif product_type == 'case' and context.get('gpu_id'):
            gpu = UnifiedProduct.query.get(context.get('gpu_id'))
            if gpu:
                allowed_ids = {
                    c.id for c in UnifiedProduct.query.filter_by(product_type='case').all()
                    if ConfigurationValidator.check_gpu_case_compatibility(gpu, c)['compatible']
                }
        elif product_type == 'cooler' and case_id:
            case = UnifiedProduct.query.get(case_id)
            if case:
                allowed_ids = ConfigurationComponentFilter._product_ids(
                    ConfigurationComponentFilter.get_compatible_coolers_for_case(case)
                )
        elif product_type == 'case' and context.get('cooler_id'):
            cooler = UnifiedProduct.query.get(context.get('cooler_id'))
            if cooler:
                allowed_ids = {
                    c.id for c in UnifiedProduct.query.filter_by(product_type='case').all()
                    if ConfigurationValidator.check_cooler_case_compatibility(cooler, c)['compatible']
                }

        if allowed_ids is None:
            return products
        return [product for product in products if product.id in allowed_ids]
