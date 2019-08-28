# from flask import Blueprint, render_template
# from flask_jwt_extended import jwt_optional
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
    # return render_template('page/home.html')
    current_user = get_jwt_identity()

    if current_user is None:
        return redirect(url_for('user.login'))

    return redirect(url_for('page.home'))

@page.route('/home')
@jwt_required
def home():
    return render_template('page/home2.html')

