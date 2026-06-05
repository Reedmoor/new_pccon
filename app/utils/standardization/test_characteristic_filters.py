"""
Test and demonstration script for characteristic filters.
Shows how filters normalize characteristics from different vendors.
"""

import json
import sys
from pathlib import Path

# Add the project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.utils.standardization.characteristic_filters import (
    apply_filter,
    get_required_characteristics,
    get_important_characteristics,
    ProcessorFilter,
    MotherboardFilter,
    GraphicsCardFilter,
    RAMFilter,
    HardDriveFilter,
    PowerSupplyFilter,
    CoolerFilter,
    CaseFilter,
)


def test_processor_filter():
    """Test processor characteristic filtering"""
    print("\n" + "="*50)
    print("PROCESSOR FILTER TEST")
    print("="*50)
    
    # Example: Different vendors have different socket formats
    test_cases = [
        {
            "socket": "Intel LGA 1700",
            "core_count": "10 cores",
            "thread_count": "20",
            "base_clock": "3.2 ГГц",
            "boost_clock": "5.6 GHz",
            "l3_cache": "24 МБ",
            "power_consumption": "125 Вт"
        },
        {
            "socket": "AM5",
            "core_count": "16",
            "thread_count": "32 потока",
            "base_clock": "3.8 GHz",
            "boost_clock": "5.6 ГГц",
            "l3_cache": "128MB",
            "power_consumption": "170W"
        }
    ]
    
    for i, chars in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        print(f"Input: {chars}")
        filtered = apply_filter('processor', chars)
        print(f"Output: {filtered}")
        
    print(f"\nRequired characteristics: {ProcessorFilter.REQUIRED_CHARACTERISTICS}")
    print(f"Important characteristics: {ProcessorFilter.IMPORTANT_CHARACTERISTICS}")


def test_motherboard_filter():
    """Test motherboard characteristic filtering"""
    print("\n" + "="*50)
    print("MOTHERBOARD FILTER TEST")
    print("="*50)
    
    test_cases = [
        {
            "socket": "Intel LGA1700",
            "form_factor": "ATX",
            "chipset": "Z790",
            "memory_type": "DDR5",
            "memory_form_factor": "DIMM"
        },
        {
            "socket": "AMD Socket AM5",
            "form_factor": "Micro-ATX",
            "chipset": "X870",
            "memory_type": "DDR5",
            "memory_form_factor": "SO-DIMM"
        }
    ]
    
    for i, chars in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        print(f"Input: {chars}")
        filtered = apply_filter('motherboard', chars)
        print(f"Output: {filtered}")
        
    print(f"\nRequired characteristics: {MotherboardFilter.REQUIRED_CHARACTERISTICS}")
    print(f"Important characteristics: {MotherboardFilter.IMPORTANT_CHARACTERISTICS}")


def test_graphics_card_filter():
    """Test graphics card characteristic filtering"""
    print("\n" + "="*50)
    print("GRAPHICS CARD FILTER TEST")
    print("="*50)
    
    test_cases = [
        {
            "gpu_model": "NVIDIA GeForce RTX 4080",
            "architecture": "Ada",
            "base_clock": "2505 МГц",
            "boost_clock": "2700 MHz",
            "memory_size": "16GB",
            "memory_type": "GDDR6X",
            "memory_bus": "256 bit",
            "power_consumption": "320W"
        },
        {
            "gpu_model": "AMD Radeon RX 7800 XT",
            "architecture": "RDNA 3",
            "memory_size": "16 ГБ",
            "memory_type": "GDDR6",
            "memory_bus": "256 bit",
            "power_consumption": "250 Вт"
        }
    ]
    
    for i, chars in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        print(f"Input: {chars}")
        filtered = apply_filter('graphics_card', chars)
        print(f"Output: {filtered}")
        
    print(f"\nRequired characteristics: {GraphicsCardFilter.REQUIRED_CHARACTERISTICS}")
    print(f"Important characteristics: {GraphicsCardFilter.IMPORTANT_CHARACTERISTICS}")


def test_ram_filter():
    """Test RAM characteristic filtering"""
    print("\n" + "="*50)
    print("RAM FILTER TEST")
    print("="*50)
    
    test_cases = [
        {
            "memory_size": "32 ГБ",
            "memory_type": "DDR5",
            "memory_form_factor": "DIMM",
            "memory_clock": "6000 МГц",
            "memory_bus": "192 bit"
        },
        {
            "memory_size": "16GB",
            "memory_type": "DDR4",
            "memory_form_factor": "UDIMM",
            "memory_clock": "3200 MHz"
        }
    ]
    
    for i, chars in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        print(f"Input: {chars}")
        filtered = apply_filter('ram', chars)
        print(f"Output: {filtered}")
        
    print(f"\nRequired characteristics: {RAMFilter.REQUIRED_CHARACTERISTICS}")
    print(f"Important characteristics: {RAMFilter.IMPORTANT_CHARACTERISTICS}")


def test_hard_drive_filter():
    """Test hard drive characteristic filtering"""
    print("\n" + "="*50)
    print("HARD DRIVE FILTER TEST")
    print("="*50)
    
    test_cases = [
        {
            "storage_capacity": "2 ТБ",
            "interface": "NVMe M.2",
            "read_speed": "7000 MB/s",
            "write_speed": "6000 MB/s",
            "form_factor": "2280"
        },
        {
            "storage_capacity": "4000GB",
            "interface": "SATA",
            "read_speed": "550 MB/s",
            "write_speed": "500 MB/s"
        }
    ]
    
    for i, chars in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        print(f"Input: {chars}")
        filtered = apply_filter('hard_drive', chars)
        print(f"Output: {filtered}")
        
    print(f"\nRequired characteristics: {HardDriveFilter.REQUIRED_CHARACTERISTICS}")
    print(f"Important characteristics: {HardDriveFilter.IMPORTANT_CHARACTERISTICS}")


def test_power_supply_filter():
    """Test power supply characteristic filtering"""
    print("\n" + "="*50)
    print("POWER SUPPLY FILTER TEST")
    print("="*50)
    
    test_cases = [
        {
            "wattage": "1000 Вт",
            "efficiency_rating": "80+ Platinum",
            "modular_type": "Full Modular",
            "connectors": "PCIe 8-pin x4"
        },
        {
            "wattage": "850W",
            "efficiency_rating": "Gold",
            "modular_type": "Semi-Modular"
        }
    ]
    
    for i, chars in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        print(f"Input: {chars}")
        filtered = apply_filter('power_supply', chars)
        print(f"Output: {filtered}")
        
    print(f"\nRequired characteristics: {PowerSupplyFilter.REQUIRED_CHARACTERISTICS}")
    print(f"Important characteristics: {PowerSupplyFilter.IMPORTANT_CHARACTERISTICS}")


def test_cooler_filter():
    """Test cooler characteristic filtering"""
    print("\n" + "="*50)
    print("COOLER FILTER TEST")
    print("="*50)
    
    test_cases = [
        {
            "cooling_type": "Air",
            "cooler_height": "163 мм",
            "fan_count": "2",
            "power_consumption": "5W"
        },
        {
            "cooling_type": "Liquid",
            "fan_count": "3 fans"
        }
    ]
    
    for i, chars in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        print(f"Input: {chars}")
        filtered = apply_filter('cooler', chars)
        print(f"Output: {filtered}")
        
    print(f"\nRequired characteristics: {CoolerFilter.REQUIRED_CHARACTERISTICS}")
    print(f"Important characteristics: {CoolerFilter.IMPORTANT_CHARACTERISTICS}")


def test_case_filter():
    """Test case characteristic filtering"""
    print("\n" + "="*50)
    print("CASE FILTER TEST")
    print("="*50)
    
    test_cases = [
        {
            "case_size": "Mid Tower",
            "supported_form_factors": ["ATX", "Micro-ATX", "Mini-ITX"],
            "max_gpu_length": "330 мм",
            "max_cooler_height": "170mm"
        },
        {
            "case_size": "SFF",
            "max_gpu_length": "280 мм"
        }
    ]
    
    for i, chars in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        print(f"Input: {chars}")
        filtered = apply_filter('case', chars)
        print(f"Output: {filtered}")
        
    print(f"\nRequired characteristics: {CaseFilter.REQUIRED_CHARACTERISTICS}")
    print(f"Important characteristics: {CaseFilter.IMPORTANT_CHARACTERISTICS}")


def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("CHARACTERISTIC FILTERS - DEMONSTRATION")
    print("="*50)
    
    test_processor_filter()
    test_motherboard_filter()
    test_graphics_card_filter()
    test_ram_filter()
    test_hard_drive_filter()
    test_power_supply_filter()
    test_cooler_filter()
    test_case_filter()
    
    print("\n" + "="*50)
    print("ALL TESTS COMPLETED")
    print("="*50)


if __name__ == "__main__":
    main()
