from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import secrets
import string
import json

app = Flask(__name__)
#socketio = SocketIO(app)

UPLOAD_FOLDER = "./static/uploads"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#connected_users = []

def generate_file_id(length=32):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(secrets.choice(characters) for _ in range(length))
    return random_string

def ReadJSON(file_code, line):
    json_filename = f"{UPLOAD_FOLDER}/{file_code}.json"

    try:
        with open(json_filename, "r") as json_file:
            data = json.load(json_file)

        if line == "all":
            return data
        
        else:
            return data.get(line, None)
    
    except FileNotFoundError:
        print(f"{json_filename} not found.")
        return None
    
    except json.JSONDecodeError:
        print(f"Error during decode of {json_filename}")
        return None

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/api/upload_file', methods=["POST"])
def handle_file():
    file = request.files["file"]

    if file.filename == "":
        return jsonify({"status": "error", "error_text": "No files selected"})

    filename = secure_filename(file.filename)
    file_id = generate_file_id()

    print(file_id)

    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    return jsonify({"status": "success", "file_id": file_id, "filename": filename})

@app.route('/new-share-link', methods=["GET", "POST"])
def new_share_link():
    if request.method == "POST":
        try:
            file_id = request.form.get("file_id")
            filename = request.form.get("filename")
            sharer = request.form.get("sharer")
            expires_in = request.form.get("expires_in")
            max_downloads = request.form.get("download_times")
            can_raw_checkbox = request.form.get("can_raw")

            can_raw = can_raw_checkbox is not None

            share_link = "https://127.0.0.1:5000/view/" + file_id

            expire_days = int(expires_in)
            expire_date = (datetime.now() + timedelta(days=expire_days)).strftime('%d-%m-%Y')

            file_info = {
                "filename": filename,
                "sharer": sharer,
                "expire_date": expire_date,
                "max_downloads": max_downloads,
                "raw": can_raw
            }

            json_filename = os.path.join(UPLOAD_FOLDER, f"{file_id}.json")

            with open(json_filename, "w") as json_file:
                json.dump(file_info, json_file, indent=4)        

            return jsonify({"status": "success", "share_link": share_link})
        
        except Exception as e:
            return jsonify({"status": "error", "error_text": e})
    
    return render_template("create_share_link.html")
    
@app.route("/view/<file_id>")
def view_file(file_id):
    fileinfo = ReadJSON(file_id, "all")

    if fileinfo:
        filename = fileinfo.get("filename", None)
        sharer = fileinfo.get("sharer", None)
        raw = fileinfo.get("raw", None)

        _, file_extension = os.path.splitext(filename)
        type = file_extension.lstrip(".").upper()

        #print(type)

        return render_template("view_file.html", file_id=file_id, type=type, filename=filename, sharer=sharer, raw=raw)
    
    else:
        return render_template("general_error.html", error="FIle not found", error_code="404")

@app.route("/r/<file_id>")
def view_raw_file(file_id):
    referer = request.headers.get("Referer")
    attachment = request.args.get("a")

    if attachment == "False":
        attachment = False
    else:
        attachment = True

    fileinfo = ReadJSON(file_id, "all")

    if fileinfo:                ### CHECK MAX DOWNLOADSSSSS ###
        filename = fileinfo.get("filename", None)
        raw = fileinfo.get("raw")
        file_path = f"{UPLOAD_FOLDER}/{filename}"

        if raw == False:
            if referer is None or not referer.startswith(request.host_url):
                return render_template("general_error.html", error="This file cannot be viewed as raw.", error_code="403")
            
            else:
                return send_file(file_path, as_attachment=attachment)
        else:
            return send_file(file_path, as_attachment=attachment)

    else:
        return render_template("general_error.html", error="File not found", error_code="404")


if __name__ == '__main__':              ### AUTOMATE FILE DELETE ### 
    app.run(host="0.0.0.0", debug=True)