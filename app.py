import os
import urllib.parse
from flask import Flask, render_template, request, send_file
from flask_socketio import SocketIO, emit
import yt_dlp

app = Flask(__name__)
socketio = SocketIO(app)

def download_video(url, format, sid):
    # Define the download options
    ydl_opts = {
        'format': format,
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'progress_hooks': [lambda d: download_progress(d, sid)],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if format == 'bestaudio' else {}
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extract info and download the file
        info_dict = ydl.extract_info(url, download=True)
        # Get the downloaded file path (this might be the video file)
        video_filename = ydl.prepare_filename(info_dict)
        # Get the audio filename (post-processed file)
        audio_filename = ydl.prepare_filename(info_dict).replace('.webm', '.mp3')
    
    # Return the path of the audio file if it's available
    if os.path.exists(audio_filename):
        return os.path.abspath(audio_filename)
    return os.path.abspath(video_filename)

def download_progress(d, sid):
    if d['status'] == 'downloading':
        progress = d['_percent_str']
        socketio.emit('progress', {'progress': progress}, to=sid)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    format = request.form['format']
    sid = request.form['sid']
    try:
        # Download the video and get the absolute path of the file
        file_path = download_video(url, format, sid)
        # Send the file for download
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    socketio.run(app, debug=True)
