from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField, IntegerField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional, URL

class UserForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[Length(min=6)])
    role = SelectField('Роль', choices=[('user', 'Пользователь'), ('admin', 'Администратор')])
    submit = SubmitField('Сохранить')

class UnifiedProductForm(FlaskForm):
    """
    A unified form for all product types with fields for different component characteristics.
    Fields will be shown/hidden in the template based on product type.
    """
    # Basic product information (common to all types)
    product_name = StringField('Название продукта', validators=[DataRequired()])
    price_discounted = FloatField('Цена со скидкой', validators=[Optional()])
    price_original = FloatField('Исходная цена', validators=[Optional()])
    vendor = StringField('Производитель/Вендор', validators=[DataRequired()])
    product_url = StringField('URL продукта', validators=[Optional(), URL()])
    image_url = StringField('URL изображения', validators=[Optional(), URL()])
    
    # Common characteristics
    brand = StringField('Бренд', validators=[Optional()])
    model = StringField('Модель', validators=[Optional()])
    
    # Motherboard specific
    socket = StringField('Сокет', validators=[Optional()])
    chipset = StringField('Чипсет', validators=[Optional()])
    form_factor = StringField('Форм-фактор', validators=[Optional()])
    
    # Processor specific
    core_count = IntegerField('Количество ядер', validators=[Optional()])
    thread_count = IntegerField('Количество потоков', validators=[Optional()])
    
    # Graphics card specific
    gpu_model = StringField('Модель GPU', validators=[Optional()])
    memory_size = IntegerField('Объем памяти (ГБ)', validators=[Optional()])
    memory_type = StringField('Тип памяти', validators=[Optional()])
    memory_clock = IntegerField('Частота памяти (МГц)', validators=[Optional()])
    memory_bus = IntegerField('Шина памяти (бит)', validators=[Optional()])
    
    # Common clock speeds
    base_clock = IntegerField('Базовая частота (МГц)', validators=[Optional()])
    boost_clock = IntegerField('Турбо частота (МГц)', validators=[Optional()])
    
    # Power related
    power_consumption = IntegerField('Энергопотребление (Вт)', validators=[Optional()])
    wattage = IntegerField('Мощность (Вт)', validators=[Optional()]) # For power supplies
    certification = StringField('Сертификация', validators=[Optional()]) # For power supplies
    
    # Storage specific
    storage_capacity = IntegerField('Объем накопителя (ГБ)', validators=[Optional()])
    interface = StringField('Интерфейс', validators=[Optional()])
    read_speed = IntegerField('Скорость чтения (МБ/с)', validators=[Optional()])
    write_speed = IntegerField('Скорость записи (МБ/с)', validators=[Optional()])
    
    # RAM specific
    module_count = IntegerField('Количество модулей', validators=[Optional()])
    
    # Cooler specific
    cooling_type = StringField('Тип охлаждения', validators=[Optional()])
    fan_count = IntegerField('Количество вентиляторов', validators=[Optional()])
    
    # Case specific
    case_size = StringField('Размер корпуса', validators=[Optional()])
    supported_form_factors = StringField('Поддерживаемые форм-факторы (через запятую)', validators=[Optional()])
    max_gpu_length = IntegerField('Макс. длина видеокарты (мм)', validators=[Optional()])
    max_cooler_height = IntegerField('Макс. высота кулера (мм)', validators=[Optional()])
    
    # Physical dimensions
    length = IntegerField('Длина (мм)', validators=[Optional()])
    width = IntegerField('Ширина (мм)', validators=[Optional()])
    height = IntegerField('Высота (мм)', validators=[Optional()])
    
    submit = SubmitField('Сохранить') 