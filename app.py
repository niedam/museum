from flask import Flask, request, make_response, render_template, redirect
from jinja2 import Template, Environment, FileSystemLoader

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def hello_world():
    if (request.method == 'POST'):
        response = make_response(redirect('/', 303));
        response.set_cookie('role', request.form['role']);
        return response
    if (request.cookies.get('role') == "staff"):
        return "Hello staff <a href='/logout'>logout</a>";
    elif (request.cookies.get('role') == "visitor"):
        return "Hello visitor <a href='/logout'>logout</a>";
    else:
        return render_template("guest.html", **locals())

@app.route('/logout')
def hello_world2():
    resp = make_response(redirect('/'));
    resp.set_cookie('role', "");
    return resp


if __name__ == '__main__':
    app.run()
