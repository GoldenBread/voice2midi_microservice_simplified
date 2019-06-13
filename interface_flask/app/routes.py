from app import app
from flask import Flask, flash, redirect, url_for, request, Response, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
import subprocess
import uuid

UPLOAD_FOLDER = '/app/upload'
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

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/upload_generate', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        uploaded_file = handle_upload(request)
        json_output = generation(upload_file)
        return Response(str(json_output), mimetype='application/json')
    return 'POST Request'

def handle_upload(request):
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename


def generation(uploaded_file):
    rnd_string = str(uuid.uuid4())
    
    filename = 'result.mid'
    path_to_generated_output = '/tmp/magenta_generated/' + rnd_string
    full_path_to_file = os.path.join(path_to_generated_output, filename)

    cmd_melodia = '/app/audio_to_midi_melodia.py ' + uploaded_file + ' ' + full_path_to_file + ' 60'
    so_melodia = os.popen(cmd_melodia).read()
    print(so_melodia)

    deleteFile(filename)

    midiToMp3(filename, path_to_generated_output)

    json_output = getJsonGeneratedFiles(url_path_to_generated_output, rnd_string)

    return json_output
    #return Response(str(json_output), mimetype='application/json')

def deleteFile(filename):
    cmd_file = '/bin/rm ' + os.path.join(UPLOAD_FOLDER, filename)
    so_file = os.popen(cmd_file).read()
    print(so_file)

def getJsonGeneratedFiles(url_path_to_generated_output, rnd_string):
    cmd_ls = '/bin/ls ' + path_to_generated_output
    so_ls = os.popen(cmd_ls).read().split('\n')
    generated_files = filter(None, so_ls)
    print(generated_files)

    json_output = {}
    json_output['midiOutput'] = []
    for generated_file in generated_files:
        json_output['midiOutput'].append(os.path.join(url_path_to_generated_output, rnd_string, generated_file))
    
    return json_output


def midiToMp3(midi_file, path_to_generated_output):
    raw_filename = midi_file + '.raw'
    mp3_filename = midi_file + '.mp3'

    cmd_convert_raw = 'fluidsynth -i /app/GeneralUser_GS.sf2 ' + os.path.join(path_to_generated_output, midi_file) + ' -F ' + os.path.join(path_to_generated_output, raw_filename)
    so_raw = os.popen(cmd_convert_raw).read()
    print(so_raw)

    cmd_convert_mp3 = 'sox -t raw -r 88200 -e signed -b 16 -c 1 ' + os.path.join(path_to_generated_output, raw_filename) + ' ' + os.path.join(path_to_generated_output, mp3_filename)
    so_mp3 = os.popen(cmd_convert_mp3).read()
    print(so_mp3)

@app.route('/generated/<path:filename>')
def downloadFile(filename):
    path = os.path.join("/tmp/magenta_generated/", filename)
    return send_file(path, as_attachment=True)
