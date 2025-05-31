from app import create_app, db
from app.models.models import UnifiedProduct
import json

def test_unified_model():
    """Test the UnifiedProduct model with a simple example"""
    app = create_app()
    with app.app_context():
        # Create the table if it doesn't exist
        db.create_all()
        
        # Create a test GPU product
        test_gpu = UnifiedProduct(
            product_name="Test GPU",
            price_discounted=299.99,
            price_original=349.99,
            rating=4.5,
            number_of_reviews=10,
            vendor="test",
            product_url="https://example.com/test-gpu",
            availability=True,
            product_type="graphics_card"
        )
        
        # Set JSON fields
        test_gpu.set_images(["https://example.com/image1.jpg", "https://example.com/image2.jpg"])
        test_gpu.set_characteristics({
            "gpu_model": "Test GPU",
            "memory_size": 8,
            "memory_type": "GDDR6",
            "base_clock": 1500,
            "boost_clock": 1800,
            "power_consumption": 250,
            "socket": "PCIe 4.0",
            "length": 300  # 300mm length
        })
        test_gpu.set_category(["Hardware", "GPU"])
        
        # Create a test motherboard product
        test_motherboard = UnifiedProduct(
            product_name="Test Motherboard",
            price_discounted=199.99,
            price_original=229.99,
            rating=4.2,
            number_of_reviews=15,
            vendor="test",
            product_url="https://example.com/test-motherboard",
            availability=True,
            product_type="motherboard"
        )
        
        # Set JSON fields
        test_motherboard.set_images(["https://example.com/mb1.jpg"])
        test_motherboard.set_characteristics({
            "socket": "LGA1700",
            "chipset": "Z690",
            "memory_type": "DDR5",
            "form_factor": "ATX"
        })
        test_motherboard.set_category(["Hardware", "Motherboard"])
        
        # Create a test CPU product
        test_cpu = UnifiedProduct(
            product_name="Test CPU",
            price_discounted=399.99,
            price_original=449.99,
            rating=4.8,
            number_of_reviews=25,
            vendor="test",
            product_url="https://example.com/test-cpu",
            availability=True,
            product_type="processor"
        )
        
        # Set JSON fields
        test_cpu.set_images(["https://example.com/cpu1.jpg"])
        test_cpu.set_characteristics({
            "socket": "LGA1700",
            "core_count": 8,
            "thread_count": 16,
            "base_clock": 3500,
            "boost_clock": 5000,
            "power_consumption": 125
        })
        test_cpu.set_category(["Hardware", "CPU"])
        
        # Create a test case product
        test_case = UnifiedProduct(
            product_name="Test Case",
            price_discounted=99.99,
            price_original=119.99,
            rating=4.0,
            number_of_reviews=8,
            vendor="test",
            product_url="https://example.com/test-case",
            availability=True,
            product_type="case"
        )
        
        # Set JSON fields
        test_case.set_images(["https://example.com/case1.jpg"])
        test_case.set_characteristics({
            "supported_form_factors": ["ATX", "mATX", "ITX"],
            "max_gpu_length": 350,  # 350mm max GPU length
            "max_cooler_height": 170
        })
        test_case.set_category(["Hardware", "Case"])
        
        # Add to database
        db.session.add_all([test_gpu, test_motherboard, test_cpu, test_case])
        db.session.commit()
        
        # Query the database
        products = UnifiedProduct.query.all()
        print(f"Found {len(products)} products in the database")
        
        # Test compatibility checks
        print("\nTesting compatibility checks:")
        
        # CPU and Motherboard - should be compatible (same socket)
        cpu = UnifiedProduct.query.filter_by(product_type="processor").first()
        motherboard = UnifiedProduct.query.filter_by(product_type="motherboard").first()
        print(f"CPU and Motherboard compatible: {cpu.is_compatible_with(motherboard)}")
        
        # GPU and Case - should be compatible (GPU length < max length)
        gpu = UnifiedProduct.query.filter_by(product_type="graphics_card").first()
        case = UnifiedProduct.query.filter_by(product_type="case").first()
        print(f"GPU and Case compatible: {gpu.is_compatible_with(case)}")
        
        # Test incompatible CPU
        incompatible_cpu = UnifiedProduct(
            product_name="Incompatible CPU",
            product_type="processor",
            vendor="test",
            product_url="https://example.com/incompatible-cpu"
        )
        incompatible_cpu.set_characteristics({"socket": "AM4"})  # Different socket
        print(f"Incompatible CPU and Motherboard: {incompatible_cpu.is_compatible_with(motherboard)}")
        
        # Test incompatible GPU (too long)
        long_gpu = UnifiedProduct(
            product_name="Long GPU",
            product_type="graphics_card",
            vendor="test",
            product_url="https://example.com/long-gpu"
        )
        long_gpu.set_characteristics({"length": 400})  # 400mm is longer than case max (350mm)
        print(f"Long GPU and Case compatible: {long_gpu.is_compatible_with(case)}")
        
        # Clean up
        db.session.delete(test_gpu)
        db.session.delete(test_motherboard)
        db.session.delete(test_cpu)
        db.session.delete(test_case)
        db.session.commit()
        print("\nTest completed successfully!")

if __name__ == "__main__":
    test_unified_model() 