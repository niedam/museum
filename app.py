from functools import wraps

import psycopg2
from psycopg2 import sql

from dbinfo import *
from flask import Flask, request, make_response, render_template, redirect


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


def check_none(atr):
    if atr == '':
        return None
    return atr

@app.route('/', methods=['GET'])
@role_required
def main_page():
    role = request.cookies.get('role')
    return render_template("dashboard.html", **locals());


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
    if id_ent != 'new':
        cur = conn.cursor()
        cur.execute(sql.SQL("SELECT * FROM artists WHERE id = %s"), [id_ent])
        data = cur.fetchone()
        cur.execute(sql.SQL("SELECT * FROM exhibits WHERE artist = %s"), [id_ent])
        exhibits = cur.fetchall()
    else:
        data = ["new", "", "", "", ""]
        exhibits = []
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

def getGalleries(id_ent, role):
    if id_ent != 'new':
        cur = conn.cursor()
        cur.execute(sql.SQL("SELECT id, name, COALESCE(street, ''), COALESCE(city, ''), "
                    "COALESCE (zip_code, '')  FROM galleries WHERE id = %s"), [id_ent])
        data = cur.fetchone()
        cur.execute(sql.SQL("SELECT * FROM rooms WHERE gallery = %s"), [id_ent])
        rooms = cur.fetchall()
    else:
        data = ["new", "", "", "", ""]
        rooms = []
    return render_template("galleries-entity.html", **locals())

def postGalleries(id_ent, request):
    name = check_none(request.form['name'])
    street = check_none(request.form['street'])
    city = check_none(request.form['city'])
    zip = check_none(request.form['zip_code'])
    cur = conn.cursor()
    if id_ent == 'new':
        cur.execute(sql.SQL("INSERT INTO galleries (name, street, city, zip_code)"
                        "VALUES (%s, %s, %s, %s)"), [name, street, city, zip])
    else:
        cur.execute(sql.SQL("UPDATE galleries SET name = %s, street = %s, city = %s, zip_code = %s WHERE id = %s"),
                    [name, street, city, zip, id_ent])
    conn.commit()
    return make_response(redirect("/entity/galleries/" + str(id_ent)), 303)


def getInstitutions(id_ent, role):
    if id_ent != 'new':
        cur = conn.cursor()
        cur.execute(sql.SQL("SELECT id, institution_name, COALESCE(street, ''), COALESCE(city, ''), "
                    "COALESCE (zip_code, '')  FROM other_institution WHERE id = %s"), [id_ent])
        data = cur.fetchone()
        cur.execute(sql.SQL("SELECT * FROM rooms WHERE gallery = %s"), [id_ent])
        rooms = cur.fetchall()
    else:
        data = ["new", "", "", "", ""]
        rooms = []
    return render_template("institutions-entity.html", **locals())


def postInstitutions(id_ent, request):
    name = check_none(request.form['name'])
    street = check_none(request.form['street'])
    city = check_none(request.form['city'])
    zip = check_none(request.form['zip_code'])
    cur = conn.cursor()
    if id_ent == 'new':
        cur.execute(sql.SQL("INSERT INTO other_institution (institution_name, street, city, zip_code)"
                    "VALUES (%s, %s, %s, %s)"), [name, street, city, zip])
    else:
        cur.execute(sql.SQL("UPDATE other_institution SET institution_name = %s, street = %s, city = %s, zip_code = %s "
                            "WHERE id = %s"), [name, street, city, zip, id_ent])
    conn.commit()
    return make_response(redirect("/entity/institutions/" + str(id_ent)), 303)


def getRooms(id_ent, role, request):
    cur = conn.cursor()
    if id_ent != 'new':
        cur.execute(sql.SQL("SELECT * FROM rooms LEFT JOIN galleries ON rooms.gallery = galleries.id  "
                            "WHERE rooms.id = %s"), [id_ent])
        data = cur.fetchone()
    else:
        cur.execute(sql.SQL("SELECT name FROM galleries where id = %s"), [request.args['gal']])
        tmp = cur.fetchone()
        data = ['new', request.args['gal'], str(), str(), tmp[0]]
    return render_template("rooms-entity.html", **locals())

def postRooms(id_ent, request):
    name = check_none(request.form['name'])
    gall = check_none(request.form['gallery_id'])
    cur = conn.cursor()
    if id_ent == 'new':
        cur.execute(sql.SQL("INSERT INTO rooms (room, gallery) VALUES (%s, %s)"), [name, gall])
    else:
        cur.execute(sql.SQL("UPDATE rooms SET room = %s WHERE id = %s"), [name, id_ent])
    conn.commit()
    return make_response(redirect("/entity/galleries/" + str(gall)), 303)




@app.route('/entity/<entity>/<id_ent>', methods=['GET', 'POST'])
@role_required
def view(entity, id_ent):
    cur = conn.cursor()
    role = request.cookies.get('role')
    template = None
    if entity == 'exhibits':
        if request.method == 'GET':
            return getExhibits(cur, id_ent, role)
        elif role == 'staff':
            return postExhibits(cur, id_ent, request)
    elif entity == 'artists':
        if request.method == 'GET':
            return getArtist(id_ent, role)
        elif request.method == 'POST' and role == 'staff':
            return postArtist(id_ent, request)
    elif entity == 'galleries':
        if request.method == 'GET':
            return getGalleries(id_ent, role)
        elif request.method == 'POST' and role == 'staff':
            return postGalleries(id_ent, request)
    elif entity == 'institutions':
        if request.method == 'GET':
            return getInstitutions(id_ent, role)
        elif request.method == 'POST' and role == 'staff':
            return postInstitutions(id_ent, request)
    elif entity == 'rooms':
        if request.method == 'GET':
            return getRooms(id_ent, role, request)
        elif request.method == 'POST' and role == 'staff':
            return postRooms(id_ent, request)
    return template



if __name__ == '__main__':
    app.run()
