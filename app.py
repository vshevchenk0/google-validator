import requests
import time
import os
from flask import Flask, render_template, request
from utils import parse


UPLOAD_FOLDER = "./uploads/tmp"
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload/file", methods=["POST"])
def upload_from_file():
    if 'file' not in request.files:
        error = "No file specified"
        return render_template("index.html", error=error)
    else:
        file = request.files['file']
        if file.filename == '':
            error = "No file specified"
            return render_template("index.html", error=error)
        timestamp = int(time.time())
        file_name = os.path.join(app.config['UPLOAD_FOLDER'], str(timestamp))
        file.save(file_name)
        with open(file_name, "r", encoding="utf-8") as f:
            text = f.read()
            if "&" in text:
                text = text.replace("&", "&amp;")
            result, errors = parse(text)
        if os.path.exists(file_name):
            os.remove(file_name)
    return render_template("index.html", data=result, errors=errors)


@app.route("/upload/url", methods=["POST"])
def upload_from_url():
    if request.form['url']:
        r = requests.get(request.form['url'])
        r.encoding = "utf-8"
        result, errors = parse(r.text)
        return render_template("index.html", data=result, errors=errors)
    else:
        error = "No url specified"
    return render_template("index.html", error=error)
