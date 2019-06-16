from app import app
from flask import Flask, flash, redirect, url_for, request, Response, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
import subprocess
import uuid
import urlparse
import errno

GENERATE_FOLDER = '/app/generated'
ALLOWED_EXTENSIONS = set(['audio/x-wav'])
BASE_URL = 'http://vps662256.ovh.net:5000/'

UPLOADED_WAV_FILE = 'original.wav'
MIDI_FILENAME = 'result.mid'
RAW_FILENAME = MIDI_FILENAME + '.raw'
MP3_FILENAME = MIDI_FILENAME + '.mp3'

app.secret_key = b'{je8^#zPQms[&upq'
app.config['SESSION_TYPE'] = 'filesystem'


def allowed_file(content_type):
    return content_type.lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return '{ "status": "running" }'

@app.route('/upload_generate', methods=['POST'])
def upload_wav_file():
    soundId = str(uuid.uuid4())
    
    path_to_generated_output = os.path.join(GENERATE_FOLDER, soundId)

    handle_upload(request, path_to_generated_output, UPLOADED_WAV_FILE)

    json_output = generation(UPLOADED_WAV_FILE, path_to_generated_output, soundId)
    return Response(str(json_output), mimetype='application/json')

def handle_upload(request, path_to_generated_output, uploaded_file):
    # check if the post request has the file part
    file = request.files['file']
    if file and allowed_file(file.content_type):
        create_path(path_to_generated_output)
        file.save(os.path.join(path_to_generated_output, uploaded_file))

def create_path(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
		

def generation(uploaded_file, path_to_generated_output, soundId):
    cmd_melodia = '/app/audio_to_midi_melodia.py ' + os.path.join(path_to_generated_output, uploaded_file) + ' ' + os.path.join(path_to_generated_output, MIDI_FILENAME) + ' 60'
    so_melodia = os.popen(cmd_melodia).read()
    print(so_melodia)
    print(cmd_melodia)

    midi_to_mp3(MIDI_FILENAME, path_to_generated_output)

    json_output = get_json_generated_files(path_to_generated_output, soundId)

    return json_output

def get_json_generated_files(path_to_generated_output, soundId):
    cmd_ls = '/bin/ls ' + path_to_generated_output
    so_ls = os.popen(cmd_ls).read().split('\n')
    generated_files = filter(None, so_ls)
    print(generated_files)

    json_output = {}
    #json_output['linkOutput'] = []
    #for generated_file in generated_files:
        #json_output['linkOutput'].append(urlparse.urljoin(BASE_URL, os.path.join(path_to_generated_output, generated_file)))
    json_output['soundId'] = soundId
    json_output['originalWavLink'] = urlparse.urljoin(BASE_URL, os.path.join(path_to_generated_output, UPLOADED_WAV_FILE))
    json_output['mp3Link'] = urlparse.urljoin(BASE_URL, os.path.join(path_to_generated_output, MP3_FILENAME))
    json_output['midiLink'] = urlparse.urljoin(BASE_URL, os.path.join(path_to_generated_output, MIDI_FILENAME))
    
    return json_output


def midi_to_mp3(midi_file, path_to_generated_output):
    cmd_convert_raw = 'fluidsynth -i /app/GeneralUser_GS.sf2 ' + os.path.join(path_to_generated_output, midi_file) + ' -F ' + os.path.join(path_to_generated_output, RAW_FILENAME)
    print(cmd_convert_raw)
    so_raw = os.popen(cmd_convert_raw).read()
    print(so_raw)

    cmd_convert_mp3 = 'sox -t raw -r 88200 -e signed -b 16 -c 1 ' + os.path.join(path_to_generated_output, RAW_FILENAME) + ' ' + os.path.join(path_to_generated_output, MP3_FILENAME)
    print(cmd_convert_mp3)
    so_mp3 = os.popen(cmd_convert_mp3).read()
    print(so_mp3)


@app.route('/sound_list')
def sound_list():
    cmd_ls = '/bin/ls ' + GENERATE_FOLDER
    so_ls = os.popen(cmd_ls).read().split('\n')
    generated_folders = filter(None, so_ls)
    print(generated_folders)

    json_output = {}
    json_output['soundLinkLists'] = []
    for generated_file in generated_files:
        sound_json = {}
        sound_json['soundId'] = urlparse.urljoin(BASE_URL, os.path.join(path_to_generated_output, UPLOADED_WAV_FILE))
        sound_json['originalWavLink'] = urlparse.urljoin(BASE_URL, os.path.join(path_to_generated_output, UPLOADED_WAV_FILE))
        sound_json['mp3Link'] = urlparse.urljoin(BASE_URL, os.path.join(path_to_generated_output, MP3_FILENAME))
        sound_json['midiLink'] = urlparse.urljoin(BASE_URL, os.path.join(path_to_generated_output, MIDI_FILENAME))

        json_output['soundLinkLists'].append(sound_json)
    return json_output


@app.route('/app/generated/<path:filename>')
def download_file(filename):
    path = os.path.join(GENERATE_FOLDER, filename)
    return send_file(path, as_attachment=True)
