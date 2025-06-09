from flask_wtf import FlaskForm
from wtforms import SelectField, FloatField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class ProductComparisonForm(FlaskForm):
    """Форма для сравнения товаров"""
    
    category = SelectField(
        'Категория товаров',
        choices=[
            ('', 'Выберите категорию...'),
            ('ram', 'Оперативная память'),
            ('gpu', 'Видеокарты'),
            ('cpu', 'Процессоры'),
            ('storage', 'Накопители (SSD, HDD)'),
            ('motherboard', 'Материнские платы'),
            ('psu', 'Блоки питания'),
            ('cooler', 'Кулеры для процессоров'),
            ('case', 'Корпуса')
        ],
        validators=[DataRequired(message='Выберите категорию товаров')],
        render_kw={'placeholder': 'Выберите категорию...'}
    )
    
    threshold = FloatField(
        'Порог сходства',
        validators=[
            DataRequired(message='Укажите порог сходства'),
            NumberRange(min=0.1, max=1.0, message='Порог должен быть от 0.1 до 1.0')
        ],
        default=0.6,
        render_kw={'step': 0.05, 'min': 0.1, 'max': 1.0}
    )
    
    submit = SubmitField('Найти совпадения') 