from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
import os
import secrets
import string

app = Flask(__name__)
#socketio = SocketIO(app)

UPLOAD_FOLDER = "./static/uploads"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#connected_users = []

def generate_file_id(length=32):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(secrets.choice(characters) for _ in range(length))
    return random_string

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
        file_id = request.form.get("file_id")
        filename = request.form.get("filename")
        sharer = request.form.get("sharer")
        expires_in = request.form.get("expires_in")
        how_many_downloads = request.form.get("download_times")
        can_raw_checkbox = request.form.get("can_raw")

        can_raw = can_raw_checkbox is not None

        share_link = "https://127.0.0.1:5000/view/" + file_id 

        return jsonify({"status": "success", "share_link": share_link})
    
    return render_template("create_share_link.html")
    

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)