"""_summary_

Returns:
    _type_: _description_
"""
import os
import json
from flask import Flask, jsonify, render_template, request, redirect, session
from werkzeug.utils import secure_filename
from functools import wraps
from database import (
    search,
    modif_data,
    list_langue,
    history,
    get_page_db,
    update_function,
    update_link,
    reference,
    audio,
)
import hashlib

os.chdir(os.path.dirname(__file__))

update_function()

app = Flask(__name__)

app.secret_key = '5bf990faff27d10c2869dce5ce04a5d09ed3b467aa207700187a291c3a1a031b'


def require_password(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        correct_hash = '8a1d2f69e80343b687b6bd93537105c0a5940b7634437804b48497069c8c4c9c'
        if hash_password(password) == correct_hash:
            session['authenticated'] = True
            return redirect('/')
        return render_template('login.html', error='Mot de passe incorrect')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect('/login')

@app.route("/search", methods=["POST"])
@require_password
def fetch_search():  # pylint: disable=missing-function-docstring
    result = json.loads(request.get_data())
    keyword = result["keyword"]
    engine = result["engine"]
    langue_base = result["langueBase"]
    langue_result = result["langueResult"]
    offset = result["offset"]
    try:
        res = search(
            keyword,
            engine,
            langue=langue_result,
            langue_base=langue_base,
            offset=offset,
        )
        return jsonify({"table": res[0], "count": res[1], "verif": "ok"})
    except Exception as error:  # pylint: disable=broad-except
        print(error)
        return jsonify({"verif": "error"})

@app.route("/listLangue", methods=["POST"])
@require_password
def fetch_langue():  # pylint: disable=missing-function-docstring
    result = json.loads(request.get_data())
    res = list_langue(result["livre"])
    return jsonify(res)

@app.route("/edit", methods=["POST"])
@require_password
def edit():  # pylint: disable=missing-function-docstring
    for change in json.loads(request.get_data()):
        modif_data(change[0], change[1], change[2])
    return "ok"

@app.route("/historyRequest", methods=["POST"])
@require_password
def history_request():  # pylint: disable=missing-function-docstring
    result = json.loads(request.get_data())
    langue = result["langue"]
    sens = result["sens"]
    return jsonify(history(langue=langue, sens=sens))

@app.route("/getaudio", methods=["POST"])
@require_password
def get_audio():  # pylint: disable=missing-function-docstring
    result = json.loads(request.get_data())
    langue = result["langue"]
    sens = result["sens"]
    return jsonify(audio(sens, langue))

@app.route("/getreference", methods=["POST"])
@require_password
def get_reference():  # pylint: disable=missing-function-docstring
    result = json.loads(request.get_data())
    livre = result["livre"]
    return jsonify(reference(livre))

@app.route("/getPage", methods=["POST"])
@require_password
def get_page():  # pylint: disable=missing-function-docstring
    result = json.loads(request.get_data())
    livre = result["livre"]
    num_page = result["page"]
    return jsonify(get_page_db(livre, num_page))

@app.route("/")
def root():
    if not session.get('authenticated'):
        return redirect('/login')
    return redirect("/home", code=302)

@app.route("/home")
@require_password
def index():
    return render_template("home.html")

@app.route("/tmp")
def tmp():  # pylint: disable=missing-function-docstring
    return render_template("tmp.html")

@app.route("/historique")
def historique():  # pylint: disable=missing-function-docstring
    return render_template("historique.html")

@app.route("/correction-page")
def correction_page():  # pylint: disable=missing-function-docstring
    return render_template("correction-page.html")

@app.route("/receiveAudio", methods=["POST"])
@require_password
def receive_audio():  # pylint: disable=missing-function-docstring
    file = request.files["file"]
    sens = request.form["sens"]
    langue = request.form["langue"]
    secure_name = secure_filename(file.filename)
    update_link(sens, langue, secure_name)
    file.save(os.path.join("./static/audio/", secure_name))
    return "ok"

app.debug = False

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
