import psycopg2
from psycopg2 import sql
from dbinfo import *
from flask import Flask, request, make_response, render_template, redirect, url_for
from db import *
from tables import tables
from views import views

app = Flask(__name__)
app.register_blueprint(tables)
app.register_blueprint(views)

# Route to main page.
@app.route('/', methods=['GET'])
def main_page():
    role = request.cookies.get('role')
    try:
        no_exhibits, no_exhibited = notification()
        size_no_exhibits, size_no_exhibited = len(no_exhibits), len(no_exhibited)
    except:
        conn.rollback()
        return make_response(redirect(request.path), 302)
    return render_template("dashboard.html", **locals());


# Route for login.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.cookies.get('role') == 'staff':
        return make_response(redirect(url_for("main_page")))
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        if request.form['password'] == password_user:
            response = make_response(redirect(url_for("main_page")))
            response.set_cookie('role', 'staff')
            return response
        else:
            return make_response(redirect(url_for("login")))


# Route for logout.
@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for("main_page")), 302)
    resp.set_cookie('role', "")
    return resp


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
