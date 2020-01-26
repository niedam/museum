import psycopg2
from psycopg2 import sql
from dbinfo import *
from flask import Flask, request, make_response, render_template, redirect, url_for

app = Flask(__name__)

try:
    conn = psycopg2.connect(host = host, user = user, password = password, dbname = dbname)
    conn.set_client_encoding('UTF8')
except:
    exit(-1)


def check_none(atr):
    if atr == '':
        return None
    return atr


def notification():
    cur = conn.cursor()
    cur.execute("SELECT * FROM no_exhibits")
    no_exhibits = cur.fetchall()
    cur.execute("SELECT * FROM no_exhibited")
    no_exhibited = cur.fetchall()
    return (no_exhibits, no_exhibited)


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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.cookies.get('role') == 'staff':
        return make_response(redirect(url_for("main_page")))
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        if request.form['password'] == "12345":
            response = make_response(redirect(url_for("main_page")))
            response.set_cookie('role', 'staff')
            return response
        else:
            return make_response(redirect(url_for("login")))


@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for("main_page")), 302)
    resp.set_cookie('role', "")
    return resp


@app.route('/table/<entity>', methods=['GET'])
def table(entity):
    role = request.cookies.get('role')
    cur = conn.cursor()
    template = None
    try:
        no_exhibits, no_exhibited = notification()
        size_no_exhibits, size_no_exhibited = len(no_exhibits), len(no_exhibited)
        if entity == 'artists':
            cur.execute("SELECT id, name, surname, born_date, die_date FROM artists")
            records = cur.fetchall()
            template = render_template("artist-table.html", **locals())
        elif entity == 'exhibits':
                cur.execute("SELECT e.id, title, artist, type, rentable, picture_url, a.id, COALESCE(a.name, ''), "
                            "COALESCE(a.surname, '') FROM exhibits e LEFT JOIN artists a on e.artist = a.id")
                records = cur.fetchall()
                template = render_template("exhibits-table.html", **locals())
        elif entity == 'storage':
            cur.execute("SELECT id, name, surname FROM artists")
            art = cur.fetchall()
            if 'since' in request.args and role == 'staff':
                since = check_none(request.args['since'])
            else:
                since = None
            if 'to' in request.args and role == 'staff':
                to = check_none(request.args['to'])
            else:
                to = None
            if 'a' in request.args:
                artists = tuple(request.args.getlist('a'))
            else:
                artists = tuple()
            cur.execute(sql.SQL("SELECT * FROM storage_query(%s , %s)"
                        + (" WHERE id_a IN %s" if artists != tuple() else "")), ([since, to, artists] if artists != tuple() else [since, to]))
            records = cur.fetchall()
            template = render_template("storage-table.html", **locals())
        elif (entity == 'galleries'):
            cur.execute("SELECT id, name, coalesce(street, ''), coalesce(city, ''), coalesce(zip_code, '') FROM galleries")
            records = cur.fetchall()
            template = render_template("galleries-table.html", **locals())
        elif (entity == 'institutions'):
            cur.execute("SELECT id, institution_name, coalesce(street, ''), coalesce(city, ''), "
                        "coalesce(zip_code, '') FROM other_institution")
            records = cur.fetchall()
            template = render_template("institutions-table.html", **locals())
        elif entity == 'events':
            cur.execute("SELECT id, name, surname FROM artists")
            art = cur.fetchall()
            cur.execute("SELECT id, name FROM galleries")
            gal = cur.fetchall()
            cur.execute("SELECT id, institution_name FROM other_institution")
            otin = cur.fetchall()
            since = ""
            to = ""
            gallery = []
            artists = []
            rent = []
            if len(request.args) == 0:
                if role == 'staff':
                    cur.execute("SELECT * FROM exhibits_history LEFT JOIN exhibits e on exhibits_history.exhibit = e.id")
                else:
                    cur.execute("SELECT * FROM exhibits_history LEFT JOIN exhibits e on exhibits_history.exhibit = e.id "
                                "WHERE current_date BETWEEN since_date AND to_date")
            else:
                query = "SELECT * FROM exhibits_history LEFT JOIN exhibits e on exhibits_history.exhibit = e.id WHERE TRUE "
                if 'since' in request.args:
                    since = check_none(request.args['since'])
                    if since != None:
                        query += "AND since_date >= date '" + str(since) + "' "
                if 'to' in request.args:
                    to = check_none(request.args['to'])
                    if to != None:
                        query += "AND to_date <= date '" + str(to) + "' "
                if 'g' in request.args:
                    gallery = check_none(request.args.getlist('g'))
                    if gallery != None:
                        gallery = [int(i) for i in gallery]
                        q_gallery = "exhibited_in IN (" + str(gallery)[1:-1] + ") "
                    else:
                        q_gallery = "FALSE"
                else:
                    q_gallery = "FALSE"
                if 'r' in request.args:
                    rent = check_none(request.args.getlist('r'))
                    if rent != None:
                        rent = [int(i) for i in rent]
                        q_rent = "rented_to IN (" + str(rent)[1:-1] + ")"
                    else:
                        q_rent = "FALSE"
                else:
                    q_rent = "FALSE"
                if 'a' in request.args:
                    artists = check_none(request.args.getlist('a'))
                    if artists != None:
                        artists = [int(i) for i in artists]
                        query += "AND artist IN (" + str(artists)[1:-1] + ") "
                if q_gallery != "FALSE" or q_rent != "FALSE":
                    query += "AND (" + q_rent + " OR " + q_gallery + ") "
                if role != 'staff':
                    query += "AND current_date BETWEEN since_date AND to_date"
                cur.execute(query)
            records = cur.fetchall()
            template = render_template("events-table.html", **locals())
    except Exception as e:
        conn.rollback()
        return make_response(redirect(url_for("table", entity=entity)))
    return template


def getExhibits(cur, id_ent, role):
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


def postExhibits(cur, id, request):
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
    if id != 'new':
        cur.execute(sql.SQL("UPDATE exhibits SET title = %s, artist = %s, type = %s, rentable = %s, picture_url = %s"
                            "WHERE id = %s"), [title, artist, type, rentable, picture_url, id])
    else:
        cur.execute(sql.SQL("INSERT INTO exhibits(title, artist, type, rentable, picture_url) " 
                            "VALUES (%s, %s, %s, %s, %s)"), [title, artist, type, rentable, picture_url])
    conn.commit()
    return make_response(redirect(url_for("view", entity="exhibits", id_ent=id)), 303)


def deleteExhibits(id_ent):
    cur = conn.cursor()
    cur.execute(sql.SQL("DELETE FROM exhibits_history WHERE exhibit = %s"), [id_ent])
    cur.execute(sql.SQL("DELETE FROM exhibits CASCADE WHERE id = %s"), [id_ent])
    conn.commit()
    return make_response(redirect(url_for("table", entity="exhibits")))


def getArtist(id_ent, role):
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


def postArtist(id_ent, request):
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
    return make_response(redirect(url_for("table", entity="artists")), 303)


def deleteArtist(id_ent):
    cur = conn.cursor()
    cur.execute(sql.SQL("DELETE FROM artists WHERE id = %s"), [id_ent])
    conn.commit()
    return make_response(redirect(url_for("table", entity="artists")))


def getGalleries(id_ent, role):
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
    return make_response(redirect(url_for("view", entity="galleries", id_ent = id_ent)), 303)


def deleteGalleries(id_ent):
    cur = conn.cursor()
    cur.execute(sql.SQL("DELETE FROM exhibits_history WHERE exhibited_in IN (SELECT id FROM rooms WHERE gallery = %s)"),
                [id_ent])
    cur.execute(sql.SQL("DELETE FROM rooms WHERE gallery = %s"), [id_ent])
    cur.execute(sql.SQL("DELETE FROM galleries WHERE id = %s"), [id_ent])
    conn.commit()
    return make_response(redirect(url_for("table", entity="galleries")))


def getInstitutions(id_ent, role):
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
    return make_response(redirect(url_for("view", entity="institutions", id_ent = id_ent)), 303)


def deleteInstitutions(id_ent):
    cur = conn.cursor()
    cur.execute(sql.SQL("DELETE FROM exhibits_history WHERE rented_to = %s"), [id_ent])
    cur.execute(sql.SQL("DELETE FROM other_institution WHERE id = %s"), [id_ent])
    conn.commit()
    return make_response(redirect(url_for("table", entity="institutions")))


def getRooms(id_ent, role, request):
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


def postRooms(id_ent, request):
    name = check_none(request.form['name'])
    gall = check_none(request.form['gallery_id'])
    cur = conn.cursor()
    if id_ent == 'new':
        cur.execute(sql.SQL("INSERT INTO rooms (room, gallery) VALUES (%s, %s)"), [name, gall])
    else:
        cur.execute(sql.SQL("UPDATE rooms SET room = %s WHERE id = %s"), [name, id_ent])
    conn.commit()
    return make_response(redirect(url_for("view", entity="galleries", id_ent = gall)), 303)


def deleteRooms(id_ent):
    cur = conn.cursor()
    cur.execute(sql.SQL("SELECT gallery FROM rooms WHERE id = %s"), [id_ent])
    gal = cur.fetchone()[0]
    cur.execute(sql.SQL("DELETE FROM exhibits_history WHERE exhibited_in = %s"), [id_ent])
    cur.execute(sql.SQL("DELETE FROM rooms WHERE id = %s"), [id_ent])
    conn.commit()
    return make_response(url_for("view", entity="galleries", id_ent = gal))


def getEvents(id_ent, role):
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


def postEvents(id_ent, request):
    since = check_none(request.form["since"])
    to = check_none(request.form["to"])
    cur = conn.cursor()
    try:
        if id_ent == 'new':
            action = request.form["action"]
            exhibited = None
            rented = None
            if action == "rent":
                rented = int(request.form["inst_rent"])
                exhibit = int(request.form["exhibit2"])
            elif action == "gallery":
                exhibited = int(request.form["gall_ex"])
                exhibit = int(request.form["exhibit"])
            cur.execute(sql.SQL("INSERT INTO exhibits_history (exhibit, since_date, to_date, exhibited_in, rented_to) "
                                "VALUES (%s, %s, %s, %s, %s)"), [exhibit, since, to, exhibited, rented])
        else:
            cur.execute(sql.SQL("UPDATE exhibits_history SET since_date = %s, to_date = %s WHERE id = %s"), [since, to, id_ent])
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
    return make_response(redirect(url_for("table", entity="events")), 303)


def deleteEvents(id_ent):
    cur = conn.cursor()
    cur.execute(sql.SQL("DELETE FROM exhibits_history WHERE id = %s"), [id_ent])
    conn.commit()
    return make_response(redirect(url_for("table", entity="events")))


@app.route('/entity/<entity>/<id_ent>', methods=['GET', 'POST'])
def view(entity, id_ent):
    cur = conn.cursor()
    role = request.cookies.get('role')
    template = None
    try:
        if entity == 'exhibits':
            if request.method == 'GET' and not 'del' in request.args:
                return getExhibits(cur, id_ent, role)
            elif request.method == 'GET' and 'del' in request.args and role == 'staff':
                return deleteExhibits(id_ent)
            elif role == 'staff':
                return postExhibits(cur, id_ent, request)
        elif entity == 'artists':
            if request.method == 'GET' and (not 'del' in request.args):
                return getArtist(id_ent, role)
            elif request.method == 'GET' and 'del' in request.args and role == 'staff':
                return deleteArtist(id_ent)
            elif request.method == 'POST' and role == 'staff':
                return postArtist(id_ent, request)
        elif entity == 'galleries':
            if request.method == 'GET' and 'del' not in request.args:
                return getGalleries(id_ent, role)
            elif request.method == 'GET' and 'del' in request.args and role == 'staff':
                return deleteGalleries(id_ent)
            elif request.method == 'POST' and role == 'staff':
                return postGalleries(id_ent, request)
        elif entity == 'institutions':
            if request.method == 'GET' and 'del' not in request.args:
                return getInstitutions(id_ent, role)
            elif request.method == 'GET' and 'del' in request.args and role == 'staff':
                return deleteInstitutions(id_ent)
            elif request.method == 'POST' and role == 'staff':
                return postInstitutions(id_ent, request)
        elif entity == 'rooms':
            if request.method == 'GET' and 'del' not in request.args:
                return getRooms(id_ent, role, request)
            elif request.method == 'GET' and 'del' in request.args and role == 'staff':
                return deleteRooms(id_ent)
            elif request.method == 'POST' and role == 'staff':
                return postRooms(id_ent, request)
        elif entity == 'events':
            if request.method == 'GET' and (not 'del' in request.args):
                return getEvents(id_ent, role)
            elif request.method == 'GET' and 'del' in request.args and role == 'staff':
                return deleteEvents(id_ent)
            elif request.method == 'POST' and role == 'staff':
                return postEvents(id_ent, request)
        else:
            return "tfu"
    except psycopg2.Error:
        conn.rollback()
        return make_response(redirect(request.path + '?info=wrong'), 302)
    return template


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
