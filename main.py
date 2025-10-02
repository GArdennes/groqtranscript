"""
main.py

This is the main file of ScribePlus.

Modules:
- streamlit: For creating the web interface.
- groq: For interacting with the Groq API.
- json: For handling JSON data.
- os: For working with operating system commands.
- io: For working with input/output operations.
- dotenv: For loading environment variables from a .env file.
- download: For downloading and deleting audio files.
- notes: For generating notes and transcript structure.
- time: For working with time-related operations.

Functions:
- disable(): Disables certain features in the web interface.
- enable(): Enables certain features in the web interface.
- empty_st(): Empties the Streamlit session state.
- display_status(): Displays the status of the audio process.
- clear_status(): Clears the status of the audio process.
- display_download_status(): Display the audio download progress.
- clear_download_status(): Clears the audio download progress from screen.
- display_statistics(): Handles the model stastistics and the transcription text as per progress.
- stream_section_content(): Streams the section content and updates existing file. 
- check_dependencies(): Verify all required dependencies are available.

Constants:
- MAX_FILE_SIZE: The maximum file size for audio files (25 MB).
- FILE_TOO_LARGE_MESSAGE: The message to display when the file is too large.
- AUDIO_FILES: Dictionary of sample audio files with their paths and Youtube links.
- OUTLINE_MODEL_OPTIONS: List of model options for generating outlines.
- CONTENT_MODEL_OPTIONS: List of model options for generating content.

Usage: 
    Run this script using Streamlit to start the web application.
"""

import streamlit as st
from groq import Groq
import json
import os
import time
from io import BytesIO
from py_youtube import Data
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
from download import download_video_audio, delete_download, validity_checker
from notes import GenerationStatistics, NoteSection, generate_notes_structure, generate_section, create_markdown_file, create_pdf_file, transcribe_audio, generate_transcript_structure, merge_json_structures, create_chunks
import subprocess
import tempfile

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Constants
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
MAX_TEXT_LENGTH = 25000
FILE_TOO_LARGE_MESSAGE = "The audio file is too large for the current size and rate limits using the LLM. If you used a YouTube link, please try a shorter video clip. If you uploaded an audio file, try trimming or compressing the audio to under 25 MB."

# Sample Audio Files
AUDIO_FILES = {
    "Transformers Explained by Google Cloud Tech": {
        "file_path": "assets/audio/transformers_explained.m4a",
        "youtube_link": "https://www.youtube.com/watch?v=SZorAJ4I-sA"
    },
    "The Essence of Calculus by 3Blue1Brown": {
        "file_path": "assets/audio/essence_calculus.m4a",
        "youtube_link": "https://www.youtube.com/watch?v=WUvTyaaNkzM"
    },
    "First 20 minutes of Groq's AMA": {
        "file_path": "assets/audio/groq_ama_trimmed_20min.m4a",
        "youtube_link": "https://www.youtube.com/watch?v=UztfweS-7MU"
    }
}

# Model Options
OUTLINE_MODEL_OPTIONS = [
    "llama-3.1-8b-instant", "llama-3.3-70b-versatile", "meta-llama/llama-guard-4-12b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"
]
CONTENT_MODEL_OPTIONS = [
    "llama-3.1-8b-instant", "llama-3.3-70b-versatile", "meta-llama/llama-guard-4-12b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"
]

# Streamlit Setup
st.set_page_config(
    page_title="ScribePlus",
    page_icon="🗒️",
)

# Session State Initialization
if 'api_key' not in st.session_state:
    st.session_state.api_key = GROQ_API_KEY
if 'groq' not in st.session_state:
    if GROQ_API_KEY:
        st.session_state.groq = Groq()
if 'button_disabled' not in st.session_state:
    st.session_state.button_disabled = False
if 'button_text' not in st.session_state:
    st.session_state.button_text = "Generate Notes"
if 'button_text_2' not in st.session_state:
    st.session_state.button_text_2 = "Generate Transcript"
if 'statistics_text' not in st.session_state:
    st.session_state.statistics_text = ""
if 'notes_title' not in st.session_state:
    st.session_state.notes_title = "generate"
if 'notes' not in st.session_state:
    st.session_state.notes = None
if 'transcript_notes' not in st.session_state:
    st.session_state.transcript_notes = None
if 'youtube_link' not in st.session_state:
    st.session_state.youtube_link = ""
if 'valid_youtube_link' not in st.session_state:
    st.session_state.valid_youtube_link = None

# Main Page Content
st.write("""
# ScribePlus: Create structured notes from audio 🗒️⚡
""")


# Helper Functions
def disable():
    st.session_state.button_disabled = True


def enable():
    st.session_state.button_disabled = False


def empty_st():
    st.empty()


def display_status(text):
    status_text.write(text)


def clear_status():
    status_text.empty()


def display_download_status(text: str):
    download_status_text.write(text)


def clear_download_status():
    download_status_text.empty()


def display_statistics():
    """
    Displays the model statistics and the transcription text as per progress.
    """
    with placeholder.container():
        if st.session_state.statistics_text:
            if "Transcribing audio in background" not in st.session_state.statistics_text:
                st.markdown(
                    st.session_state.statistics_text +
                    "\n\n---\n")  # Format with line if showing statistics
            else:
                st.markdown(st.session_state.statistics_text)
        else:
            placeholder.empty()


def stream_section_content(sections, transcription_text, notes,
                           content_selected_model,
                           total_generation_statistics):
    """
    Recursively streams the content of each section in the notes structure.

    Args:
        sections (dict): A dictionary where keys are section titles and values are strings (content) or nested dictionaries (subsections).
        transcription_text (str): Transcription text.
        notes (Notes): An instance of the Notes class, used to manage and update note contents.
        content_selected_model (str): The selected model for generating content.
        total_generation_statistics (GenerationStatistics): An instance of GenerationStatistics to accumulate statistics from the content generation process.
    """
    for title, content in sections.items():
        if isinstance(content, str):
            if len(notes.return_existing_contents()) > MAX_TEXT_LENGTH:
                notes_text = notes.return_existing_contents(
                )[-MAX_TEXT_LENGTH:]
            else:
                notes_text = notes.return_existing_contents()
            time.sleep(10)
            content_stream = generate_section(
                transcript=transcription_text,
                existing_notes=notes_text,
                section=(title + ": " + content),
                model=str(content_selected_model))
            for chunk in content_stream:
                # Check if GenerationStatistics data is returned instead of str tokens
                chunk_data = chunk
                if type(chunk_data) == GenerationStatistics:
                    total_generation_statistics.add(chunk_data)
                    st.session_state.statistics_text = str(
                        total_generation_statistics)
                    display_statistics()
                elif chunk is not None:
                    st.session_state.notes.update_content(title, chunk)
        elif isinstance(content, dict):
            stream_section_content(content, transcription_text, notes,
                                   content_selected_model,
                                   total_generation_statistics)


def check_dependencies():
    """Verify all required dependencies are available."""
    checks = {
        'ffmpeg': lambda: subprocess.run(['ffmpeg', '-version'], capture_output=True).returncode == 0,
        'groq_api': lambda: st.session_state.get('groq') is not None,
        'temp_dir': lambda: os.access(tempfile.gettempdir(), os.W_OK)
    }

    for name, check in checks.items():
        if not check():
            st.error(f"Dependency check failed: {name}")
            return False
    return True


# Call the dependency check at the start of the application
if not check_dependencies():
    st.stop()

# API Key Validation
def validate_api_key(api_key):
    """Validate the API key format."""
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is required.")
    if not api_key.startswith("gsk_"):
        raise ValueError("Invalid API key format. It should start with 'gsk_'.")

# Validate the API key at the start of the application
try:
    validate_api_key(GROQ_API_KEY)
except ValueError as e:
    st.error(str(e))
    st.stop()

# Sidebar Content
try:
    with st.sidebar:
        st.write(
            f"# 🗒️ ScribePlus \n## Generate notes from audio in seconds using Groq"
        )
        st.write(f"---")

        st.write(f"# Sample Audio Files")

        for audio_name, audio_info in AUDIO_FILES.items():
            st.write(f"### {audio_name}")
            with open(audio_info['file_path'], 'rb') as audio_file:
                audio_bytes = audio_file.read()
            st.download_button(label=f"Download audio",
                               data=audio_bytes,
                               file_name=audio_info['file_path'],
                               mime='audio/m4a')
            st.markdown(f"[Credit Youtube Link]({audio_info['youtube_link']})")
            st.write(f"\n\n")

        st.write(f"---")

        st.write(
            "# Customization Settings\n🧪 These settings are experimental.\n")
        st.write(
            f"By default, ScribePlus uses gemma2 for generating the notes outline and Llama3 for the content. This balances quality with speed and rate limit usage. You can customize these selections below."
        )
        outline_selected_model = st.selectbox("Outline generation:",
                                              OUTLINE_MODEL_OPTIONS)
        content_selected_model = st.selectbox("Content generation:",
                                              CONTENT_MODEL_OPTIONS)

        # Add note about rate limits
        st.info(
            "Important: Different models have different token and rate limits which may cause runtime errors."
        )

    # Main Content
    if st.button('End Generation and Download Notes'):
        if st.session_state.notes is not None:
            markdown_file = create_markdown_file(
                st.session_state.notes.get_markdown_content())
            st.download_button(
                label='Download Text',
                data=markdown_file,
                file_name=f'{st.session_state.notes_title}_notes.txt',
                mime='text/plain')
            pdf_file = create_pdf_file(
                st.session_state.notes.get_markdown_content())
            st.download_button(
                label='Download PDF',
                data=pdf_file,
                file_name=f'{st.session_state.notes_title}_notes.pdf',
                mime='application/pdf')
            st.session_state.notes = None
            st.session_state.button_disabled = False
        elif st.session_state.transcript_notes is not None:
            markdown_file = create_markdown_file(
                st.session_state.transcript_notes.
                get_transcript_markdown_content())
            st.download_button(
                label='Download Text',
                data=markdown_file,
                file_name=f'{st.session_state.notes_title}_transcript.txt',
                mime='text/plain')
            pdf_file = create_pdf_file(st.session_state.transcript_notes.
                                       get_transcript_markdown_content())
            st.download_button(
                label='Download PDF',
                data=pdf_file,
                file_name=f'{st.session_state.notes_title}_transcript.pdf',
                mime='application/pdf')
            st.session_state.transcript_notes = None
            st.session_state.button_disabled = False
        else:
            raise ValueError(
                "Please generate content first before downloading the notes.")

    input_method = st.radio("Choose input method:",
                            ["Upload audio file", "YouTube link"])

    audio_file = None
    youtube_link = None
    groq_input_key = None
    audio_file_path = None
    notes = None
    transcript_notes = None

    with st.form("groqform"):
        if not GROQ_API_KEY:
            groq_input_key = st.text_input(
                "Enter your Groq API Key (gsk_yA...):", "", type="password")

        if input_method == "Upload audio file":
            audio_file = st.file_uploader("Upload an audio file",
                                          type=["mp3", "wav", "m4a"])
        else:
            youtube_link = st.text_input("Enter YouTube link:", "")
            if youtube_link != st.session_state.youtube_link:
                st.session_state.youtube_link = youtube_link
                st.session_state.valid_youtube_link = validity_checker(
                    youtube_link)

            if st.session_state.valid_youtube_link:
                message = st.success("Valid YouTube link")
                time.sleep(3)
                message.empty()

        # Generate notes button
        submitted = st.form_submit_button(
            st.session_state.button_text,
            on_click=disable,
            disabled=st.session_state.button_disabled)

        # Generate transcript button
        submitted_2 = st.form_submit_button(
            st.session_state.button_text_2,
            on_click=disable,
            disabled=st.session_state.button_disabled)

        #processing status
        status_text = st.empty()
        download_status_text = st.empty()
        placeholder = st.empty()

        if submitted or submitted_2:
            st.session_state.button_disabled = True

            if input_method == "YouTube link":
                if st.session_state.valid_youtube_link:
                    display_status("Downloading audio from YouTube link ....")
                    audio_file_path, audio_title = download_video_audio(
                        youtube_link, display_download_status)
                    if audio_file_path is None:
                        st.error(
                            "Failed to download audio from YouTube link. Please try again."
                        )
                        enable()
                        clear_status()
                    else:
                        display_status("Processing Youtube audio ....")
                        print(f'Audio file path is: {audio_file_path}')
                        with open(audio_file_path, 'rb') as f:
                            file_contents = f.read()
                        audio_file = BytesIO(file_contents)
                        if os.path.getsize(audio_file_path) > MAX_FILE_SIZE:
                            raise ValueError(FILE_TOO_LARGE_MESSAGE)
                        audio_file.name = os.path.basename(
                            audio_file_path)  # Set the file name
                        st.session_state.notes_title = str(audio_title)
                        delete_download(audio_file_path)
                    clear_download_status()
                else:
                    raise ValueError("Invalid YouTube link. Please try again.")

            if not GROQ_API_KEY:
                st.session_state.groq = Groq(api_key=groq_input_key)

            try:
                whisper_failed = False
                display_status("Transcribing audio...")
                transcription_text = transcribe_audio(audio_file)
                display_statistics()
            except Exception as error:
                error_dict = None
                if hasattr(error, 'response') and error.response is not None:
                    try:
                        error_dict = json.loads(error.response.text)
                    except json.JSONDecodeError:
                        pass

                if error_dict and 'error' in error_dict and 'code' in error_dict[
                        'error'] and error_dict['error'][
                            'code'] == 'rate_limit_exceeded':
                    whisper_failed = True
                    if youtube_link:
                        try:
                            display_status(
                                "Whisper API rate limit reached. Falling back to YouTube transcript..."
                            )
                            video_data = Data(youtube_link).data()
                            video_id = video_data['id']
                            transcript = YouTubeTranscriptApi.get_transcript(
                                video_id)
                            transcription_text = " ".join(
                                [line['text'] for line in transcript])
                            display_status(
                                "YouTube transcript retrieved successfully.")
                        except Exception as yt_error:
                            st.error(
                                f"Failed to retrieve Youtube Transcript. Error: {yt_error}"
                            )
                            st.stop()
                    else:
                        st.error(
                            "Rate limit reached and no fallback available.")
                        st.stop()
                else:
                    st.error(
                        f"An error occurred during transcription: {str(error)}"
                    )
                    st.stop()

            if submitted:  # Generate notes
                display_status("Generating notes structure....")
                transcription_chunks = []
                if len(transcription_text) > MAX_TEXT_LENGTH or whisper_failed:
                    transcription_chunks = create_chunks(transcription_text)
                    stats_0 = GenerationStatistics(
                        model_name=str(outline_selected_model))
                    chunk_results = []
                    for chunk in transcription_chunks:
                        print("The length of the chunk is {}".format(
                            len(chunk)))
                        time.sleep(15)
                        stats, result = generate_notes_structure(
                            chunk, model=str(outline_selected_model))
                        chunk_results.append(result)
                        stats_0.add(stats)
                    notes_structure, _ = merge_json_structures(chunk_results)
                else:
                    large_model_generation_statistics, notes_structure = generate_notes_structure(
                        transcription_text, model=str(outline_selected_model))
                print("Structure: ", notes_structure)
                display_status("Generating notes ...")
                total_generation_statistics = GenerationStatistics(
                    model_name=str(content_selected_model))
                clear_status()

                try:
                    if isinstance(notes_structure, str):
                        notes_structure_json = json.loads(notes_structure)
                    else:
                        notes_structure_json = notes_structure
                    notes = NoteSection(structure=notes_structure_json,
                                        transcript=transcription_text)
                    st.session_state.notes = notes
                    st.session_state.notes.display_structure()
                    if len(transcription_text) > MAX_TEXT_LENGTH:
                        for i in range(len(transcription_chunks)):
                            for section_index, section_content in notes_structure_json.items(
                            ):
                                if i == section_index:
                                    time.sleep(15)
                                    stream_section_content(
                                        section_content,
                                        transcription_chunks[i], notes,
                                        content_selected_model,
                                        total_generation_statistics)
                    else:
                        stream_section_content(notes_structure_json,
                                               transcription_text, notes,
                                               content_selected_model,
                                               total_generation_statistics)
                except json.JSONDecodeError:
                    st.error(
                        "Failed to decode the notes structure. Please try again."
                    )
                enable()
            elif submitted_2:  # Generate transcript
                display_status("Generating transcript structure....")
                transcription_chunks = []
                if len(transcription_text) > MAX_TEXT_LENGTH:
                    # transcription_chunks = create_chunks(transcription_text)
                    # stats_0 = GenerationStatistics(
                    #     model_name=str(outline_selected_model))
                    # chunk_results = []
                    # for chunk in transcription_chunks:
                    #     print("The length of the chunk is {}".format(
                    #         len(chunk)))
                    #     time.sleep(15)
                    #     stats, result = generate_notes_structure(
                    #         chunk, model=str(outline_selected_model))
                    #     chunk_results.append(result)
                    #     stats_0.add(stats)
                    # notes_structure_json, notes_sections = merge_json_structures(chunk_results)
                    large_model_generation_statistics, notes_structure_1 = generate_notes_structure(
                        transcription_text[-MAX_TEXT_LENGTH:],
                        model=str(outline_selected_model))
                    notes_structure_json = json.loads(notes_structure_1)
                    notes_sections = [title for title in notes_structure_json]
                else:
                    large_model_generation_statistics, notes_structure_1 = generate_notes_structure(
                        transcription_text, model=str(outline_selected_model))
                    notes_structure_json = json.loads(notes_structure_1)
                    notes_sections = [title for title in notes_structure_json]
                notes_structure_2 = generate_transcript_structure(
                    transcription_text, notes_sections)
                notes_structure_json_2 = json.loads(notes_structure_2)
                print(
                    f'Structure is of {type(notes_structure_json_2)} in main.py'
                )
                # print("Structure: ", notes_structure_2)
                transcript_notes = NoteSection(
                    structure=notes_structure_json_2,
                    transcript=transcription_text)
                st.markdown(
                    f"## Transcript:\n{transcript_notes.get_transcript_markdown_content()}"
                )
                st.session_state.transcript_notes = transcript_notes
                # st.session_state.transcript_notes.display_structure()

                st.session_state.button_disabled = False
                enable()

except Exception as e:
    st.session_state.button_disabled = False

    if hasattr(e, 'status_code') and e.status_code == 413:
        st.error(FILE_TOO_LARGE_MESSAGE)
    elif hasattr(e, 'status_code') and e.status_code == 400:
        st.error(FILE_TOO_LARGE_MESSAGE)
    else:
        st.error(f"An error occurred: Error code {str(e.status_code)}")

    if st.button("Clear"):
        st.rerun()
    if audio_file_path is not None:
        delete_download(audio_file_path)
