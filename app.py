import psycopg2
from flask import Flask, request, make_response, render_template, redirect

app = Flask(__name__)
try:
    conn = psycopg2.connect("host='labdb' dbname='bd' user='nick' password='haslo'")
except:
    print("Karamba");

@app.route('/', methods=['GET'])
def main_page():
    if (request.cookies.get('role') == "staff"):
        return "Hello staff <a href='/logout'>logout</a>"
    elif (request.cookies.get('role') == "visitor"):
        return "Hello visitor <a href='/logout'>logout</a>"
    else:
        return render_template("guest.html", **locals())


@app.route('/get/<role>', methods=['GET'])
def get_role(role):
    if request.cookies.get('role') == 'staff' or request.cookies.get('role') == 'visitor':
        return make_response(redirect('/'))
    if role != 'staff' and role != 'visitor':
        return make_response(redirect('/'));
    response = make_response(redirect('/'), 302)
    response.set_cookie('role', role)
    return response

@app.route('/logout')
def logout():
    resp = make_response(redirect('/'), 302)
    resp.set_cookie('role', "")
    return resp


if __name__ == '__main__':
    app.run()
