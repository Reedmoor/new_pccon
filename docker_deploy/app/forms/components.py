from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length

class MotherboardForm(FlaskForm):
    name = StringField('Название', validators=[
        DataRequired(message='Имя обязательное поле'),
        Length(min=3, max=100, message='Имя должно быть от 3 до 100 символов')
    ])
    price = FloatField('Цена (руб.)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Цена должна быть положительным числом')
    ])
    form = SelectField('Форм-фактор', choices=[
        ('ATX', 'ATX'),
        ('microATX', 'microATX'),
        ('miniITX', 'mini-ITX'),
        ('E-ATX', 'E-ATX')
    ], validators=[DataRequired()])
    soket = StringField('Сокет', validators=[
        DataRequired(message='Сокет обязательное поле')
    ])
    memory_type = SelectField('Тип памяти', choices=[
        ('DDR3', 'DDR3'),
        ('DDR4', 'DDR4'),
        ('DDR5', 'DDR5')
    ], validators=[DataRequired()])
    interface = StringField('Интерфейсы', validators=[DataRequired()])
    submit = SubmitField('Добавить материнскую плату')

class PowerSupplyForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = FloatField('Цена (руб.)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Цена должна быть положительным числом')
    ])
    power = IntegerField('Мощность (Вт)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Мощность должна быть положительным числом')
    ])
    type = SelectField('Тип', choices=[
        ('ATX', 'ATX'),
        ('SFX', 'SFX'),
        ('SFX-L', 'SFX-L')
    ], validators=[DataRequired()])
    certificate = SelectField('Сертификат', choices=[
        ('80 PLUS', '80 PLUS'),
        ('80 PLUS Bronze', '80 PLUS Bronze'),
        ('80 PLUS Gold', '80 PLUS Gold'),
        ('80 PLUS Platinum', '80 PLUS Platinum'),
        ('80 PLUS Titanium', '80 PLUS Titanium'),
    ], validators=[DataRequired()])
    submit = SubmitField('Добавить блок питания')

class ProcessorForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = FloatField('Цена (руб.)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Цена должна быть положительным числом')
    ])
    soket = StringField('Сокет', validators=[DataRequired()])
    base_clock = FloatField('Базовая частота (ГГц)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Базовая частота должна быть положительным числом')
    ])
    turbo_clock = FloatField('Турбочастота (ГГц)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Турбочастота должна быть положительным числом')
    ])
    cores = IntegerField('Количество ядер', validators=[
        DataRequired(),
        NumberRange(min=0, message='Количество ядер должно быть положительным числом')
    ])
    threads = IntegerField('Количество потоков', validators=[
        DataRequired(),
        NumberRange(min=0, message='Количество потоков должно быть положительным числом')
    ])
    power_use = IntegerField('Потребляемая мощность (Вт)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Потребляемая мощность должна быть положительным числом')
    ])
    submit = SubmitField('Добавить процессор')

class GraphicsCardForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = FloatField('Цена (руб.)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Цена должна быть положительным числом')
    ])
    frequency = FloatField('Частота (МГц)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Частота должна быть положительным числом')
    ])
    soket = StringField('Разъемы', validators=[DataRequired()])
    power_use = IntegerField('Потребляемая мощность (Вт)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Потребляемая мощность должна быть положительным числом')
    ])
    submit = SubmitField('Добавить видеокарту')

class CoolerForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = FloatField('Цена (руб.)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Цена должна быть положительным числом')
    ])
    speed = IntegerField('Скорость вращения (об/мин)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Скорость вращения должна быть положительным числом')
    ])
    power_use = IntegerField('Потребляемая мощность (Вт)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Потребляемая мощность должна быть положительным числом')
    ])
    submit = SubmitField('Добавить кулер')

class RAMForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = FloatField('Цена (руб.)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Цена должна быть положительным числом')
    ])
    frequency = IntegerField('Частота (МГц)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Частота должна быть положительным числом')
    ])
    memory_type = SelectField('Тип памяти', choices=[
        ('DDR3', 'DDR3'),
        ('DDR4', 'DDR4'),
        ('DDR5', 'DDR5')
    ], validators=[DataRequired()])

    capacity = IntegerField('Объем (ГБ)', validators=[
        DataRequired(),
        NumberRange(min=1, message='Объем должен быть положительным числом')
    ])
    power_use = IntegerField('Потребляемая мощность (Вт)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Потребляемая мощность должна быть положительным числом')
    ])
    submit = SubmitField('Добавить оперативную память')

class HardDriveForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = FloatField('Цена (руб.)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Цена должна быть положительным числом')
    ])
    capacity = IntegerField('Объем (ГБ)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Объем должен быть положительным числом')
    ])
    recording = IntegerField('Скорость записи (МБ/с)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Скорость записи должна быть положительным числом')
    ])
    reading = IntegerField('Скорость чтения (МБ/с)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Скорость чтения должна быть положительным числом')
    ])
    submit = SubmitField('Добавить жесткий диск')

class CaseForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = FloatField('Цена (руб.)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Цена должна быть положительным числом')
    ])
    form = StringField('Поддерживаемые форм-факторы', validators=[DataRequired()])
    submit = SubmitField('Добавить корпус') 