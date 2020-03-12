from flask import Blueprint, render_template, request, make_response, redirect, url_for
from psycopg2 import sql
from db import *


'''
    Routes for entities' views.
'''


views = Blueprint('views', __name__, template_folder='templates')


def get_exhibits(cur, id_ent, role):
    if id_ent == "0":
        return make_response(redirect(url_for("table", entity="exhibits")))
    if id_ent != 'new':
        cur.execute(sql.SQL("SELECT * FROM exhibits WHERE id = %s"), [id_ent])
        data = cur.fetchone()
        cur.execute(sql.SQL("SELECT * FROM exhibits_history WHERE exhibit = %s "
                            "AND current_date BETWEEN since_date AND to_date"), [id_ent])
        loc = cur.fetchall()
        storage = True if len(loc) == 0 else False
    else:
        data = ["new", "", "", "", "", ""]
    cur.execute("SELECT id, surname, name FROM artists")
    artists = cur.fetchall()
    no_exhibits, no_exhibited = notification()
    size_no_exhibits, size_no_exhibited = len(no_exhibits), len(no_exhibited)
    return render_template("exhibits-entity.html", **locals())


def post_exhibits(cur, id_ent, request):
    title = check_none(request.form["title"])
    if request.form["artist"] == "0":
        artist = None
    else:
        artist = check_none(request.form["artist"])
    type = request.form["type"]
    if "rentable" in request.form:
        rentable = True
    else:
        rentable = False
    picture_url = check_none(request.form["picture_url"])
    if id_ent != 'new':
        cur.execute(sql.SQL("UPDATE exhibits SET title = %s, artist = %s, type = %s, rentable = %s, picture_url = %s "
                            "WHERE id = %s"), [title, artist, type, rentable, picture_url, id_ent])
    else:
        cur.execute(sql.SQL("INSERT INTO exhibits(title, artist, type, rentable, picture_url) "
                            "VALUES (%s, %s, %s, %s, %s)"), [title, artist, type, rentable, picture_url])
    conn.commit()
    return make_response(redirect(url_for("table", entity="exhibits") + "?succ=0"), 303)


def delete_exhibits(id_ent):
    cur = conn.cursor()
    cur.execute(sql.SQL("DELETE FROM exhibits_history WHERE exhibit = %s"), [id_ent])
    cur.execute(sql.SQL("DELETE FROM exhibits CASCADE WHERE id = %s"), [id_ent])
    conn.commit()
    return make_response(redirect(url_for("table", entity="exhibits") + "?dell=0"))


@views.route('/entity/exhibits/<id_ent>', methods=['GET', 'POST'])
def entity_exhibits(id_ent):
    cur = conn.cursor()
    role = request.cookies.get('role')
    try:
        if request.method == 'GET' and 'del' not in request.args:
            return get_exhibits(cur, id_ent, role)
        elif request.method == 'GET' and 'del' in request.args and role == 'staff':
            return delete_exhibits(id_ent)
        elif role == 'staff':
            return post_exhibits(cur, id_ent, request)
    except psycopg2.Error:
        conn.rollback()
        return make_response(redirect(url_for("entity_exhibits", id_ent=id_ent) + '?wrong=0'), 307)


def get_artist(id_ent, role):
    if id_ent == "0":
        return make_response(redirect(url_for("table", entity="artists")))
    if id_ent != 'new':
        cur = conn.cursor()
        cur.execute(sql.SQL("SELECT * FROM artists WHERE id = %s"), [id_ent])
        data = cur.fetchone()
        cur.execute(sql.SQL("SELECT * FROM exhibits WHERE artist = %s"), [id_ent])
        exhibits = cur.fetchall()
    else:
        data = ["new", "", "", "", ""]
        exhibits = []
    no_exhibits, no_exhibited = notification()
    size_no_exhibits, size_no_exhibited = len(no_exhibits), len(no_exhibited)
    return render_template("artist-entity.html", **locals())


def post_artist(id_ent, request):
    first = check_none(request.form['name'])
    second = check_none(request.form['surname'])
    born = check_none(request.form['born'])
    die = check_none(request.form['die'])
    cur = conn.cursor()
    if id_ent == 'new':
        cur.execute(sql.SQL("INSERT INTO artists(name, surname, born_date, die_date) VALUES (%s, %s, %s, %s)"),
                    [first, second, born, die])
    else:
        cur.execute(sql.SQL("UPDATE artists SET name = %s, surname = %s, born_date = %s, die_date = %s WHERE id = %s"),
                    [first, second, born, die, id_ent])
    conn.commit()
    return make_response(redirect(url_for("table", entity="artists") + '?succ=0'), 303)


def delete_artist(id_ent):
    cur = conn.cursor()
    cur.execute(sql.SQL("DELETE FROM artists WHERE id = %s"), [id_ent])
    conn.commit()
    return make_response(redirect(url_for("table", entity="artists") + "?dell=0"))


@views.route('/entity/artists/<id_ent>', methods=['GET', 'POST'])
def entity_artists(id_ent):
    role = request.cookies.get('role')
    try:
        if request.method == 'GET' and 'del' not in request.args:
            return get_artist(id_ent, role)
        elif request.method == 'GET' and 'del' in request.args and role == 'staff':
            return delete_artist(id_ent)
        elif request.method == 'POST' and role == 'staff':
            return post_artist(id_ent, request)
    except psycopg2.Error:
        conn.rollback()
        return make_response(redirect(url_for("entity_artists", id_ent=id_ent) + '?wrong=0'), 307)


def get_galleries(id_ent, role):
    if id_ent == "0":
        return make_response(redirect(url_for("table", entity="galleries")))
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
    no_exhibits, no_exhibited = notification()
    size_no_exhibits, size_no_exhibited = len(no_exhibits), len(no_exhibited)
    return render_template("galleries-entity.html", **locals())


def post_galleries(id_ent, request):
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
    return make_response(redirect(url_for("table", entity="galleries") + '?succ=0'), 303)


def delete_galleries(id_ent):
    cur = conn.cursor()
    cur.execute(sql.SQL("DELETE FROM exhibits_history WHERE exhibited_in IN (SELECT id FROM rooms WHERE gallery = %s)"),
                [id_ent])
    cur.execute(sql.SQL("DELETE FROM rooms WHERE gallery = %s"), [id_ent])
    cur.execute(sql.SQL("DELETE FROM galleries WHERE id = %s"), [id_ent])
    conn.commit()
    return make_response(redirect(url_for("table", entity="galleries") + "?dell=0"))


@views.route('/entity/galleries/<id_ent>', methods=['SET', 'GET'])
def entity_galleries(id_ent):
    role = request.cookies.get('role')
    try:
        if request.method == 'GET' and 'del' not in request.args:
            return get_galleries(id_ent, role)
        elif request.method == 'GET' and 'del' in request.args and role == 'staff':
            return delete_galleries(id_ent)
        elif request.method == 'POST' and role == 'staff':
            return post_galleries(id_ent, request)
    except psycopg2.Error:
        conn.rollback()
        return make_response(redirect(url_for("entity_galleries", id_ent=id_ent) + '?wrong=0'), 307)


def get_institutions(id_ent, role):
    if id_ent == "0":
        return make_response(redirect(url_for("table", entity="institutions")))
    if id_ent != 'new':
        cur = conn.cursor()
        cur.execute(sql.SQL("SELECT id, institution_name, COALESCE(street, ''), COALESCE(city, ''), "
                            "COALESCE (zip_code, '')  FROM other_institution WHERE id = %s"), [id_ent])
        data = cur.fetchone()
        cur.execute(sql.SQL("SELECT * FROM rooms WHERE gallery = %s"), [id_ent])
        rooms = cur.fetchall()
        cur.execute(sql.SQL("SELECT e.id, e.title, e.artist, ex_h.since_date, ex_h.to_date "
                            "FROM exhibits_history ex_h LEFT JOIN exhibits e ON ex_h.exhibit = e.id "
                            "WHERE rented_to = %s AND current_date BETWEEN since_date AND to_date"), [id_ent])
        exhibits = cur.fetchall()
    else:
        data = ["new", "", "", "", ""]
        rooms = []
    no_exhibits, no_exhibited = notification()
    size_no_exhibits, size_no_exhibited = len(no_exhibits), len(no_exhibited)
    return render_template("institutions-entity.html", **locals())


def post_institutions(id_ent, request):
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
    return make_response(redirect(url_for("table", entity="institutions") + "?succ=0"), 303)


def delete_institutions(id_ent):
    cur = conn.cursor()
    cur.execute(sql.SQL("DELETE FROM exhibits_history WHERE rented_to = %s"), [id_ent])
    cur.execute(sql.SQL("DELETE FROM other_institution WHERE id = %s"), [id_ent])
    conn.commit()
    return make_response(redirect(url_for("table", entity="institutions") + "?dell=0"))


@views.route('/entity/institutions/<id_ent>', methods=['SET', 'GET'])
def entity_institutions(id_ent):
    role = request.cookies.get('role')
    try:
        if request.method == 'GET' and 'del' not in request.args:
            return get_institutions(id_ent, role)
        elif request.method == 'GET' and 'del' in request.args and role == 'staff':
            return delete_institutions(id_ent)
        elif request.method == 'POST' and role == 'staff':
            return post_institutions(id_ent, request)
    except psycopg2.Error:
        conn.rollback()
        return make_response(redirect(url_for("entity_institutions", id_ent=id_ent) + '?wrong=0'), 307)


def get_rooms(id_ent, role, request):
    if id_ent == "0":
        return make_response(redirect(url_for("table", entity="galleries")))
    cur = conn.cursor()
    if id_ent != 'new':
        cur.execute(sql.SQL("SELECT * FROM rooms LEFT JOIN galleries ON rooms.gallery = galleries.id  "
                            "WHERE rooms.id = %s"), [id_ent])
        data = cur.fetchone()
        cur.execute(sql.SQL("SELECT e.id, e.title, e.artist, ex_h.since_date, ex_h.to_date "
                            "FROM exhibits_history ex_h LEFT JOIN exhibits e ON ex_h.exhibit = e.id "
                            "WHERE exhibited_in = %s AND current_date BETWEEN since_date AND to_date"), [id_ent])
        exhibits = cur.fetchall()
    else:
        cur.execute(sql.SQL("SELECT name FROM galleries where id = %s"), [request.args['gal']])
        tmp = cur.fetchone()
        data = ['new', request.args['gal'], str(), str(), tmp[0]]
    no_exhibits, no_exhibited = notification()
    size_no_exhibits, size_no_exhibited = len(no_exhibits), len(no_exhibited)
    return render_template("rooms-entity.html", **locals())


def post_rooms(id_ent, request):
    name = check_none(request.form['name'])
    gall = check_none(request.form['gallery_id'])
    cur = conn.cursor()
    if id_ent == 'new':
        cur.execute(sql.SQL("INSERT INTO rooms (room, gallery) VALUES (%s, %s)"), [name, gall])
    else:
        cur.execute(sql.SQL("UPDATE rooms SET room = %s WHERE id = %s"), [name, id_ent])
    conn.commit()
    return make_response(redirect(url_for("view", entity="galleries", id_ent=gall) + "?succ=0"), 303)


def delete_rooms(id_ent):
    cur = conn.cursor()
    cur.execute(sql.SQL("SELECT gallery FROM rooms WHERE id = %s"), [id_ent])
    gal = cur.fetchone()[0]
    cur.execute(sql.SQL("DELETE FROM exhibits_history WHERE exhibited_in = %s"), [id_ent])
    cur.execute(sql.SQL("DELETE FROM rooms WHERE id = %s"), [id_ent])
    conn.commit()
    return make_response(redirect(url_for("view", entity="galleries", id_ent=gal) + "?dell=0"))


@views.route('/entity/rooms/<id_ent>', methods=['SET', 'GET'])
def entity_rooms(id_ent):
    role = request.cookies.get('role')
    try:
        if request.method == 'GET' and 'del' not in request.args:
            return get_rooms(id_ent, role, request)
        elif request.method == 'GET' and 'del' in request.args and role == 'staff':
            return delete_rooms(id_ent)
        elif request.method == 'POST' and role == 'staff':
            return post_rooms(id_ent, request)
    except psycopg2.Error:
        conn.rollback()
        return make_response(redirect(url_for("entity_rooms", id_ent=id_ent) + '?wrong=0'), 307)


def get_events(id_ent, role):
    if id_ent == "0":
        return make_response(redirect(url_for("table", entity="events")))
    cur = conn.cursor()
    if id_ent != 'new':
        cur.execute(sql.SQL("SELECT * FROM exhibits_history WHERE id = %s"), [id_ent])
        data = cur.fetchone()
        cur.execute(sql.SQL("SELECT exhibits.id, title, name, surname FROM exhibits "
                            "LEFT JOIN artists a on exhibits.artist = a.id WHERE exhibits.id = %s"), [data[1]])
        exhibits = cur.fetchall()
        exhibits_rentable = exhibits
        cur.execute(sql.SQL("SELECT exhibits.id, title, name, surname FROM exhibits "
                            "LEFT JOIN artists a on exhibits.artist = a.id WHERE exhibits.id = %s"), [data[1]])
        cur.execute(sql.SQL("SELECT * FROM other_institution WHERE id = %s"), [data[5]])
        institutions = cur.fetchall()
        cur.execute(sql.SQL("SELECT r.id, r.room, g.name FROM rooms AS r LEFT JOIN galleries g on r.gallery = g.id "
                            "WHERE r.id = %s"), [data[4]])
        rooms = cur.fetchall()
    elif id_ent == 'new' and role == 'staff':
        cur.execute(sql.SQL("SELECT exhibits.id, title, name, surname FROM exhibits "
                            "LEFT JOIN artists a on exhibits.artist = a.id"))
        exhibits = cur.fetchall()
        cur.execute(sql.SQL("SELECT exhibits.id, title, name, surname FROM exhibits "
                            "LEFT JOIN artists a on exhibits.artist = a.id WHERE rentable = TRUE"))
        exhibits_rentable = cur.fetchall()
        cur.execute(sql.SQL("SELECT * FROM other_institution"))
        institutions = cur.fetchall()
        cur.execute(sql.SQL("SELECT r.id, r.room, g.name FROM rooms r LEFT JOIN galleries g on r.gallery = g.id"))
        rooms = cur.fetchall()
        data = ["new", "", "", "", None, None, False]
    no_exhibits, no_exhibited = notification()
    size_no_exhibits, size_no_exhibited = len(no_exhibits), len(no_exhibited)
    return render_template("events-entity.html", **locals())


def post_events(id_ent, request):
    since = check_none(request.form["since"])
    to = check_none(request.form["to"])
    action = request.form["action"]
    exhibited = None
    rented = None
    exhibit = None
    if action == "rent":
        rented = int(request.form["inst_rent"])
        exhibit = int(request.form["exhibit2"])
    elif action == "gallery":
        exhibited = int(request.form["gall_ex"])
        exhibit = int(request.form["exhibit"])
    cur = conn.cursor()
    try:
        if id_ent == 'new':
            cur.execute(sql.SQL("INSERT INTO exhibits_history (exhibit, since_date, to_date, exhibited_in, rented_to) "
                                "VALUES (%s, %s, %s, %s, %s)"), [exhibit, since, to, exhibited, rented])
        else:
            cur.execute(sql.SQL("UPDATE exhibits_history SET since_date = %s, to_date = %s WHERE id = %s"),
                        [since, to, id_ent])
        conn.commit()
    except psycopg2.Error as e:
        if 'collision' not in e.pgerror:
            raise e
        conn.rollback()
        no_exhibits, no_exhibited = notification()
        size_no_exhibits, size_no_exhibited = len(no_exhibits), len(no_exhibited)
        role = 'staff'
        cur.execute(sql.SQL("SELECT exhibits.id, title, name, surname FROM exhibits "
                            "LEFT JOIN artists a on exhibits.artist = a.id"))
        exhibits = cur.fetchall()
        cur.execute(sql.SQL("SELECT exhibits.id, title, name, surname FROM exhibits "
                            "LEFT JOIN artists a on exhibits.artist = a.id WHERE rentable = TRUE"))
        exhibits_rentable = cur.fetchall()
        cur.execute(sql.SQL("SELECT * FROM other_institution"))
        institutions = cur.fetchall()
        cur.execute(sql.SQL("SELECT r.id, r.room, g.name FROM rooms r LEFT JOIN galleries g on r.gallery = g.id"))
        rooms = cur.fetchall()
        data = [id_ent, exhibit, request.form["since"], request.form["to"], exhibited, rented]
        collision_b = True
        return make_response(render_template("events-entity.html", **locals()), 303)
    collision_b = False
    return make_response(redirect(url_for("table", entity="events") + '?succ=0'), 303)


def delete_events(id_ent):
    cur = conn.cursor()
    cur.execute(sql.SQL("DELETE FROM exhibits_history WHERE id = %s"), [id_ent])
    conn.commit()
    return make_response(redirect(url_for("table", entity="events") + "?dell=0"))


@views.route('/entity/events/<id_ent>', methods=['SET', 'GET'])
def entity_events(id_ent):
    role = request.cookies.get('role')
    try:
        if request.method == 'GET' and 'del' not in request.args:
            return get_events(id_ent, role)
        elif request.method == 'GET' and 'del' in request.args and role == 'staff':
            return delete_events(id_ent)
        elif request.method == 'POST' and role == 'staff':
            return post_events(id_ent, request)
    except psycopg2.Error:
        conn.rollback()
        return make_response(redirect(url_for("entity_events", id_ent=id_ent) + '?wrong=0'), 307)
