"""
download.py

This module provides functionality for downloading and preprocessing audio files.

Modules:
- yt_dlp: A Python library for downloading YouTube videos.
- os: For handling OS functionality like handling file paths.
- time: For working with time intervals and other time-related functions.
- re: For regular expression operations such as string searching and manipulation.
- shutil: For handling file operations like copying, moving, and deleting files.
- subprocess: For executing external commands and capturing their output.
- tempfile: For creating temporary files and directories.
- logging: Generic logger to handle logging messages.

Classes:
- MyLogger: Custom logger class to handle logging messages.

Functions:
- move_to_new_path(): Moves the input file to a new directory and returns the new file path.
- preprocess_audio(): Preprocesses the input audio file using 'ffmpeg' and saves it in ogg format.
- my_hook():  A custom hook function for youtube_dl to handle download progress.
- get_ydl_opts(): Generates and returns a dictionary of options for youtube_dl.
- handle_large_file(): Handles the processing of large audio files by preparing and preprocessing them.
- download_video_audio(): Downloads and preprocesses the audio from a YouTube video into an MP3 file.
- delete_download(): Deletes the specified file or directory.
- validity_checker(): Checks if the input link is a valid YouTube link and returns a boolean.
- validate_audio_file(): Validate the uploaded audio file for security and format.

Constants:
- logger: Instance of logging to log messages.
- MAX_FILE_SIZE: Maximum allowed file size for audio files (25 MB).
- FILE_TOO_LARGE_MESSAGE: Message displayed when the file size exceeds the maximum allowed size.
- max_retries: Maximum number of tries to retrieve content from YouTube.
- delay: Time delay between retries in seconds.
"""

from __future__ import unicode_literals
import yt_dlp as youtube_dl
import os
import time
import re
import shutil
import subprocess
import tempfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 25 MB
FILE_TOO_LARGE_MESSAGE = "The audio file is too large for the current size and rate limits using Whisper. If you used a YouTube link, please try a shorter video clip. If you uploaded an audio file, try trimming or compressing the audio to under 25 MB."
max_retries = 3
delay = 2


class MyLogger(object):
    """
    A custom logger to handle logging messages with different severities.
    
    Attributes:
        external_logger (function): A function to handle logging messages. Defaults to a no-op lambda function.

    Methods:
        debug(msg): Logs a debug message.
        warning(msg): Logs a warning message.
        error(msg): Logs an error message.
    """

    def __init__(self, external_logger=lambda x: None):
        self.external_logger = external_logger

    def debug(self, msg):
        print("[debug]: ", msg)
        self.external_logger(msg)

    def warning(self, msg):
        print("[warning]: ", msg)

    def error(self, msg):
        print("[error]: ", msg)


def create_secure_temp_dir():
    """Create secure temporary directory."""
    temp_dir = tempfile.mkdtemp(prefix="groq_", suffix="_audio")
    os.chmod(temp_dir, 0o700)  # Secure permissions
    return temp_dir


def move_to_new_path(input_file):
    """
    Moves the input file to a new directory and returns the new file path.

    This function moves the specified input file to the './downloads/audio' directory.
    It ensures that the new directory exists before moving the file. The new file path is returned.

    Args:
        input_file (str): The path to the input file that needs to be moved.

    Returns:
        str: The new file path after moving the file.
    """
    # Define the new directory and file name
    new_directory = create_secure_temp_dir()
    print(f"This is the basename: {os.path.basename(input_file)}")
    new_file_path = os.path.join(new_directory, os.path.basename(input_file))

    # Ensure the new directory exists
    os.makedirs(new_directory, exist_ok=True)

    # Move the temporary file to the new directory
    shutil.move(input_file, new_file_path)
    return new_file_path


def preprocess_audio(input_file):
    """
    Preprocesses the input audio file using 'ffmpeg' and saves it in ogg format.

    This function converts the input audio file to a mono-channel Opus file with specific encoding settings suitable for voice applications.
    It uses a temporary file to store the output and moves it to a new directory. If the 'ffmpeg' process encounters an error, it logs the error message and returns None.

    Args:
        input_file (str): The path to the input audio file that needs to be preprocessed.

    Returns:
        str: The path to the preprocessed audio file in ogg format.
    """

    with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
        output_file = move_to_new_path(temp_file.name)

    ffmpeg_command = [
        'ffmpeg', '-i', input_file, '-vn', '-map_metadata', '-1', '-ac', '1',
        '-c:a', 'libopus', '-b:a', '12k', '-application', 'voip', '-y',
        output_file
    ]

    try:
        process = subprocess.Popen(ffmpeg_command,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)

        for output in process.stderr:
            print(output.strip())

        process.wait()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode,
                                                ffmpeg_command)

        print("Preprocessing complete!")
        time.sleep(0.5)  # Give user a moment to see 100%
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error preprocessing audio: {e}")
        return None


def my_hook(d):
    """
    A custom hook function for youtube_dl to handle download progress.

    This function prints the download progress and logs the progress to the console.
    When the status is 'finished', it indicates that the download is complete and the conversion process will begin.
    """
    print("hook", d["status"])
    if d["status"] == "finished":
        print("Done downloading, now converting ...")


def get_ydl_opts(external_logger=lambda x: None):
    """
    Generates and returns a dictionary of options for youtube_dl.

    This function creates a set of options for downloading audio using 'youtube_dl'. It specifies the format,
    post-processing steps, logging, output template, and progress hooks.

    Args:
        external_logger (function): A function to handle logging messages. Defaults to a no-op lambda function.

    Returns:
        dict: A dictionary of options for youtube_dl.
    """
    return {
        "format":
        "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",  # set the preferred bitrate to 192kbps
        }],
        # "logger":
        # MyLogger(external_logger),
        "outtmpl":
        "./downloads/audio/%(title)s.%(ext)s",  # Set the output filename directly
        "progress_hooks": [my_hook],
    }


def handle_large_file(filesize, MAX_FILE_SIZE, ydl, info):
    """
    Handles the processing of large audio files by preparing and preprocessing them.

    This function uses 'yt_dlp' to download the audio file, converts it to an MP3 format, preprocesses it, and returns the preprocessed file path.

    Args:
        filesize (int): The size of the audio file in bytes.
        MAX_FILE_SIZE (int): The maximum allowed file size for audio files (25 MB).
        ydl (yt_dlp.YoutubeDL): An instance of 'yt_dlp.YoutubeDL' class used to prepare the filename.
        info (dict): The metadata of the downloaded audio file.

    Returns:
        str: The path to the preprocessed audio file in ogg format.    
    """
    input_file = ydl.prepare_filename(info)
    input_file_name = os.path.splitext(input_file)[0] + '.mp3'
    filename = preprocess_audio(input_file_name)
    return filename


def download_video_audio(url, external_logger=lambda x: None):
    """
    Downloads and preprocesses the audio from a YouTube video into an MP3 file.

    This function uses 'yt_dlp' to download the audio from a YouTube video URL. It handles large audio files by preparing and preprocessing them. The function also retries the download in case of errors, up to a specifed number of times.

    Args:
        url (str): The URL of the YouTube video.
        external_logger (function): A function to handle logging messages. Defaults to a no-op lambda function.

    Returns:
        tuple: A tuple containing the path to the audio file and the sanitized title of the video.

    Raises:
        Exception: If the download fails after multiple retries.
    """
    retries = 0
    # while retries < max_retries:
    try:
        ydl_opts = get_ydl_opts(external_logger)
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print("Going to download ", url)
            info = ydl.extract_info(url, download=False)
            filesize = info.get("filesize", 0)
            filename = ydl.prepare_filename(info)
            res = ydl.download([url])
            logger.info(f"youtube-dl result :{res}")
            filetitle = info.get('title',
                                 'Video with ID: ' + info.get('id', 'unknown'))
            mp3_filename = os.path.splitext(filename)[0] + '.mp3'
            mp3_filetitle = re.sub(r'[\\/:*?"<>|]', '', filetitle)
            if filesize > MAX_FILE_SIZE:
                mp3_filename = handle_large_file(filesize, MAX_FILE_SIZE, ydl,
                                                 info)
            print('File name - ', mp3_filename)
            return mp3_filename, mp3_filetitle
    except Exception as e:
        retries += 1
        print(
            f"An error occurred during downloading (Attempt {retries}/{max_retries}):",
            str(e),
        )
        if retries >= max_retries:
            raise e
        time.sleep(delay)


def delete_download(path):
    """
    Deletes the specified file or directory.

    This function attempts to delete the file or directory at the given path. It handles various exceptions such as permission errors, file not found errors, and other general exceptions, providing appropriate messages for each case.

    Args:
        path (str): The path to the file or directory to be deleted.
    """
    try:
        if os.path.isfile(path):
            os.remove(path)
            print(f"File {path} has been deleted.")
        elif os.path.isdir(path):
            shutil.rmtree(path)
            print(f"Directory {path} and its contents have been deleted.")
        else:
            print(f"The path {path} is neither a file nor a directory.")
    except PermissionError:
        print(f"Permission denied: Unable to delete {path}.")
    except FileNotFoundError:
        print(f"File or directory not found: {path}")
    except Exception as e:
        print(f"An error occurred while trying to delete {path}: {str(e)}")


def validate_audio_file(file_path):
    """Validate the uploaded audio file for security and format."""
    allowed_extensions = {"mp3", "wav", "m4a", "ogg"}
    file_extension = os.path.splitext(file_path)[1].lower().strip('.')

    if file_extension not in allowed_extensions:
        raise ValueError("Unsupported file format. Allowed formats: mp3, wav, m4a, ogg.")

    # Check for malicious content (placeholder for actual scanning logic)
    if ".." in file_path or file_path.startswith("/"):
        raise ValueError("Invalid file path detected.")

    # Additional content scanning can be added here
    return True


def validity_checker(url):
    """Checks if the input link is a valid YouTube link and returns a boolean."""
    extractors = youtube_dl.extractor.gen_extractors()
    for extractor in extractors:
        if extractor.suitable(url) and extractor.IE_NAME != 'generic':
            return True
    return False
