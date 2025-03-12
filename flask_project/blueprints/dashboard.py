# blueprints/dashboard.py
from flask import Blueprint, render_template, redirect, url_for, session

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/front_for_pro', methods=['GET'])
def front_for_pro():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('front_for_pro.html')

@dashboard_bp.route('/admin', methods=['GET'])
def admin():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('admin.html')
