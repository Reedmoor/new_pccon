"""
Characteristic filters and normalizers for each component type.
Handles standardization of component-specific characteristics across different vendors.

Parsed JSON formats:
- Citilink: properties[].properties[] with {name, value}
- DNS: characteristics.{group}[] with {title, value}
Both are mapped to canonical keys in standardize.py before storage.
"""

import re


# Alternative field names from different vendors / legacy imports
FIELD_ALIASES = {
    'socket': ['Сокет', 'Сокет процессора', 'socket_type'],
    'core_count': ['cores', 'Количество ядер', 'cpu_cores'],
    'thread_count': ['threads', 'Количество потоков'],
    'base_clock': ['frequency', 'Базовая частота процессора'],
    'boost_clock': ['max_frequency', 'Турбочастота'],
    'power_consumption': ['tdp', 'TDP', 'max_tdp', 'Тепловыделение (TDP)'],
    'memory_size': ['capacity', 'Объем оперативной памяти', 'Объем видеопамяти'],
    'memory_clock': ['frequency', 'Частота памяти'],
    'memory_form_factor': ['Тип модуля памяти', 'memory_module_type'],
    'storage_capacity': ['capacity', 'Объем накопителя'],
    'disk_type': ['type', 'storage_type'],
    'wattage': ['power', 'Мощность блока питания', 'Мощность'],
    'efficiency_rating': ['efficiency_certificate', 'certification', 'Сертификат энергоэффективности'],
    'modular_type': ['modular', 'cable_management', 'Модульность'],
    'cooling_type': ['Тип охлаждения', 'type'],
    'cooler_height': ['height', 'Высота кулера'],
    'fan_count': ['fan_size', 'fan_diameter', 'Количество вентиляторов'],
    'max_gpu_length': ['Максимальная длина видеокарты'],
    'max_cooler_height': ['Максимальная высота кулера'],
    'case_size': ['Типоразмер корпуса', 'case_type'],
    'supported_form_factors': ['Форм-фактор материнской платы', 'Поддерживаемые форм-факторы'],
    'supported_sockets': ['socket_compatibility', 'Поддерживаемые сокеты'],
    'length': ['Длина видеокарты', 'gpu_length'],
    'interface': ['Интерфейс подключения', 'connection_interface'],
}


def _is_empty(value):
    return value in (None, '', [], {})


PRODUCT_TYPE_ALIASES = {
    'motherboard': {'form_factor': ['Форм-фактор']},
    'ram': {'memory_form_factor': ['form_factor', 'Тип модуля памяти']},
    'case': {'case_size': ['form_factor', 'Типоразмер корпуса']},
}


def prepare_characteristics(characteristics, product_type=None):
    """
    Resolve vendor-specific / legacy field names to canonical keys.
    Does not overwrite already-filled canonical fields.
    """
    if not characteristics:
        return {}

    prepared = dict(characteristics)

    if product_type and product_type in PRODUCT_TYPE_ALIASES:
        for canonical, aliases in PRODUCT_TYPE_ALIASES[product_type].items():
            if not _is_empty(prepared.get(canonical)):
                continue
            for alias in aliases:
                alias_value = prepared.get(alias)
                if not _is_empty(alias_value):
                    prepared[canonical] = alias_value
                    break

    for canonical, aliases in FIELD_ALIASES.items():
        if not _is_empty(prepared.get(canonical)):
            continue
        for alias in aliases:
            alias_value = prepared.get(alias)
            if not _is_empty(alias_value):
                prepared[canonical] = alias_value
                break
    return prepared


def normalize_for_display(characteristics, product_type):
    """
    Normalize characteristics for UI: apply filters and add display aliases.
    Keeps extra fields from DB, overwrites important ones with normalized values.
    """
    chars = prepare_characteristics(characteristics or {}, product_type)
    filtered = apply_filter(product_type, chars)

    result = dict(chars)
    result.update(filtered)

    def set_if_missing(target_key, source_keys):
        if not _is_empty(result.get(target_key)):
            return
        for source_key in source_keys:
            source_value = result.get(source_key)
            if not _is_empty(source_value):
                result[target_key] = source_value
                return

    set_if_missing('cores', ['core_count'])
    set_if_missing('tdp', ['power_consumption'])
    set_if_missing('capacity', ['memory_size', 'storage_capacity'])
    set_if_missing('frequency', ['memory_clock', 'base_clock'])
    set_if_missing('max_tdp', ['power_consumption', 'tdp'])
    set_if_missing('certification', ['efficiency_rating'])
    set_if_missing('modular', ['modular_type'])

    if product_type == 'processor':
        set_if_missing('cores', ['core_count'])
    elif product_type == 'ram':
        set_if_missing('capacity', ['memory_size'])
        set_if_missing('frequency', ['memory_clock'])
    elif product_type == 'hard_drive':
        set_if_missing('capacity', ['storage_capacity'])
        set_if_missing('type', ['disk_type', 'storage_type', 'interface'])
    elif product_type == 'cooler':
        set_if_missing('max_tdp', ['power_consumption', 'tdp'])
        set_if_missing('socket_compatibility', ['supported_sockets', 'socket'])
        set_if_missing('fan_size', ['fan_count', 'fan_diameter'])
    elif product_type == 'power_supply':
        set_if_missing('certification', ['efficiency_rating'])
        set_if_missing('modular', ['modular_type'])
    elif product_type == 'case':
        set_if_missing('form_factor', ['case_size'])

    return result


class CharacteristicFilter:
    """Base class for characteristic filtering"""
    
    @staticmethod
    def normalize_value(value, field_type='string'):
        """Normalize characteristic value based on type"""
        if value is None or value == '':
            return None
        
        value_str = str(value).strip()
        
        if field_type == 'string':
            return value_str
        elif field_type == 'float':
            try:
                return float(re.sub(r'[^\d.]', '', value_str))
            except (ValueError, AttributeError):
                return None
        elif field_type == 'int':
            try:
                return int(re.sub(r'[^\d]', '', value_str))
            except (ValueError, AttributeError):
                return None
        
        return value_str


class ProcessorFilter(CharacteristicFilter):
    """Filter for processor characteristics"""
    
    # Key characteristics required for processors
    REQUIRED_CHARACTERISTICS = {'socket', 'core_count', 'base_clock'}
    IMPORTANT_CHARACTERISTICS = {'socket', 'core_count', 'thread_count', 'base_clock', 'boost_clock', 'l3_cache', 'power_consumption'}
    
    @staticmethod
    def normalize_socket(socket_value):
        """Normalize socket designation (e.g., "LGA1700" vs "Intel LGA 1700")"""
        if not socket_value:
            return None
        
        socket_str = str(socket_value).upper().strip()
        
        # Remove common prefixes and normalize
        socket_str = re.sub(r'(INTEL|AMD)\s*', '', socket_str)
        socket_str = re.sub(r'SOCKET\s+', '', socket_str)
        socket_compact = re.sub(r'\s+', '', socket_str)
        
        # Map common socket names
        socket_map = {
            'LGA1700': 'LGA1700',
            'LGA1150': 'LGA1150',
            'LGA1155': 'LGA1155',
            'LGA1151': 'LGA1151',
            'LGA1200': 'LGA1200',
            'LGA775': 'LGA775',
            'AM5': 'AM5',
            'AM4': 'AM4',
            'AM3+': 'AM3+',
            'AM3': 'AM3',
            'TR4': 'TR4',
            'TRX4': 'TRX4',
            'TRX5': 'TRX5',
        }
        
        for key, value in socket_map.items():
            if key in socket_compact:
                return value
        
        return socket_compact or socket_str
    
    @staticmethod
    def normalize_core_count(core_count):
        """Normalize core count (extract number, sum hybrid core descriptions)"""
        if _is_empty(core_count):
            return None

        core_str = str(core_count).strip()
        numbers = re.findall(r'(\d+)', core_str)
        if len(numbers) > 1 and ('+' in core_str or 'ядр' in core_str.lower() or 'core' in core_str.lower()):
            return sum(int(n) for n in numbers)
        return CharacteristicFilter.normalize_value(core_count, 'int')
    
    @staticmethod
    def normalize_clock(clock_value, field_type='base_clock'):
        """Convert clock speeds to MHz"""
        if not clock_value:
            return None
        
        clock_str = str(clock_value).strip()
        
        # Try to extract GHz first
        ghz_match = re.search(r'(\d+\.?\d*)\s*(ГГц|GHz)', clock_str, re.IGNORECASE)
        if ghz_match:
            return int(float(ghz_match.group(1)) * 1000)
        
        # Try to extract MHz
        mhz_match = re.search(r'(\d+)\s*(МГц|MHz)', clock_str, re.IGNORECASE)
        if mhz_match:
            return int(mhz_match.group(1))
        
        # Try to extract just numbers
        num_match = re.search(r'(\d+)', clock_str)
        if num_match:
            value = int(num_match.group(1))
            # If value is less than 10, assume GHz
            if value < 100:
                return value * 1000
            return value
        
        return None
    
    @staticmethod
    def filter_characteristics(characteristics):
        """Filter processor characteristics, keeping important ones"""
        filtered = {}
        
        important_fields = {
            'socket': ProcessorFilter.normalize_socket,
            'core_count': ProcessorFilter.normalize_core_count,
            'thread_count': lambda x: CharacteristicFilter.normalize_value(x, 'int'),
            'base_clock': ProcessorFilter.normalize_clock,
            'boost_clock': ProcessorFilter.normalize_clock,
            'l3_cache': lambda x: CharacteristicFilter.normalize_value(x, 'int'),
            'power_consumption': lambda x: CharacteristicFilter.normalize_value(x, 'int'),
        }
        
        for field, normalizer in important_fields.items():
            if field in characteristics:
                value = characteristics[field]
                normalized = normalizer(value)
                if normalized is not None:
                    filtered[field] = normalized
        
        return filtered


class MotherboardFilter(CharacteristicFilter):
    """Filter for motherboard characteristics"""
    
    REQUIRED_CHARACTERISTICS = {'socket', 'form_factor'}
    IMPORTANT_CHARACTERISTICS = {'socket', 'form_factor', 'chipset', 'memory_type', 'memory_form_factor'}
    
    @staticmethod
    def normalize_socket(socket_value):
        """Normalize socket designation"""
        return ProcessorFilter.normalize_socket(socket_value)  # Same logic as CPU
    
    @staticmethod
    def normalize_form_factor(form_factor):
        """Normalize form factor (ATX, microATX, miniITX, etc.)"""
        if not form_factor:
            return None
        
        ff_str = str(form_factor).upper().strip()
        
        # Map common form factors
        form_factor_map = {
            'STANDARD-ATX': 'ATX',
            'STANDARD ATX': 'ATX',
            'ATX': 'ATX',
            'MICRO-ATX': 'microATX',
            'MINI-ITX': 'miniITX',
            'E-ATX': 'E-ATX',
            'CEB': 'CEB',
            'EATX': 'E-ATX',
            'MICROATX': 'microATX',
            'MINIITX': 'miniITX',
        }
        
        ff_normalized = ff_str.replace('_', '-')
        
        for key, value in form_factor_map.items():
            if key in ff_normalized:
                return value
        
        return ff_str
    
    @staticmethod
    def normalize_memory_type(memory_type):
        """Normalize memory type (DDR4, DDR5, etc.)"""
        if not memory_type:
            return None
        
        mem_str = str(memory_type).upper().strip()
        if '/' in mem_str:
            mem_str = mem_str.split('/')[0].strip()
        
        memory_type_map = {
            'DDR4': 'DDR4',
            'DDR5': 'DDR5',
            'DDR3': 'DDR3',
            'DDR': 'DDR',
        }
        
        for key, value in memory_type_map.items():
            if key in mem_str:
                return value
        
        return mem_str
    
    @staticmethod
    def normalize_memory_form_factor(form_factor):
        """Normalize memory form factor (DIMM, SO-DIMM, etc.)"""
        if not form_factor:
            return None
        
        ff_str = str(form_factor).upper().strip()
        
        form_factor_map = {
            'DIMM': 'DIMM',
            'UDIMM': 'DIMM',  # Unbuffered DIMM is still DIMM
            'SO-DIMM': 'SO-DIMM',
            'SODIMM': 'SO-DIMM',
            'SO DIMM': 'SO-DIMM',
            'RDIMM': 'RDIMM',  # Registered DIMM
            'LRDIMM': 'LRDIMM',  # Load-Reduced DIMM
        }
        
        for key, value in form_factor_map.items():
            if key in ff_str:
                return value
        
        return ff_str
    
    @staticmethod
    def filter_characteristics(characteristics):
        """Filter motherboard characteristics"""
        filtered = {}
        
        important_fields = {
            'socket': MotherboardFilter.normalize_socket,
            'form_factor': MotherboardFilter.normalize_form_factor,
            'chipset': CharacteristicFilter.normalize_value,
            'memory_type': MotherboardFilter.normalize_memory_type,
            'memory_form_factor': MotherboardFilter.normalize_memory_form_factor,
        }
        
        for field, normalizer in important_fields.items():
            if field in characteristics:
                value = characteristics[field]
                normalized = normalizer(value)
                if normalized is not None:
                    filtered[field] = normalized
        
        return filtered


class GraphicsCardFilter(CharacteristicFilter):
    """Filter for graphics card characteristics"""
    
    REQUIRED_CHARACTERISTICS = {'gpu_model', 'memory_size', 'memory_type'}
    IMPORTANT_CHARACTERISTICS = {'gpu_model', 'architecture', 'base_clock', 'boost_clock', 'memory_size', 'memory_type', 'memory_bus', 'power_consumption'}
    
    @staticmethod
    def normalize_gpu_model(gpu_model):
        """Normalize GPU model (e.g., GeForce RTX 4080, Radeon RX 7800 XT)"""
        if not gpu_model:
            return None
        
        model_str = str(gpu_model).strip()
        
        # Remove common prefixes
        model_str = re.sub(r'(NVIDIA|INTEL|AMD)\s*', '', model_str, flags=re.IGNORECASE)
        
        return model_str.strip()
    
    @staticmethod
    def normalize_memory_size(size):
        """Normalize memory size to GB"""
        return CharacteristicFilter.normalize_value(size, 'int')
    
    @staticmethod
    def normalize_memory_type(memory_type):
        """Normalize VRAM type (GDDR6, GDDR6X, HBM, etc.)"""
        if not memory_type:
            return None
        
        mem_str = str(memory_type).upper().strip()
        
        memory_type_map = {
            'GDDR7': 'GDDR7',
            'GDDR6X': 'GDDR6X',
            'GDDR6': 'GDDR6',
            'GDDR5X': 'GDDR5X',
            'GDDR5': 'GDDR5',
            'HBM2': 'HBM2',
            'HBM': 'HBM',
        }
        
        for key, value in memory_type_map.items():
            if key in mem_str:
                return value
        
        return mem_str
    
    @staticmethod
    def filter_characteristics(characteristics):
        """Filter graphics card characteristics"""
        filtered = {}
        
        important_fields = {
            'gpu_model': GraphicsCardFilter.normalize_gpu_model,
            'architecture': CharacteristicFilter.normalize_value,
            'base_clock': ProcessorFilter.normalize_clock,
            'boost_clock': ProcessorFilter.normalize_clock,
            'memory_size': GraphicsCardFilter.normalize_memory_size,
            'memory_type': GraphicsCardFilter.normalize_memory_type,
            'memory_bus': CharacteristicFilter.normalize_value,
            'power_consumption': CharacteristicFilter.normalize_value,
            'length': CoolerFilter.normalize_height,
        }
        
        for field, normalizer in important_fields.items():
            if field in characteristics:
                value = characteristics[field]
                normalized = normalizer(value)
                if normalized is not None:
                    filtered[field] = normalized
        
        return filtered


class RAMFilter(CharacteristicFilter):
    """Filter for RAM characteristics"""
    
    REQUIRED_CHARACTERISTICS = {'memory_size', 'memory_type', 'memory_form_factor'}
    IMPORTANT_CHARACTERISTICS = {'memory_size', 'memory_type', 'memory_form_factor', 'memory_clock', 'memory_bus'}
    
    @staticmethod
    def normalize_memory_size(size):
        """Normalize memory size to GB"""
        if not size:
            return None
        
        size_str = str(size).strip()
        
        # Try to extract GB
        gb_match = re.search(r'(\d+)\s*(ГБ|GB)', size_str, re.IGNORECASE)
        if gb_match:
            return int(gb_match.group(1))
        
        # Try to extract numbers
        num_match = re.search(r'(\d+)', size_str)
        if num_match:
            return int(num_match.group(1))
        
        return None
    
    @staticmethod
    def normalize_memory_type(memory_type):
        """Normalize memory type (DDR4, DDR5, etc.)"""
        return MotherboardFilter.normalize_memory_type(memory_type)
    
    @staticmethod
    def normalize_memory_form_factor(form_factor):
        """Normalize memory form factor"""
        return MotherboardFilter.normalize_memory_form_factor(form_factor)
    
    @staticmethod
    def filter_characteristics(characteristics):
        """Filter RAM characteristics"""
        filtered = {}
        
        important_fields = {
            'memory_size': RAMFilter.normalize_memory_size,
            'memory_type': RAMFilter.normalize_memory_type,
            'memory_form_factor': RAMFilter.normalize_memory_form_factor,
            'memory_clock': ProcessorFilter.normalize_clock,
            'memory_bus': CharacteristicFilter.normalize_value,
        }
        
        for field, normalizer in important_fields.items():
            if field in characteristics:
                value = characteristics[field]
                normalized = normalizer(value)
                if normalized is not None:
                    filtered[field] = normalized
        
        return filtered


class HardDriveFilter(CharacteristicFilter):
    """Filter for hard drive/SSD characteristics"""
    
    REQUIRED_CHARACTERISTICS = {'storage_capacity', 'interface'}
    IMPORTANT_CHARACTERISTICS = {'storage_capacity', 'interface', 'read_speed', 'write_speed', 'form_factor'}
    
    @staticmethod
    def normalize_storage_capacity(capacity):
        """Normalize storage capacity to GB"""
        if not capacity:
            return None
        
        capacity_str = str(capacity).strip()
        
        # Try TB first
        tb_match = re.search(r'(\d+\.?\d*)\s*(ТБ|TB)', capacity_str, re.IGNORECASE)
        if tb_match:
            return int(float(tb_match.group(1)) * 1000)
        
        # Try GB
        gb_match = re.search(r'(\d+)\s*(ГБ|GB)', capacity_str, re.IGNORECASE)
        if gb_match:
            return int(gb_match.group(1))
        
        # Try numbers
        num_match = re.search(r'(\d+)', capacity_str)
        if num_match:
            value = int(num_match.group(1))
            # If less than 100, assume TB
            if value < 100:
                return value * 1000
            return value
        
        return None
    
    @staticmethod
    def normalize_interface(interface):
        """Normalize interface type (SATA, NVMe, M.2, etc.)"""
        if not interface:
            return None
        
        interface_str = str(interface).upper().strip()
        
        interface_map = {
            'SATA': 'SATA',
            'NVME': 'NVMe',
            'M.2': 'M.2',
            'M2': 'M.2',
            'PCIE': 'PCIe',
            'PCI-E': 'PCIe',
            'IDE': 'IDE',
        }
        
        for key, value in interface_map.items():
            if key in interface_str:
                return value
        
        return interface_str
    
    @staticmethod
    def filter_characteristics(characteristics):
        """Filter hard drive characteristics"""
        filtered = {}
        
        important_fields = {
            'storage_capacity': HardDriveFilter.normalize_storage_capacity,
            'interface': HardDriveFilter.normalize_interface,
            'read_speed': CharacteristicFilter.normalize_value,
            'write_speed': CharacteristicFilter.normalize_value,
            'form_factor': CharacteristicFilter.normalize_value,
        }
        
        for field, normalizer in important_fields.items():
            if field in characteristics:
                value = characteristics[field]
                normalized = normalizer(value)
                if normalized is not None:
                    filtered[field] = normalized
        
        return filtered


class PowerSupplyFilter(CharacteristicFilter):
    """Filter for power supply characteristics"""
    
    REQUIRED_CHARACTERISTICS = {'wattage'}
    IMPORTANT_CHARACTERISTICS = {'wattage', 'efficiency_rating', 'modular_type', 'connectors'}
    
    @staticmethod
    def normalize_wattage(wattage):
        """Normalize wattage (extract numbers)"""
        return CharacteristicFilter.normalize_value(wattage, 'int')
    
    @staticmethod
    def normalize_efficiency(efficiency):
        """Normalize efficiency rating (80+, 80+ Gold, etc.)"""
        if not efficiency:
            return None
        
        eff_str = str(efficiency).strip()
        
        efficiency_map = {
            '80+ PLATINUM': '80+ Platinum',
            '80+ GOLD': '80+ Gold',
            '80+ SILVER': '80+ Silver',
            '80+ BRONZE': '80+ Bronze',
            '80+': '80+',
            'PLATINUM': '80+ Platinum',
            'GOLD': '80+ Gold',
            'SILVER': '80+ Silver',
            'BRONZE': '80+ Bronze',
        }
        
        eff_upper = eff_str.upper()
        for key, value in efficiency_map.items():
            if key in eff_upper:
                return value
        
        return eff_str
    
    @staticmethod
    def filter_characteristics(characteristics):
        """Filter power supply characteristics"""
        filtered = {}
        
        important_fields = {
            'wattage': PowerSupplyFilter.normalize_wattage,
            'efficiency_rating': PowerSupplyFilter.normalize_efficiency,
            'modular_type': CharacteristicFilter.normalize_value,
            'connectors': CharacteristicFilter.normalize_value,
        }
        
        for field, normalizer in important_fields.items():
            if field in characteristics:
                value = characteristics[field]
                normalized = normalizer(value)
                if normalized is not None:
                    filtered[field] = normalized
        
        return filtered


class CoolerFilter(CharacteristicFilter):
    """Filter for CPU cooler characteristics"""
    
    REQUIRED_CHARACTERISTICS = {'cooling_type'}
    IMPORTANT_CHARACTERISTICS = {'cooling_type', 'cooler_height', 'fan_count', 'power_consumption'}
    
    @staticmethod
    def normalize_cooling_type(cooling_type):
        """Normalize cooling type (Air, Liquid, etc.)"""
        if not cooling_type:
            return None
        
        type_str = str(cooling_type).upper().strip()
        
        cooling_map = {
            'AIR': 'Air',
            'LIQUID': 'Liquid',
            'PASSIVE': 'Passive',
            'ВОЗДУШ': 'Air',
            'ЖИДКОСТ': 'Liquid',
            'ВОДЯН': 'Liquid',
            'АКТИВН': 'Air',
        }
        
        for key, value in cooling_map.items():
            if key in type_str:
                return value
        
        return type_str
    
    @staticmethod
    def normalize_height(height):
        """Normalize height to mm"""
        if not height:
            return None
        
        height_str = str(height).strip()
        
        # Try to extract mm
        mm_match = re.search(r'(\d+)\s*(мм|mm)', height_str, re.IGNORECASE)
        if mm_match:
            return int(mm_match.group(1))
        
        # Try to extract numbers
        num_match = re.search(r'(\d+)', height_str)
        if num_match:
            return int(num_match.group(1))
        
        return None
    
    @staticmethod
    def filter_characteristics(characteristics):
        """Filter cooler characteristics"""
        filtered = {}
        
        important_fields = {
            'cooling_type': CoolerFilter.normalize_cooling_type,
            'cooler_height': CoolerFilter.normalize_height,
            'fan_count': CharacteristicFilter.normalize_value,
            'power_consumption': CharacteristicFilter.normalize_value,
        }
        
        for field, normalizer in important_fields.items():
            if field in characteristics:
                value = characteristics[field]
                normalized = normalizer(value)
                if normalized is not None:
                    filtered[field] = normalized
        
        return filtered


class CaseFilter(CharacteristicFilter):
    """Filter for case characteristics"""
    
    REQUIRED_CHARACTERISTICS = {'case_size'}
    IMPORTANT_CHARACTERISTICS = {'case_size', 'supported_form_factors', 'max_gpu_length', 'max_cooler_height'}
    
    @staticmethod
    def normalize_case_size(case_size):
        """Normalize case size (Full Tower, Mid Tower, Mini Tower, SFF)"""
        if not case_size:
            return None
        
        size_str = str(case_size).upper().strip()
        
        size_map = {
            'FULL TOWER': 'Full Tower',
            'MID TOWER': 'Mid Tower',
            'MINI TOWER': 'Mini Tower',
            'SMALL FORM FACTOR': 'SFF',
            'SFF': 'SFF',
            'ATX': 'Full Tower',
            'MICRO-ATX': 'Mid Tower',
            'MINI-ITX': 'Mini Tower',
        }
        
        for key, value in size_map.items():
            if key in size_str:
                return value
        
        return size_str
    
    @staticmethod
    def normalize_supported_form_factors(form_factors):
        """Normalize supported form factors"""
        if isinstance(form_factors, str):
            return form_factors
        elif isinstance(form_factors, list):
            return ', '.join(str(f) for f in form_factors)
        return str(form_factors) if form_factors else None
    
    @staticmethod
    def normalize_dimensions(dimension):
        """Normalize dimensions to mm"""
        if not dimension:
            return None
        
        return CoolerFilter.normalize_height(dimension)  # Same logic for extracting mm
    
    @staticmethod
    def filter_characteristics(characteristics):
        """Filter case characteristics"""
        filtered = {}
        
        important_fields = {
            'case_size': CaseFilter.normalize_case_size,
            'supported_form_factors': CaseFilter.normalize_supported_form_factors,
            'max_gpu_length': CaseFilter.normalize_dimensions,
            'max_cooler_height': CaseFilter.normalize_dimensions,
        }
        
        for field, normalizer in important_fields.items():
            if field in characteristics:
                value = characteristics[field]
                normalized = normalizer(value)
                if normalized is not None:
                    filtered[field] = normalized
        
        return filtered


# Mapping of product types to their filters
FILTER_MAP = {
    'processor': ProcessorFilter,
    'motherboard': MotherboardFilter,
    'graphics_card': GraphicsCardFilter,
    'ram': RAMFilter,
    'hard_drive': HardDriveFilter,
    'power_supply': PowerSupplyFilter,
    'cooler': CoolerFilter,
    'case': CaseFilter,
}


def apply_filter(product_type, characteristics):
    """
    Apply appropriate filter based on product type
    
    Args:
        product_type (str): Type of product (processor, motherboard, etc.)
        characteristics (dict): Raw characteristics dictionary
        
    Returns:
        dict: Filtered and normalized characteristics
    """
    if not characteristics:
        return {}

    prepared = prepare_characteristics(characteristics, product_type)

    if product_type not in FILTER_MAP:
        return prepared
    
    filter_class = FILTER_MAP[product_type]
    return filter_class.filter_characteristics(prepared)


def get_required_characteristics(product_type):
    """
    Get required characteristics for a product type
    
    Args:
        product_type (str): Type of product
        
    Returns:
        set: Set of required characteristic field names
    """
    if product_type not in FILTER_MAP:
        return set()
    
    filter_class = FILTER_MAP[product_type]
    return filter_class.REQUIRED_CHARACTERISTICS


def get_important_characteristics(product_type):
    """
    Get important characteristics for a product type
    
    Args:
        product_type (str): Type of product
        
    Returns:
        set: Set of important characteristic field names
    """
    if product_type not in FILTER_MAP:
        return set()
    
    filter_class = FILTER_MAP[product_type]
    return filter_class.IMPORTANT_CHARACTERISTICS
