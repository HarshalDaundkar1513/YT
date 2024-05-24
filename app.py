from flask import Flask, render_template, request, redirect, url_for
from pytube import YouTube
from tqdm import tqdm
import os
from pathlib import Path

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get('url')
        return redirect(url_for('resolutions', url=url))
    return render_template('index.html')

@app.route("/resolutions", methods=["GET", "POST"])
def resolutions():
    url = request.args.get('url')
    yt = YouTube(url)
    video_streams = yt.streams.filter(adaptive=True, only_video=True)
    resolutions = []

    for stream in video_streams:
        resolution = stream.resolution
        file_size = stream.filesize / (1024 * 1024)  # Convert to MB
        if resolution not in [res['resolution'] for res in resolutions]:
            resolutions.append({
                "resolution": resolution,
                "file_size": f"{file_size:.2f} MB",
                "itag": stream.itag
            })

    if request.method == "POST":
        itag = request.form.get('itag')
        return redirect(url_for('download', url=url, itag=itag))

    return render_template('resolutions.html', resolutions=resolutions, title=yt.title, url=url)

@app.route("/download", methods=["GET", "POST"])
def download():
    url = request.args.get('url')
    itag = request.args.get('itag')
    yt = YouTube(url)
    video = yt.streams.get_by_itag(itag)
    
    tqdm_bar = tqdm(total=video.filesize, unit='B', unit_scale=True, desc=yt.title)

    def progress_function(stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = bytes_downloaded / total_size * 100
        tqdm_bar.update(len(chunk))

    yt.register_on_progress_callback(progress_function)

    print(f"Downloading {yt.title} in {video.resolution} resolution...")

    # Set download path to the user's Downloads folder
    download_folder = str(Path.home() / "Downloads")  # Convert Path object to string
    video.download(output_path=download_folder)
    
    tqdm_bar.close()
    print("Download completed!")

    return redirect(url_for('download_complete'))

@app.route("/download_complete", methods=["GET"])
def download_complete():
    return render_template('download_complete.html')

if __name__ == "__main__":
    app.run(debug=True)
