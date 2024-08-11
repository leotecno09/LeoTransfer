from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, send_file, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import secrets
import string
import json
import io
import threading
import time

app = Flask(__name__)
#socketio = SocketIO(app)

UPLOAD_FOLDER = "./static/uploads"
TEMP_FOLDER = "./static/uploads/temp"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["TEMP_FOLDER"] = TEMP_FOLDER
app.secret_key = "F3487@83jd!9fdhLfo4$&DSN"

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['TEMP_FOLDER']):
    os.makedirs(app.config['TEMP_FOLDER'])

#connected_users = []

def generate_file_id(length=32):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(secrets.choice(characters) for _ in range(length))
    return random_string

# Thread per cancellare i file salvati nella cartella temporane durante il caricamento
class delete_temp_file(threading.Thread):
    def __init__(self, filepath, delay):
        super().__init__()
        self.filepath = filepath
        self.delay = delay

    def run(self):
        time.sleep(self.delay)
        if os.path.exists(self.filepath):
            os.remove(self.filepath)
            print(f"[NETTURBINO] File {self.filepath} deleted.")

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

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]

        if file.filename == "":
            return jsonify({"status": "error", "error_text": "No files selected"})

        filename = secure_filename(file.filename)
        file_id = generate_file_id()

        print(file_id)

        # Salva il file nella directory temporanea e poi cancellalo dopo 5 minuti
        temp_filepath = os.path.join(app.config["TEMP_FOLDER"], filename)
        file.save(temp_filepath)
        del_thread = delete_temp_file(temp_filepath, 300) # 300 secondi (5 min)
        del_thread.start()
        print(f"Netturbino started for {filename}")

        session["file_id"] = file_id
        session["filename"] = filename
        #session["file_data"] = file.read()

        return jsonify({"status": "success"})

    return render_template("index.html")

@app.route('/new-share-link', methods=["GET", "POST"])
def new_share_link():
    file_id = session.get("file_id")
    filename = session.get("filename")
    #file_data = session.get("file_data")
    temp_filepath = TEMP_FOLDER + "/" + filename
    print(temp_filepath)

    if not file_id or not filename:
        return redirect(url_for("index"))

    if request.method == "POST":
        try:
            #file_id = request.form.get("file_id")
            #filename = request.form.get("filename")
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

            try:
                json_filename = os.path.join(UPLOAD_FOLDER, f"{file_id}.json")

                # Salva il file nella cartella definitiva solo se il file non è scaduto
                final_filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                os.rename(temp_filepath, final_filepath)

                with open(json_filename, "w") as json_file:
                    json.dump(file_info, json_file, indent=4)        

                # Togli i dati del file dalla sessione
                session.pop("file_id", None)
                session.pop("filename", None)

                return jsonify({"status": "success", "share_link": share_link})
            except FileNotFoundError:
                return jsonify({"status": "error", "error_text": "File not found. It's probably expired..."})
        
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