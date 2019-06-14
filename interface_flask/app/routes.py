from app import app
from flask import Flask, flash, redirect, url_for, request, Response, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
import subprocess
import uuid
import urlparse

UPLOAD_FOLDER = '/app/upload'
GENERATE_FOLDER = '/app/generated'
ALLOWED_EXTENSIONS = set(['wav', 'mid'])
BASE_URL = 'http://vps662256.ovh.net:5000'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = b'{je8^#zPQms[&upq'
app.config['SESSION_TYPE'] = 'filesystem'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return '{ "status": "running" }'

@app.route('/upload_generate', methods=['POST'])
def upload_file():
    rnd_string = str(uuid.uuid4())
    
    uploaded_file = 'original.wav'
    path_to_generated_output = os.path.join(GENERATE_FOLDER, rnd_string)

    handle_upload(request, path_to_generated_output, uploaded_file)

    json_output = generation(uploaded_file, path_to_generated_output)
    return Response(str(json_output), mimetype='application/json')

def handle_upload(request, path_to_generated_output, uploaded_file):
    # check if the post request has the file part
    file = request.files['file']
    if file and allowed_file(file.filename):
        create_path(path_to_generated_output)
        file.save(os.path.join(path_to_generated_output, uploaded_file))

def create_path(path):
    if not os.path.exists(path):          
        os.makedirs(path)

def generation(uploaded_file, path_to_generated_output):
    filename = 'result.mid'

    cmd_melodia = '/app/audio_to_midi_melodia.py ' + os.path.join(path_to_generated_output, uploaded_file) + ' ' + os.path.join(path_to_generated_output, filename) + ' 60'
    so_melodia = os.popen(cmd_melodia).read()
    print(so_melodia)
    print(cmd_melodia)

    midi_to_mp3(filename, path_to_generated_output)

    json_output = get_json_generated_files(path_to_generated_output)

    return json_output
    #return Response(str(json_output), mimetype='application/json')

def get_json_generated_files(path_to_generated_output):
    cmd_ls = '/bin/ls ' + path_to_generated_output
    so_ls = os.popen(cmd_ls).read().split('\n')
    generated_files = filter(None, so_ls)
    print(generated_files)

    json_output = {}
    json_output['midiOutput'] = []
    for generated_file in generated_files:
        json_output['midiOutput'].append(urlparse.urljoin(BASE_URL, os.path.join(path_to_generated_output, generated_file)))
    
    return json_output


def midi_to_mp3(midi_file, path_to_generated_output):
    raw_filename = midi_file + '.raw'
    mp3_filename = midi_file + '.mp3'

    cmd_convert_raw = 'fluidsynth -i /app/GeneralUser_GS.sf2 ' + os.path.join(path_to_generated_output, midi_file) + ' -F ' + os.path.join(path_to_generated_output, raw_filename)
    print(cmd_convert_raw)
    so_raw = os.popen(cmd_convert_raw).read()
    print(so_raw)

    cmd_convert_mp3 = 'sox -t raw -r 88200 -e signed -b 16 -c 1 ' + os.path.join(path_to_generated_output, raw_filename) + ' ' + os.path.join(path_to_generated_output, mp3_filename)
    print(cmd_convert_mp3)
    so_mp3 = os.popen(cmd_convert_mp3).read()
    print(so_mp3)

@app.route('/app/generated/<path:filename>')
def download_file(filename):
    path = os.path.join(GENERATE_FOLDER, filename)
    return send_file(path, as_attachment=True)
