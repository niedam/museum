from flask import Blueprint, request

simple_page = Blueprint('entities', __name__, template_folder='templates')
@simple_page.route('/<page>')
def show(page):
    # stuff