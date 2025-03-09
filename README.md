<h2 align="center">
 <br>
 ScribePlus: Generate organized notes from audio<br>using Groq, Whisper, and Llama3
 <br>
</h2>

<p align="center">
 <a href="#Overview">Overview</a> •
 <a href="#Features">Features</a> •
 <a href="#Quickstart">Quickstart</a> •
 <a href="#Contributing">Contributing</a>
</p>

<br>

## Overview

[ScribePlus](https://scribeplus.streamlit.app/) is an extension of [ScribeWizard](https://github.com/Bklieger/ScribeWizard). It is a streamlit app that speeds up the creation of structured lecture notes by iteratively structuring and generating notes from transcribed audio lectures using Groq's Whisper API. The app mixes between Llama3-8b, Llama3-70b, mixtral-8x7b and gemma-7b utilizing the models for generating the notes structure and creating the content.


### Features

- 🎧 Generate structured notes using transcribed audio by Whisper-large and text by Llama3
- ⚡ Lightning fast speed transcribing audio and generating text using Groq
- 📖 Scaffolded prompting strategically switches between two models to balance speed and quality
- 🖊️ Markdown styling creates aesthetic notes on the streamlit app that can include tables and code 
- 📂 Allows user to download a text or PDF file with the entire notes contents

### Example Generated Notes:

| Example                                      | Youtube Link                                                                                                                                |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| [Transformers Explained by Google Cloud Tech](examples/transformers_explained/generated_notes.pdf)             |  https://www.youtube.com/watch?v=SZorAJ4I-sA                                       |
| [The Essence of Calculus by 3Blue1Brown](examples/essence_calculus/generated_notes.pdf) | https://www.youtube.com/watch?v=WUvTyaaNkzM                                            |

> As with all generative AI, content may include inaccurate or placeholder information. ScribePlus is in beta and all feedback is welcome!

---

## Quickstart

> [!IMPORTANT]
> To use ScribePlus, you would need an api token from [GroqCloud](https://console.groq.com/keys)
> You can use a hosted version at [groqnotes.replit.app](https://groqnotes.streamlit.app).
> Alternatively, you can run ScribePlus locally with Streamlit using the quickstart instructions.


### Hosted on Replit:

You can also use the hosted version on replit at [groqnotes.replit.app](https://groqnotes.streamlit.app)
> The project can be forked on replit here: [replit.com](https://replit.com/@KevinAfachao/groqtranscript-1?v=1)

### Run locally:

Alternative, you can run ScribePlus locally with streamlit.

#### Step 1
First, you can set your Groq API key in the environment variables:

~~~
export GROQ_API_KEY="gsk_yA..."
~~~

This is an optional step that allows you to skip setting the Groq API key later in the streamlit app.

#### Step 2
Next, you can set up a virtual environment and install the dependencies.

~~~
python3 -m venv venv
~~~

~~~
source venv/bin/activate
~~~

~~~
pip3 install -r requirements.txt
~~~


#### Step 3
Finally, you can run the streamlit app.

~~~
python3 -m streamlit run main.py
~~~

## Details


### Technologies

- Streamlit
- Llama3 on Groq Cloud
- Whisper-large on Groq Cloud

### Limitations

ScribePlus may generate inaccurate information or placeholder content. It should be used to generate notes with discretion.


## Contributing

Improvements through PRs are welcome!
