"""
notes.py

This file contains the functions for the notes section of the app.

Modules:
- streamlit: A Python library for building interactive apps.
- io: A built-in module for working with input/output operations.
- md2pdf: A Python library for converting Markdown to PDF.

Classes:
- GenerationStatistics: A class to represent and calculate statistics for generation tasks.
- NoteSection: A class to represent and manage the notes section of the app.

Functions:
- create_markdown_file():
- create_pdf_file():
- transcribe_audio():
- generate_notes_structure():
- generate_section():
- generate_transcript_structure():
"""
import json
import streamlit as st
from io import BytesIO
import pypandoc
#from langchain_text_splitters import RecursiveCharacterTextSplitter
from semantic_text_splitter import TextSplitter


class GenerationStatistics:
    """
    A class to represent and calculate statistics for generation tasks.

    Attributes:
        input_time (float): The time taken to process the input text.
        output_time (float): The time taken to process the output text.
        input_tokens (int): The number of input tokens.
        output_tokens (int): The number of output tokens.
        total_time (float): The total time taken to process the task.
        model_name (str): The name of the model used for generation.

    Methods:
        get_input_speed(): Calculates and returns the input speed in tokens per second.
        get_output_speed(): Calculates and returns the output speed in tokens per second.
        add(other): Adds the statistics of another instance to this instance.
        __str__(): Returns a string representation of the statistics.
    """

    def __init__(self,
                 input_time=0,
                 output_time=0,
                 input_tokens=0,
                 output_tokens=0,
                 total_time=0,
                 model_name="llama3-8b-8192"):
        self.input_time = input_time
        self.output_time = output_time
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_time = total_time  # Sum of queue, prompt (input), and completion (output) times
        self.model_name = model_name

    def get_input_speed(self):
        """ 
        Tokens per second calculation for input
        """
        if self.input_time != 0:
            return self.input_tokens / self.input_time
        else:
            return 0

    def get_output_speed(self):
        """ 
        Tokens per second calculation for output
        """
        if self.output_time != 0:
            return self.output_tokens / self.output_time
        else:
            return 0

    def add(self, other):
        """
        Add statistics from another GenerationStatistics object to this one.
        """
        if not isinstance(other, GenerationStatistics):
            raise TypeError("Can only add GenerationStatistics objects")

        self.input_time += other.input_time
        self.output_time += other.output_time
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.total_time += other.total_time

    def __str__(self):
        return (
            f"\n## {self.get_output_speed():.2f} T/s ⚡\nRound trip time: {self.total_time:.2f}s  Model: {self.model_name}\n\n"
            f"| Metric          | Input          | Output          | Total          |\n"
            f"|-----------------|----------------|-----------------|----------------|\n"
            f"| Speed (T/s)     | {self.get_input_speed():.2f}            | {self.get_output_speed():.2f}            | {(self.input_tokens + self.output_tokens) / self.total_time if self.total_time != 0 else 0:.2f}            |\n"
            f"| Tokens          | {self.input_tokens}            | {self.output_tokens}            | {self.input_tokens + self.output_tokens}            |\n"
            f"| Inference Time (s) | {self.input_time:.2f}            | {self.output_time:.2f}            | {self.total_time:.2f}            |"
        )


class NoteSection:
    """
    A class to manage and display structured notes with markdown formatting.

    Attributes:
        structure (dict): A nested dictionary representing the notes structure.
        contents (dict): A dictionary to store the contents of each note.
        placeholders (dict): A dictionary to store placeholders for each note.

    Methods:
        flatten_structure(): Flattens the notes structure into a list of section titles.
        update_content(): Updates the content of a given section.
        display_content(): Displays the content of a given section if it is not empty.
        return_existing_contents(): Returns the existing contents as a markdown string.
        display_structure(): Displays the structure and content of the notes.
        display_toc(): Displays the table of contents for the notes.
        get_markdown_content(): Returns the markdown formatted content of the notes.
        get_transcript_markdown_content(): Returns the markdown formatted content of the transcript.
    """

    def __init__(self, structure, transcript):
        self.structure = structure
        self.contents = {
            title: ""
            for title in self.flatten_structure(structure)
        }
        self.placeholders = {
            title: st.empty()
            for title in self.flatten_structure(structure)
        }

    def flatten_structure(self, structure):
        sections = []
        for title, content in structure.items():
            sections.append(title)
            if isinstance(content, dict):
                sections.extend(self.flatten_structure(content))
        return sections

    def update_content(self, title, new_content):
        try:
            self.contents[title] += new_content
            self.display_content(title)
        except TypeError as e:
            pass

    def display_content(self, title):
        if self.contents[title].strip():
            self.placeholders[title].markdown(
                f"## {title}\n{self.contents[title]}")

    def return_existing_contents(self, level=1) -> str:
        existing_content = ""
        for title, content in self.structure.items():
            if self.contents[title].strip(
            ):  # Only include title if there is content
                existing_content += f"{'#' * level} {title}\n{self.contents[title]}.\n\n"
            if isinstance(content, dict):
                existing_content += self.get_markdown_content(
                    content, level + 1)
        return existing_content

    def display_structure(self, structure=None, level=1):
        if structure is None:
            structure = self.structure

        for title, content in structure.items():
            if self.contents[title].strip(
            ):  # Only display title if there is content
                st.markdown(f"{'#' * level} {title}")
                self.placeholders[title].markdown(self.contents[title])
            if isinstance(content, dict):
                self.display_structure(content, level + 1)

    def display_toc(self, structure, columns, level=1, col_index=0):
        for title, content in structure.items():
            with columns[col_index % len(columns)]:
                st.markdown(f"{' ' * (level-1) * 2}- {title}")
            col_index += 1
            if isinstance(content, dict):
                col_index = self.display_toc(content, columns, level + 1,
                                             col_index)
        return col_index

    def get_markdown_content(self, structure=None, level=1):
        """
        Returns the markdown styled pure string with the contents.
        """
        if structure is None:
            structure = self.structure

        markdown_content = ""
        for title, content in structure.items():
            if self.contents[title].strip(
            ):  # Only include title if there is content
                markdown_content += f"{'#' * level} {title}\n{self.contents[title]}.\n\n"
            if isinstance(content, dict):
                markdown_content += self.get_markdown_content(
                    content, level + 1)
        return markdown_content

    def get_transcript_markdown_content(self, structure=None, level=1):
        """
        Returns the markdown styled pure string with the contents.
        """
        if structure is None:
            structure = self.structure

        # print(f'These are the contents of structure: {structure}')

        markdown_content = ""
        for title, content in structure.items(
        ):  # Iterate directly over the list of titles
            markdown_content += f"{'#' * level} {title}\n{content}.\n\n"

        # print(
        #     f'These are the contents of markdown_content: {markdown_content}')
        return markdown_content


def create_markdown_file(content: str) -> BytesIO:
    """
    Create a Markdown file from the provided content.
    """
    markdown_file = BytesIO()
    markdown_file.write(content.encode('utf-8'))
    markdown_file.seek(0)
    return markdown_file


def create_pdf_file(content: str):
    """
    Create a PDF file from the provided content using Pandoc.
    """
    pdf_buffer = BytesIO()
    try:
        pdf_content = pypandoc.convert_text(content, 'pdf', format='md')
        pdf_buffer.write(pdf_content.encode('utf-8'))
        pdf_buffer.seek(0)
    except Exception as e:
        print(f"Error during PDF conversion: {e}")
        raise
    return pdf_buffer


def transcribe_audio(audio_file):
    """
    Transcribes audio using Groq's Whisper API.
    """
    transcription = st.session_state.groq.audio.transcriptions.create(
        file=audio_file,
        model="whisper-large-v3",
        prompt="",
        response_format="json",
        language="en",
        temperature=0.0)

    results = transcription.text
    return results


def create_chunks(transcript, chunk_size=3000, chunk_overlap=200):
    """
    """
    splitter = TextSplitter.from_tiktoken_model("gpt-3.5-turbo", chunk_size)

    texts = splitter.chunks(transcript)
    return texts


def merge_json_structures(json_objects):
    """
    Merges multiple JSON structures into a single structure, using their index as keys.
    Args:
        - json_objects (list): A list of JSON objects or JSON strings.

    Returns:
        - dict: A dictionary where keys are indices and values are the corresponding JSON objects.
        - list: A list of each chunks keys (titles).
    """
    merged_structure = {}
    merged_keys = []
    for i, chunk in enumerate(json_objects):
        try:
            if isinstance(chunk, str):
                chunk_json = json.loads(chunk)
            elif isinstance(chunk, dict):
                chunk_json = chunk
            else:
                raise ValueError(f"Unsupported type for chunk {type(chunk)}")
            for key, value in chunk_json.items():
                merged_keys.append(key)
            merged_structure[i] = chunk_json
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except Exception as e:
            print(f"Error processing chunk {i}: {e}")
    return merged_structure, merged_keys


def generate_notes_structure(transcript: str, model: str = "llama3-70b-8192"):
    """
    Returns notes structure content as well as total tokens and total time for generation.
    """

    shot_example = """
"Introduction": "Introduction to the AMA session, including the topic of Groq scaling architecture and the panelists",
"Panelist Introductions": "Brief introductions from Igor, Andrew, and Omar, covering their backgrounds and roles at Groq",
"Groq Scaling Architecture Overview": "High-level overview of Groq's scaling architecture, covering hardware, software, and cloud components",
"Hardware Perspective": "Igor's overview of Groq's hardware approach, using an analogy of city traffic management to explain the traditional compute approach and Groq's innovative approach"
"""
    completion = st.session_state.groq.chat.completions.create(
        model=model,
        messages=[{
            "role":
            "user",
            "content":
            f"### Transcript {transcript}\n\n### Example\n\n{shot_example}\n\n### Instructions\n\nYour task is to create a JSON structure of section title to content description like in the example for the above transcribed audio. Section titles and content descriptions must be comprehensive. Quality over quantity. Don't include any additional information."
        }],
        temperature=0.3,
        max_tokens=8000,
        top_p=1,
        stream=False,
        response_format={"type": "json_object"},
        stop=None,
    )

    usage = completion.usage
    statistics_to_return = GenerationStatistics(
        input_time=usage.prompt_time,
        output_time=usage.completion_time,
        input_tokens=usage.prompt_tokens,
        output_tokens=usage.completion_tokens,
        total_time=usage.total_time,
        model_name=model)

    return statistics_to_return, completion.choices[0].message.content


def generate_section(transcript: str,
                     existing_notes: str,
                     section: str,
                     model: str = "llama3-8b-8192"):
    """
    Returns notes structure content as well as total tokens and total time for generation.
    """
    stream = st.session_state.groq.chat.completions.create(
        model=model,
        messages=[{
            "role":
            "system",
            "content":
            "You are an expert writer. Generate a comprehensive note for the section provided based factually on the transcript provided. Do *not* repeat any content from previous sections. Avoid giving a premise before the section. Don't repeat section titles."
        }, {
            "role":
            "user",
            "content":
            f"### Transcript\n\n{transcript}\n\n### Existing Notes\n\n{existing_notes}\n\n### Instructions\n\nGenerate comprehensive notes for this section only based on the transcript: \n\n{section}."
        }],
        temperature=0.3,
        max_tokens=8000,
        top_p=1,
        stream=True,
        stop=None,
    )

    for chunk in stream:
        tokens = chunk.choices[0].delta.content
        if tokens:
            yield tokens
        if x_groq := chunk.x_groq:
            if not x_groq.usage:
                continue
            usage = x_groq.usage
            statistics_to_return = GenerationStatistics(
                input_time=usage.prompt_time,
                output_time=usage.completion_time,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
                total_time=usage.total_time,
                model_name=model)
            yield statistics_to_return


def generate_transcript_structure(
    transcript: str,
    sections: list,
    model: str = "llama3-70b-8192",
):
    """
    Returns transcript structure content segmented into sections using a model to identify section boundaries.
    """
    structured_transcript = {}

    # Use the model to identify section boundaries in the transcript.
    completion = st.session_state.groq.chat.completions.create(
        model=model,
        messages=[{
            "role":
            "system",
            "content":
            "You are a transcript editor. Identify the sections in the following transcript, preserving the original text.  Output a JSON object where each key is a section title from the provided list, and the value is the content of that section."
        }, {
            "role":
            "user",
            "content":
            f"### Transcript\n\n{transcript}\n\n### Sections\n\n{sections}\n\n### Instructions\n\nIdentify the sections in the transcript and insert a separator (---) between them. Preserve the original text and do not add any additional information.  Output the structured transcript as a JSON object with the format:\n\n```json\n{{\n  \"{sections[0]}\": \"Content of section 1\",\n  \"{sections[1]}\": \"Content of section 2\",\n  ...\n}}\n```"
        }],
        temperature=0.3,
        max_tokens=8000,
        top_p=1,
        stream=False,
        response_format={"type": "json_object"},
        stop=None,
    )

    # Extract the structured transcript from the model's response.
    structured_transcript = completion.choices[0].message.content

    return structured_transcript
