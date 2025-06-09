-- Инициализация базы данных для PCConf
-- Этот файл будет выполнен при первом запуске PostgreSQL

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Настройка прав доступа
GRANT ALL PRIVILEGES ON DATABASE pccon_db TO pccon_user;

-- Дополнительные настройки (если нужны)
-- ALTER DATABASE pccon_db SET timezone TO 'UTC'; 