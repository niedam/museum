from functools import wraps

import psycopg2
from psycopg2 import sql

from dbinfo import *
from flask import Flask, request, make_response, render_template, redirect, send_from_directory


app = Flask(__name__)

try:
    conn = psycopg2.connect(host = host, user = user, password = password, dbname = dbname)
    conn.set_client_encoding('UTF8')
except:
    exit(-1);



def role_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if request.cookies.get('role') == 'staff' or request.cookies.get('role') == 'visitor':
            return f(*args, **kwargs)
        else:
            return render_template("guest.html", **locals());
    return wrap

@app.route('/', methods=['GET'])
@role_required
def main_page():
    print("aaaa")
    return render_template("dashboard.html");
    if (request.cookies.get('role') == "staff"):
        return "Hello staff <a href='/logout'>logout</a>"
    elif (request.cookies.get('role') == "visitor"):
        return "Hello visitor <a href='/logout'>logout</a>"


@app.route('/get/<role>', methods=['GET'])
def get_role(role):
    # User already has had role.
    if request.cookies.get('role') == 'staff' or request.cookies.get('role') == 'visitor':
        return make_response(redirect('./'))
    # Wrong role in GET request.
    if role != 'staff' and role != 'visitor':
        return make_response(redirect('./'));
    # Set user role.
    response = make_response(redirect('./'), 302)
    response.set_cookie('role', role)
    return response


@app.route('/logout')
@role_required
def logout():
    resp = make_response(redirect('./'), 302)
    resp.set_cookie('role', "")
    return resp

@app.route('/entity/<entity>', methods=['GET'])
@role_required
def list(entity):
    cur = conn.cursor()
    template = None
    if (entity == 'artists'):
        cur.execute("SELECT * FROM artists")
        records = cur.fetchall()
        template = render_template("list_artists.html", **locals())
    elif (entity == 'exhibits'):
            cur.execute("SELECT * FROM exhibits")
            records = cur.fetchall()
            template = render_template("list_exhibits.html", **locals())
    elif (entity == 'galleries'):
        cur.execute("SELECT * FROM galleries")
        records = cur.fetchall()
        template = render_template("list_galleries.html", **locals())
    elif (entity == 'institutions'):
        cur.execute("SELECT * FROM other_institution")
        records = cur.fetchall()
        template = render_template("list_institution.html", **locals())
    return template


@app.route('/entity/<entity>/<id>', methods=['GET'])
@role_required
def view(entity, id):
    cur = conn.cursor()
    template = None
    if (entity == 'exhibits'):
        cur.execute(sql.SQL("SELECT * FROM exhibits WHERE id = %s"), [id])
        data = cur.fetchone()
        template = render_template("view_exhibit.html", **locals())
    return template


if __name__ == '__main__':
    app.run()
