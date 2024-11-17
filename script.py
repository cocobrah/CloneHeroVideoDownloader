import os
import yt_dlp
import re
import subprocess

def clean_artist_name(artist_name):
    # Use a regular expression to remove anything in parentheses (including the parentheses)
    cleaned_name = re.sub(r'\s?\(.*\)', '', artist_name).strip()
    return cleaned_name

# Function to download video using yt-dlp and convert to webm
def download_video(url, output_dir, artist_name):    
    ydl_opts = {
        'format': 'bestvideo',  # select the best quality
        'outtmpl': os.path.join(output_dir, 'video.%(ext)s'),  # save the video as 'video'
        'noplaylist': True,  # don't download entire playlists, just the single video
        'quiet': True,  # make it verbose for debugging
        'extract_flat': True,  # Only extract video information without downloading the video
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extract the video information
        result = ydl.extract_info(url, download=False)

        # Check if the video is from a channel whose name contains the artist name
        if 'uploader' in result and artist_name.lower() in result['uploader'].lower():
            print(f"Channel matches artist (partial match): {result['uploader']}")
            # Proceed to download the video
            ydl_opts['extract_flat'] = False  # Disable flat extraction and set to download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                ydl_download.download([url])

            # Get the path to the downloaded video (this assumes the extension is .mp4 or other formats)
            downloaded_video_path = os.path.join(output_dir, 'video.mp4')  # Adjust if necessary based on download format
            if os.path.exists(downloaded_video_path):
                # Call function to convert to webm
                convert_to_webm(downloaded_video_path, output_dir)
        else:
            print(f"Video uploader does not contain the artist '{artist_name}' (partial match). No video will be downloaded.")

# Function to convert the downloaded video to webm using ffmpeg
def convert_to_webm(input_video_path, output_dir):
    # Define the path to ffmpeg.exe (ensure ffmpeg.exe is in the same folder as the script)
    ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg.exe')
    
    # Check if ffmpeg.exe exists in the expected directory
    if not os.path.exists(ffmpeg_path):
        print("Error: ffmpeg.exe not found in the same directory as the script.")
        return

    # Define the output webm file path
    output_webm_path = os.path.join(output_dir, 'video.webm')

    # Run ffmpeg to convert the video
    print(f"Converting {input_video_path} to {output_webm_path} using {ffmpeg_path}...")
    command = [
        ffmpeg_path, '-i', input_video_path,  # Input video file
        '-c:v', 'libvpx', '-crf', '10', '-b:v', '1M',  # Video codec settings for webm
        '-an',  # No audio
        output_webm_path  # Output path
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Conversion complete: {output_webm_path}")
        # Optionally, delete the original video file after conversion
        os.remove(input_video_path)
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")

# Function to process each song directory
def process_song_directory(song_dir):
    # Look for the song.ini file
    ini_file = None
    for root, dirs, files in os.walk(song_dir):
        for file in files:
            if file.lower() == 'song.ini':  # Ensure you are looking for "song.ini" only
                ini_file = os.path.join(root, file)
                break
        if ini_file:
            break

    if not ini_file:
        print(f"No song.ini file found in {song_dir}. Skipping...")
        return

    # Read song title and artist from the ini file under [song] section
    song_title = None
    artist_name = None
    with open(ini_file, 'r', encoding='utf-8', errors='ignore') as f:
        in_song_section = False
        for line in f:
            line = line.strip()
            if line.lower() == '[song]':
                in_song_section = True
            elif in_song_section:
                if line.startswith('name'):
                    match = re.match(r"^name\s*=\s*(.*)$", line)
                    if match:
                        song_title = match.group(1)
                elif line.startswith('artist'):
                    match = re.match(r"^artist\s*=\s*(.*)$", line)
                    if match:
                        artist_name = match.group(1)
                        artist_name = clean_artist_name(artist_name)
                if song_title and artist_name:
                    break

    if not song_title or not artist_name:
        print(f"Missing song title or artist in {ini_file}. Skipping...")
        return

    print(f"Downloading video for {song_title} by {artist_name}...")

    # Search YouTube for the song
    query = f"{song_title} {artist_name} music video"
    ydl_opts = {
        'quiet': True,  # suppress output
        'extract_flat': True,  # get only metadata, no actual download
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(f"ytsearch:{query}", download=False)

    if 'entries' not in search_results or len(search_results['entries']) == 0:
        print(f"No results found for {song_title} by {artist_name}.")
        return

    # Get the last video entry (usually the best quality)
    video_url = search_results['entries'][-1]['url']

    # Check if a video already exists in the folder
    output_dir = os.path.dirname(ini_file)
    video_path = os.path.join(output_dir, 'video.webm')
    if os.path.exists(video_path):
        print(f"Video already exists for {song_title}. Skipping download.")
        return

    # Call download_video with two arguments: URL, output directory, and artist name
    try:
        download_video(video_url, output_dir, artist_name)  # Make sure this function gets the artist_name
        print(f"Downloaded video for {song_title} by {artist_name}.")
    except Exception as e:
        print(f"Error downloading video: {e}")

# Main function
def main():
    # Ask for the root directory
    root_dir = input("Enter the path to the root song directory: ")

    # Check if the directory exists
    if not os.path.isdir(root_dir):
        print(f"The directory {root_dir} does not exist.")
        return

    # Walk through each song directory and process it
    for root, dirs, files in os.walk(root_dir):
        for dir_name in dirs:
            song_dir = os.path.join(root, dir_name)
            process_song_directory(song_dir)

if __name__ == "__main__":
    main()
