from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class ConfigurationForm(FlaskForm):
    name = StringField('Название конфигурации', validators=[
        DataRequired(), 
        Length(min=3, max=100, message='Название должно содержать от 3 до 100 символов')
    ])
    
    motherboard_id = SelectField('Материнская плата', coerce=int, validators=[])
    supply_id = SelectField('Блок питания', coerce=int, validators=[])
    cpu_id = SelectField('Процессор', coerce=int, validators=[])
    gpu_id = SelectField('Видеокарта', coerce=int, validators=[])
    cooler_id = SelectField('Кулер', coerce=int, validators=[])
    ram_id = SelectField('Оперативная память', coerce=int, validators=[])
    hdd_id = SelectField('Жёсткий диск', coerce=int, validators=[])
    frame_id = SelectField('Корпус', coerce=int, validators=[])
    
    submit = SubmitField('Сохранить конфигурацию') 