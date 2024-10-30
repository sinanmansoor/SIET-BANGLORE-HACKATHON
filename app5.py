import os
import streamlit as st
import google.generativeai as gen_ai
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
from langdetect import detect
import tempfile
from PIL import Image
import pytesseract  # For OCR on images
from PyPDF2 import PdfReader  # For reading PDFs

# Set your Google API Key
GOOGLE_API_KEY = "AIzaSyAOkpZALljzgG-XV_ioicA95ByXNK2gVi0"

# Set up Google Gemini-Pro AI model
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

st.set_page_config(
    page_title="Chat with Gemini-Pro!",
    page_icon=":brain:"  # Favicon emoji
)

# Initialize chat session in Streamlit if not already present
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

# Function to translate roles between Gemini-Pro and Streamlit terminology
def translate_role_for_streamlit(user_role):
    return "assistant" if user_role == "model" else user_role

# Display the chatbot's title on the page
st.title("🤖 Gemini Pro - ChatBot")

# Display the chat history
if st.session_state.chat_session.history:
    for message in st.session_state.chat_session.history:
        try:
            if isinstance(message, dict):
                role = translate_role_for_streamlit(message['role'])
                text = message['parts'][0]['text']
            else:
                role = translate_role_for_streamlit(message.role)
                text = message.parts[0].text

            with st.chat_message(role):
                st.markdown(text)

        except AttributeError:
            st.error("Error accessing message attributes.")

# System instruction for context
system_instruction = "You are an expert chatbot that only responds to agriculture-related queries."

# Input field for user's message
user_prompt = st.chat_input("Ask Gemini-Pro...")

# ** New Section: File and Image Upload **
uploaded_file = st.file_uploader("Upload an image or document", type=["jpg", "jpeg", "png", "pdf", "txt"])

if uploaded_file:
    content = ""
    if uploaded_file.type.startswith("image/"):
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

        # Extract text from the image using OCR
        content = pytesseract.image_to_string(image)
        st.text_area("Extracted Text from Image", content)

    elif uploaded_file.type in ["application/pdf", "text/plain"]:
        if uploaded_file.type == "text/plain":
            content = uploaded_file.read().decode("utf-8")
            st.text_area("Text File Contents", content)
        else:  # PDF
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                content += page.extract_text()
            st.text_area("Extracted Text from PDF", content)

    if content:
        # Summarize or provide answers based on the extracted content
        summary_prompt = f"{system_instruction}\nHere is some content: {content}\nProvide a summary or answer the user's question based on this content."
        if user_prompt:
            summary_prompt += f"\nUser: {user_prompt}\nAssistant:"

            with st.spinner("Thinking..."):
                try:
                    gemini_response = st.session_state.chat_session.send_message(summary_prompt)
                    response_text = gemini_response.text
                    with st.chat_message("assistant"):
                        st.markdown(response_text)

                except Exception as e:
                    st.error(f"Error occurred: {str(e)}")

# Process user prompt immediately after it's entered
if user_prompt:
    full_prompt = f"{system_instruction}\nUser: {user_prompt}\nAssistant:"
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.spinner("Thinking..."):
        try:
            gemini_response = st.session_state.chat_session.send_message(full_prompt)
            response_text = gemini_response.text

            # Check if the response is agriculture-related
            if "agriculture" in user_prompt.lower() or "farm" in user_prompt.lower() or "crop" in user_prompt.lower():
                # Display response
                with st.chat_message("assistant"):
                    st.markdown(response_text)
            else:
                # Notify the user that their query is out of scope
                out_of_scope_message = "I'm here to assist you with agriculture-related topics only. Please ask a relevant question."
                with st.chat_message("assistant"):
                    st.markdown(out_of_scope_message)

            language = detect(user_prompt)
            if language not in ['en', 'hi', 'ml', 'kn']:
                language = 'en'

            temp_dir = "C:/Temp"
            os.makedirs(temp_dir, exist_ok=True)

            audio_file = os.path.join(temp_dir, "response.mp3")
            tts = gTTS(text=response_text, lang=language)
            tts.save(audio_file)

            if os.path.exists(audio_file):
                audio = AudioSegment.from_mp3(audio_file)
                play(audio)

            # Update chat session history
            st.session_state.chat_session.history.append({"role": "model", "parts": [{"text": response_text}]})

        except Exception as e:
            st.error(f"Error occurred: {str(e)}")

# Voice input feature
if st.button("Speak"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        audio = recognizer.listen(source)
        st.write("Processing...")
        try:
            voice_input = recognizer.recognize_google(audio)
            st.chat_message("user").markdown(voice_input)

            full_voice_input = f"{system_instruction}\nUser: {voice_input}\nAssistant:"

            with st.spinner("Thinking..."):
                try:
                    gemini_response = st.session_state.chat_session.send_message(full_voice_input)
                    response_text = gemini_response.text

                    if "agriculture" in voice_input.lower() or "farm" in voice_input.lower() or "crop" in voice_input.lower():
                        with st.chat_message("assistant"):
                            st.markdown(response_text)
                    else:
                        out_of_scope_message = "I'm here to assist you with agriculture-related topics only. Please ask a relevant question."
                        with st.chat_message("assistant"):
                            st.markdown(out_of_scope_message)

                    # Update chat session history
                    st.session_state.chat_session.history.append({"role": "model", "parts": [{"text": response_text}]})

                except Exception as e:
                    st.error(f"Error occurred: {str(e)}")

        except sr.UnknownValueError:
            st.error("Sorry, I could not understand the audio.")
        except sr.RequestError:
            st.error("Could not request results from Google Speech Recognition service.")
