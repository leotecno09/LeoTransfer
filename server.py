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

    return jsonify({"status": "success", "file_id": file_id})

@app.route('/new-share-link/<file_id>')
def new_share_link(file_id):
    return file_id

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)