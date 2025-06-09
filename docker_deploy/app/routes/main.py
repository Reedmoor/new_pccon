from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.forms.auth import UpdateProfileForm, ChangePasswordForm
from app.models.models import User
from werkzeug.security import check_password_hash
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('main/index.html')

@main_bp.route('/about')
def about():
    return render_template('main/about.html')

@main_bp.route('/profile')
@login_required
def profile():
    return render_template('main/profile.html')

@main_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = UpdateProfileForm()
    
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Ваш профиль успешно обновлен!', 'success')
        return redirect(url_for('main.profile'))
    elif request.method == 'GET':
        # Заполняем форму текущими данными
        form.name.data = current_user.name
        form.email.data = current_user.email
    
    return render_template('main/edit_profile.html', form=form)

@main_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Проверяем, совпадает ли текущий пароль
        if not current_user.check_password(form.current_password.data):
            flash('Текущий пароль неверен', 'danger')
            return render_template('main/change_password.html', form=form)
        
        # Устанавливаем новый пароль
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('Ваш пароль успешно изменен!', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('main/change_password.html', form=form) 