from flask import Blueprint, render_template, redirect, request, url_for
from flask_jwt_extended import (
	jwt_optional,
    jwt_required,
    get_jwt_identity,
    current_user
)

page = Blueprint('page', __name__, template_folder='templates')


@page.route('/')
@jwt_optional
def index():
    current_user = get_jwt_identity()
    if current_user is None:
        return redirect(url_for('user.login'))
    return redirect(url_for('page.home'))

@page.route('/home')
@jwt_optional
def home():
    current_user = get_jwt_identity()
    if current_user is None:
        return redirect(url_for('user.login'))
    return render_template('page/home2.html')


@page.route('/vim')
@jwt_optional
def vim():
    current_user = get_jwt_identity()
    if current_user is None:
        return redirect(url_for('user.login'))
    return render_template('page/vim.html')


@page.route('/wim')
@jwt_optional
def wim():
    current_user = get_jwt_identity()
    if current_user is None:
        return redirect(url_for('user.login'))
    return render_template('page/wim.html')