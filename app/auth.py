from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user, login_required

def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('У вас нет прав администратора для доступа к этой странице', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# Экспортируем login_required из flask_login для удобства
__all__ = ['login_required', 'admin_required'] 