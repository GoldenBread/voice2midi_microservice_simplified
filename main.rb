require 'sinatra'
require 'thread/pool'
require 'thread/every'
require 'securerandom'
require 'net/http'
require 'fileutils'

MAX_RESULTS = ENV['MAX_RESULTS'] || 1
MAX_THREADS = ENV['MAX_THREADS'] || 5
RETAIN_FILE_TIME = ENV['RETAIN_TIME'] || 300
CLEANUP_FREQUENCY = ENV['CLEANUP_FREQUENCY'] || 600

class GenerateTask
  def initialize(uuid, request)
    @request = request
    @uuid = uuid
  end

  def perform
    begin
      cmd_voice2midi = '/app/audio_to_midi_melodia.py ' \
        '/tmp/sources/' + @uuid.to_s + '.wav ' \
        'builds/' + @uuid.to_s + '/output.mid ' \
        '60'

      File.write("/tmp/sources/#{@uuid}.wav", Net::HTTP.get(URI.parse(@request['path'])))
      FileUtils.mkdir_p "builds/#{@uuid}"

      system(cmd_voice2midi)

      response = {
          uuid: @uuid,
          id: @request['id'],
          files: Dir["builds/#{@uuid}/*"].map {|path| path.split('/').last }
      }
      uri = URI(@request['complete_callback'])
      send(uri, response)
    rescue => e
      puts e.inspect
    end
  end
  
  def send(uri, data)
    http = Net::HTTP.new(uri.hostname, uri.port)
    http.use_ssl = true if uri.port == 443

    req = Net::HTTP::Post.new(uri, 'Content-Type' => 'application/json')
    req.body = data.to_json

    http.request(req)
  end
end

class CleanupTask
  def perform
    puts "Running cleanup"
    remove_old_files "builds"
    remove_old_files "/tmp/sources"
    remove_empty_folders "builds"
  end

  def remove_old_files(dir)
    files = Dir.glob("#{dir}/**/*").select{ |e| File.file? e }
    files.each do |file|
      last_update = File.mtime(file)
      File.delete(file) if Time.now - last_update > RETAIN_FILE_TIME
    end
  end

  def remove_empty_folders(base)
    directories = Dir["#{base}/*"].select { |e| File.directory? e }
    directories.each do |dir|
      FileUtils.remove_dir(dir) if Dir["#{dir}/*"].size == 0
    end
  end
end

FileUtils.mkdir_p '/tmp/sources'
pool = Thread::Pool.new(MAX_THREADS)
Thread.every(CLEANUP_FREQUENCY) { CleanupTask.new.perform }
set :port, 5000

before do
  begin
    request.body.rewind
    @request_payload = JSON.parse request.body.read
  rescue
  end
end

get '/' do
  '{ "status": "running" }'
end

post '/api/v1/jobs' do
  uuid = SecureRandom.uuid
  task = GenerateTask.new(uuid, @request_payload)
  pool.process { task.perform }
  "{ 'status': 'pending', 'id': '#{@request_payload['id']}', 'uuid': '#{uuid}'}"
end

get '/api/v1/build/:uuid/:file' do
  send_file File.join('builds', params['uuid'], params['file'])
end

