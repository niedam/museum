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


@app.route('/get/<role>')
def get_role(role):
    # User already has had role.
    if request.cookies.get('role') == 'staff' or request.cookies.get('role') == 'visitor':
        return make_response(redirect('/'))
    # Wrong role in GET request.
    if role != 'staff' and role != 'visitor':
        return make_response(redirect('/'));
    # Set user role.
    response = make_response(redirect('/'), 302)
    response.set_cookie('role', role)
    return response


@app.route('/logout')
@role_required
def logout():
    resp = make_response(redirect('./'), 302)
    resp.set_cookie('role', "")
    return resp

@app.route('/table/<entity>', methods=['GET'])
@role_required
def list(entity):
    cur = conn.cursor()
    template = None
    if (entity == 'artists'):
        cur.execute("SELECT * FROM artists")
        records = cur.fetchall()
        template = render_template("artist-table.html", **locals())
    elif (entity == 'exhibits'):
            cur.execute("SELECT * FROM exhibits LEFT JOIN artists a on exhibits.artist = a.id")
            records = cur.fetchall()
            template = render_template("exhibits-table.html", **locals())
    elif (entity == 'galleries'):
        cur.execute("SELECT * FROM galleries")
        records = cur.fetchall()
        template = render_template("galleries-table.html", **locals())
    elif (entity == 'institutions'):
        cur.execute("SELECT * FROM other_institution")
        records = cur.fetchall()
        template = render_template("institutions-table.html", **locals())
    return template


@app.route('/entity/<entity>/<id>', methods=['GET'])
@role_required
def view(entity, id):
    cur = conn.cursor()
    role = request.cookies.get('role')
    template = None
    if (entity == 'exhibits'):
        cur.execute(sql.SQL("SELECT * FROM exhibits WHERE id = %s"), [id])
        data = cur.fetchone()
        cur.execute("SELECT id, surname, name FROM artists")
        artists = cur.fetchall();
        template = render_template("exhibits-entity.html", **locals())
    elif (entity == 'artists'):
        cur.execute(sql.SQL("SELECT * FROM artists WHERE id = %s"), [id])
        data = cur.fetchone()
        cur.execute(sql.SQL("SELECT * FROM exhibits WHERE artist = %s"), [id])
        exhibits = cur.fetchall()
        template = render_template("artist-entity.html", **locals())
    elif entity == 'galleries':
        cur.execute(sql.SQL("SELECT * FROM galleries WHERE id = %s"), [id])
        data = cur.fetchone()
        cur.execute(sql.SQL("SELECT * FROM rooms WHERE gallery = %s"), [id])
        rooms = cur.fetchall()
        template = render_template("galleries-entity.html", **locals())
    elif entity == 'institutions':
        cur.execute(sql.SQL("SELECT * FROM other_institution WHERE id = %s"), [id])
        data = cur.fetchone()
        template = render_template("institutions-entity.html", **locals())
    return template


if __name__ == '__main__':
    app.run()
