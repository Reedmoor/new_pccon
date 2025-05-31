from app import create_app, db
from app.models.models import (
    User, Motherboard, PowerSupply, Processor, 
    GraphicsCard, Cooler, RAM, HardDrive, Case, Configuration
)
from werkzeug.security import generate_password_hash

app = create_app()

def seed_database():
    """Заполняет базу данных тестовыми данными"""
    with app.app_context():
        print("Начало заполнения базы данных...")
        
        # Удаление существующих данных
        db.session.query(Configuration).delete()
        db.session.query(User).delete()
        db.session.query(Motherboard).delete()
        db.session.query(PowerSupply).delete()
        db.session.query(Processor).delete()
        db.session.query(GraphicsCard).delete()
        db.session.query(Cooler).delete()
        db.session.query(RAM).delete()
        db.session.query(HardDrive).delete()
        db.session.query(Case).delete()
        db.session.commit()
        
        # Создание пользователей
        admin = User(
            name="Администратор",
            email="admin@example.com",
            password_hash=generate_password_hash("admin123"),
            role="admin"
        )
        
        user = User(
            name="Пользователь",
            email="user@example.com",
            password_hash=generate_password_hash("user123"),
            role="user"
        )
        
        db.session.add_all([admin, user])
        db.session.commit()
        
        print("Пользователи созданы!")
        
        # Материнские платы
        motherboards = [
            Motherboard(
                name="Asus ROG STRIX Z690-F GAMING WIFI",
                price=32000,
                form="ATX",
                soket="LGA1700",
                memory_type="DDR4",
                interface="PCIe 5.0, SATA III"
            ),
            Motherboard(
                name="MSI MAG B550 TOMAHAWK",
                price=15000,
                form="ATX",
                soket="AM4",
                memory_type="DDR4",
                interface="PCIe 4.0, SATA III"
            ),
            Motherboard(
                name="Gigabyte Z690 AORUS ELITE AX",
                price=28000,
                form="ATX",
                soket="LGA1700",
                memory_type="DDR5",
                interface="PCIe 5.0, SATA III"
            )
        ]
        
        db.session.add_all(motherboards)
        db.session.commit()
        
        print("Материнские платы добавлены!")
        
        # Процессоры
        processors = [
            Processor(
                name="AMD Ryzen 5 5600X",
                price=17990,
                soket="AM4",
                base_clock=3.7,
                turbo_clock=4.6,
                cores=6,
                threads=12,
                power_use=65
            ),
            Processor(
                name="AMD Ryzen 7 5800X",
                price=27990,
                soket="AM4",
                base_clock=3.8,
                turbo_clock=4.7,
                cores=8,
                threads=16,
                power_use=105
            ),
            Processor(
                name="Intel Core i5-12600K",
                price=22990,
                soket="LGA1700",
                base_clock=3.7,
                turbo_clock=4.9,
                cores=6,
                threads=12,
                power_use=125
            ),
            Processor(
                name="Intel Core i7-12700K",
                price=34990,
                soket="LGA1700",
                base_clock=3.6,
                turbo_clock=4.9,
                cores=8,
                threads=16,
                power_use=125
            )
        ]
        
        db.session.add_all(processors)
        db.session.commit()
        
        print("Процессоры добавлены!")
        
        # Видеокарты
        graphics_cards = [
            GraphicsCard(
                name="NVIDIA GeForce RTX 3060",
                price=39990,
                frequency=1.32,
                soket="PCIe 4.0",
                power_use=170
            ),
            GraphicsCard(
                name="NVIDIA GeForce RTX 3070",
                price=59990,
                frequency=1.5,
                soket="PCIe 4.0",
                power_use=220
            ),
            GraphicsCard(
                name="AMD Radeon RX 6700 XT",
                price=54990,
                frequency=2.42,
                soket="PCIe 4.0",
                power_use=230
            )
        ]
        
        db.session.add_all(graphics_cards)
        db.session.commit()
        
        print("Видеокарты добавлены!")
        
        # Оперативная память
        rams = [
            RAM(
                name="Kingston FURY Beast 16GB (2x8GB)",
                price=7990,
                frequency=3200,
                memory_type="DDR4",
                power_use=10,
                capacity=16
            ),
            RAM(
                name="Corsair Vengeance RGB Pro 32GB (2x16GB)",
                price=13990,
                frequency=3600,
                memory_type="DDR4",
                power_use=15,
                capacity=32
            ),
            RAM(
                name="G.Skill Trident Z5 RGB 32GB (2x16GB)",
                price=18990,
                frequency=5600,
                memory_type="DDR5",
                power_use=20,
                capacity=32
            )
        ]
        
        db.session.add_all(rams)
        db.session.commit()
        
        print("Оперативная память добавлена!")
        
        # Блоки питания
        power_supplies = [
            PowerSupply(
                name="Corsair RM750x",
                price=9990,
                power=750,
                type="ATX",
                certificate="80 PLUS Gold"
            ),
            PowerSupply(
                name="EVGA SuperNOVA 850 G5",
                price=12990,
                power=850,
                type="ATX",
                certificate="80 PLUS Gold"
            ),
            PowerSupply(
                name="Cooler Master V1000 Platinum",
                price=16990,
                power=1000,
                type="ATX",
                certificate="80 PLUS Gold"
            )
        ]
        
        db.session.add_all(power_supplies)
        db.session.commit()
        
        print("Блоки питания добавлены!")
        
        # Кулеры
        coolers = [
            Cooler(
                name="Noctua NH-D15",
                price=8990,
                speed=1500,
                power_use=5
            ),
            Cooler(
                name="ARCTIC Liquid Freezer II 240",
                price=9990,
                speed=1800,
                power_use=10
            ),
            Cooler(
                name="Cooler Master Hyper 212 RGB",
                price=3990,
                speed=1600,
                power_use=5
            )
        ]
        
        db.session.add_all(coolers)
        db.session.commit()
        
        print("Кулеры добавлены!")
        
        # Жесткие диски
        hard_drives = [
            HardDrive(
                name="Samsung 970 EVO Plus SSD 1TB",
                price=12990,
                capacity=1000,
                recording=3500,
                reading=3500
            ),
            HardDrive(
                name="WD_BLACK SN850 SSD 2TB",
                price=24990,
                capacity=2000,
                recording=5300,
                reading=7000
            ),
            HardDrive(
                name="Seagate Barracuda 4TB",
                price=7990,
                capacity=4000,
                recording=190,
                reading=190
            )
        ]
        
        db.session.add_all(hard_drives)
        db.session.commit()
        
        print("Жесткие диски добавлены!")
        
        # Корпуса
        cases = [
            Case(
                name="NZXT H510",
                price=7990,
                form="ATX, Micro-ATX, Mini-ITX"
            ),
            Case(
                name="Corsair 4000D Airflow",
                price=8990,
                form="ATX, Micro-ATX, Mini-ITX"
            ),
            Case(
                name="Fractal Design Meshify C",
                price=9990,
                form="ATX, Micro-ATX"
            )
        ]
        
        db.session.add_all(cases)
        db.session.commit()
        
        print("Корпуса добавлены!")
        
        # Создание примера конфигурации
        config = Configuration(
            name="Игровой ПК",
            user_id=user.id,
            motherboard_id=motherboards[0].id,
            cpu_id=processors[0].id,
            gpu_id=graphics_cards[0].id,
            ram_id=rams[0].id,
            hdd_id=hard_drives[0].id,
            supply_id=power_supplies[0].id,
            cooler_id=coolers[0].id,
            frame_id=cases[0].id
        )
        
        db.session.add(config)
        db.session.commit()
        
        print("Пример конфигурации создан!")
        print("База данных успешно заполнена!")

if __name__ == "__main__":
    seed_database() 