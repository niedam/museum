from flask import Blueprint, render_template, request, make_response, redirect, url_for
from psycopg2 import sql
from db import *

tables = Blueprint('tables', __name__, template_folder='templates')

'''
    Routes for all tables.
'''


@tables.route('/table/artists')
def table_artists():
    role = request.cookies.get('role')
    cur = conn.cursor()
    try:
        no_exhibits, no_exhibited = notification()
        size_no_exhibits, size_no_exhibited = len(no_exhibits), len(no_exhibited)
        cur.execute("SELECT id, name, surname, born_date, die_date FROM artists")
        records = cur.fetchall()
        return render_template("artist-table.html", **locals())
    except psycopg2.Error:
        conn.rollback()
        return make_response(redirect(url_for("table_artists")), 307)


@tables.route('/table/exhibits')
def table_exhibits():
    role = request.cookies.get('role')
    cur = conn.cursor()
    try:
        no_exhibits, no_exhibited = notification()
        size_no_exhibits, size_no_exhibited = len(no_exhibits), len(no_exhibited)
        cur.execute("SELECT e.id, title, artist, type, rentable, picture_url, a.id, COALESCE(a.name, ''), "
                "COALESCE(a.surname, '') FROM exhibits e LEFT JOIN artists a on e.artist = a.id")
        records = cur.fetchall()
        return render_template("exhibits-table.html", **locals())
    except psycopg2.Error:
        conn.rollback()
        return make_response(redirect(url_for("table_exhibits")), 307)


@tables.route('/table/storage')
def table_storage():
    role = request.cookies.get('role')
    cur = conn.cursor()
    try:
        no_exhibits, no_exhibited = notification()
        size_no_exhibits, size_no_exhibited = len(no_exhibits), len(no_exhibited)
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
                            + (" WHERE id_a IN %s" if artists != tuple() else "")),
                    ([since, to, artists] if artists != tuple() else [since, to]))
        records = cur.fetchall()
        return render_template("storage-table.html", **locals())
    except psycopg2.Error:
        conn.rollback()
        return make_response(redirect(url_for("table_storage")), 307)


@tables.route('/table/galleries')
def table_galleries():
    role = request.cookies.get('role')
    cur = conn.cursor()
    try:
        no_exhibits, no_exhibited = notification()
        size_no_exhibits, size_no_exhibited = len(no_exhibits), len(no_exhibited)
        cur.execute(
            "SELECT id, name, coalesce(street, ''), coalesce(city, ''), coalesce(zip_code, '') FROM galleries")
        records = cur.fetchall()
        return render_template("galleries-table.html", **locals())
    except psycopg2.Error:
        conn.rollback()
        return make_response(redirect(url_for("table_galleries")), 307)


@tables.route('/table/institutions')
def table_institutions():
    role = request.cookies.get('role')
    cur = conn.cursor()
    try:
        no_exhibits, no_exhibited = notification()
        size_no_exhibits, size_no_exhibited = len(no_exhibits), len(no_exhibited)
        cur.execute("SELECT id, institution_name, coalesce(street, ''), coalesce(city, ''), "
                    "coalesce(zip_code, '') FROM other_institution")
        records = cur.fetchall()
        return render_template("institutions-table.html", **locals())
    except psycopg2.Error:
        conn.rollback()
        return make_response(redirect(url_for("table_institutions")), 307)


@tables.route('/table/events')
def table_events():
    role = request.cookies.get('role')
    cur = conn.cursor()
    try:
        no_exhibits, no_exhibited = notification()
        size_no_exhibits, size_no_exhibited = len(no_exhibits), len(no_exhibited)
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
                cur.execute(
                    "SELECT * FROM exhibits_history LEFT JOIN exhibits e on exhibits_history.exhibit = e.id")
            else:
                cur.execute(
                    "SELECT * FROM exhibits_history LEFT JOIN exhibits e on exhibits_history.exhibit = e.id "
                    "WHERE current_date BETWEEN since_date AND to_date")
        else:
            query = "SELECT * FROM exhibits_history LEFT JOIN exhibits e on exhibits_history.exhibit = e.id WHERE TRUE "
            if 'since' in request.args:
                since = check_none(request.args['since'])
                if since is not None:
                    query += "AND since_date >= date '" + str(since) + "' "
            if 'to' in request.args:
                to = check_none(request.args['to'])
                if to is not None:
                    query += "AND to_date <= date '" + str(to) + "' "
            if 'g' in request.args:
                gallery = check_none(request.args.getlist('g'))
                if gallery is not None:
                    gallery = [int(i) for i in gallery]
                    q_gallery = "exhibited_in IN (" + str(gallery)[1:-1] + ") "
                else:
                    q_gallery = "FALSE"
            else:
                q_gallery = "FALSE"
            if 'r' in request.args:
                rent = check_none(request.args.getlist('r'))
                if rent is not None:
                    rent = [int(i) for i in rent]
                    q_rent = "rented_to IN (" + str(rent)[1:-1] + ")"
                else:
                    q_rent = "FALSE"
            else:
                q_rent = "FALSE"
            if 'a' in request.args:
                artists = check_none(request.args.getlist('a'))
                if artists is not None:
                    artists = [int(i) for i in artists]
                    query += "AND artist IN (" + str(artists)[1:-1] + ") "
            if q_gallery != "FALSE" or q_rent != "FALSE":
                query += "AND (" + q_rent + " OR " + q_gallery + ") "
            if role != 'staff':
                query += "AND current_date BETWEEN since_date AND to_date"
            cur.execute(query)
        records = cur.fetchall()
        return render_template("events-table.html", **locals())
    except psycopg2.Error:
        conn.rollback()
        return make_response(redirect(url_for("table_institutions")), 307)
