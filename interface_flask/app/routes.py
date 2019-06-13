from app import app
from flask import Flask, flash, redirect, url_for, request, Response, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
import subprocess
import uuid

UPLOAD_FOLDER = '/app/upload'
ALLOWED_EXTENSIONS = set(['wav', 'mid'])

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

@app.route('/gen_upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        print("uploadfile")
        # check if the post request has the file part
        print(request.files)
        print(request.url)
        if 'file' not in request.files:
            print("ouiiii1")
            flash('No file part')
            return redirect(request.url)
        print("ouiiii2")
        file = request.files['file']
        print("ouiiii3")
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return 'coucou'

@app.route('/generation', methods=['POST'])
def generation():
    print(request.is_json)
    content = request.get_json()
    print(content)
    print(content['urlPrimerMidi'])
    print(content['numberOfFileToGenerate'])
    print(content['genre'])

    rnd_string = str(uuid.uuid4())
    filename = rnd_string + '.midi'

    path_to_generated_output = '/tmp/magenta_generated/' + rnd_string
    #url_path_to_generated_output = 'http://localhost:5000/generated/'

    cmd_curl = '/usr/bin/curl ' + content['urlPrimerMidi'] + ' --output /tmp/' + filename
    so_curl = os.popen(cmd_curl).read()
    print(so_curl)

    cmd_generate = \
        '/usr/local/bin/melody_rnn_generate ' \
        '--config=\'attention_rnn\' ' \
        '--bundle_file=/magenta-models/attention_rnn.mag ' \
        '--num_outputs=' + content['numberOfFileToGenerate'] + ' ' \
        '--num_steps=256 ' \
        '--output_dir=' + path_to_generated_output + '/ ' \
        '--primer_midi=/tmp/' + filename

    print(cmd_generate)

    ##Handle magenta error
    try:
        res = subprocess.Popen(cmd_generate, stdout=subprocess.PIPE, shell=True)
    except OSError:
        print("error: popen")
        return "Error on magenta", 409

    res.wait()
    if res.returncode != 0:
        print("magenta:exit status != 0\n")
        return "Error during magenta generation", 409
    ##
    so_generate = res.stdout.read()
    print(so_generate)

    cmd_ls = '/bin/ls ' + path_to_generated_output
    so_ls = os.popen(cmd_ls).read().split('\n')
    generated_files = filter(None, so_ls)
    print(generated_files)

    cmd_file = '/bin/rm /tmp/' + filename
    so_file = os.popen(cmd_file).read()
    print(so_file)

    json_output = {}
    json_output['midiOutput'] = []
    for generated_file in generated_files:
        json_output['midiOutput'].append(url_path_to_generated_output + rnd_string + '/' + generated_file)

    return Response(str(json_output), mimetype='application/json')


@app.route('/generated/<path:filename>')
def downloadFile(filename):
    path = "/tmp/magenta_generated/" + filename
    return send_file(path, as_attachment=True)
