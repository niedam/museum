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
    exit(-1)


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
    return render_template("dashboard.html");


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


def getExhibits(cur, id, role):
    if id != 'new':
        cur.execute(sql.SQL("SELECT * FROM exhibits WHERE id = %s"), [id])
        data = cur.fetchone()
    else:
        data = ["new", "", "", "", "", ""]
    cur.execute("SELECT id, surname, name FROM artists")
    artists = cur.fetchall()
    return render_template("exhibits-entity.html", **locals())


def postExhibits(cur, id, request):
    title = request.form["title"]
    if request.form["artist"] == "0":
        artist = None
    else:
        artist = request.form["artist"]
    type = request.form["type"]
    if "rentable" in request.form:
        rentable = True
    else:
        rentable = False
    picture_url = request.form["picture_url"]
    if id != 'new':
        cur.execute(sql.SQL("UPDATE exhibits SET title = %s, artist = %s, type = %s, rentable = %s, picture_url = %s"
                            "WHERE id = %s"), [title, artist, type, rentable, picture_url, id])
    else:
        cur.execute(sql.SQL("INSERT INTO exhibits(title, artist, type, rentable, picture_url) " 
                            "VALUES (%s, %s, %s, %s, %s)"), [title, artist, type, rentable, picture_url])
    conn.commit()
    return make_response(redirect("/entity/exhibits/" + id), 303)

def getArtist(id_ent, role):
    cur = conn.cursor()
    cur.execute(sql.SQL("SELECT * FROM artists WHERE id = %s"), [id_ent])
    data = cur.fetchone()
    cur.execute(sql.SQL("SELECT * FROM exhibits WHERE artist = %s"), [id_ent])
    exhibits = cur.fetchall()
    return render_template("artist-entity.html", **locals())


def postArtist(id_ent, request):
    first = request.form['name']
    second = request.form['surname']
    born = request.form['born']
    die_tmp = request.form['die']
    if die_tmp == '' or die_tmp == None or die_tmp == 'None':
        die = None
    else:
        die = die_tmp
    cur = conn.cursor()
    cur.execute(sql.SQL("UPDATE artists SET name = %s, surname = %s, born_date = %s, die_date = %s WHERE id = %s"),
                [first, second, born, die, id_ent])
    conn.commit()
    return make_response(redirect("/entity/artists/" + str(id_ent)), 303)

@app.route('/entity/<entity>/<id_ent>', methods=['GET', 'POST'])
@role_required
def view(entity, id_ent):
    cur = conn.cursor()
    role = request.cookies.get('role')
    template = None
    if (entity == 'exhibits'):
        if request.method == 'GET':
            return getExhibits(cur, id_ent, role)
        elif role == 'staff':
            return postExhibits(cur, id_ent, request)
    elif (entity == 'artists'):
        if request.method == 'GET':
            return getArtist(id_ent, role)
        elif request.method == 'POST' and role == 'staff':
            return postArtist(id_ent, request)
    elif entity == 'galleries':
        cur.execute(sql.SQL("SELECT * FROM galleries WHERE id = %s"), [id_ent])
        data = cur.fetchone()
        cur.execute(sql.SQL("SELECT * FROM rooms WHERE gallery = %s"), [id_ent])
        rooms = cur.fetchall()
        template = render_template("galleries-entity.html", **locals())
    elif entity == 'institutions':
        cur.execute(sql.SQL("SELECT * FROM other_institution WHERE id = %s"), [id_ent])
        data = cur.fetchone()
        template = render_template("institutions-entity.html", **locals())
    return template


if __name__ == '__main__':
    app.run()
