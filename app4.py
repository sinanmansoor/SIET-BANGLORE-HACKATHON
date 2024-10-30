import os
import streamlit as st
import google.generativeai as gen_ai
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
from langdetect import detect
from PIL import Image
import pytesseract  # For text extraction from images

# Set your Google API Key
GOOGLE_API_KEY = "AIzaSyAOkpZALljzgG-XV_ioicA95ByXNK2gVi0"  # Replace with your actual API Key

# Set up Google Gemini-Pro AI model
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

st.set_page_config(
    page_title="Chat with AgriBot!",
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

# Language selection
language_choice = st.selectbox("Select your preferred language:", 
                                 ["English", "Hindi", "Malayalam", "Kannada"])

# Display the chat history
if st.session_state.chat_session.history:
    for message in st.session_state.chat_session.history:
        try:
            with st.chat_message(translate_role_for_streamlit(message['role'])):
                st.markdown(message['content'])
        except KeyError:
            st.error(f"Error displaying message: {str(message)}")

# System instruction for context
system_instruction = "You are an expert chatbot that only responds to agriculture-related queries."

# Input field for user's message
user_prompt = st.chat_input(f"Ask AgriBot in {language_choice}...")

if user_prompt:
    # Detect the language of the user input
    detected_language = detect(user_prompt)

    # Prepend system instruction to user prompt
    full_prompt = f"{system_instruction}\nUser: {user_prompt}\nAssistant:"

    # Add user's message to chat and display it
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Use st.spinner to indicate that processing is happening
    with st.spinner("Thinking..."):
        try:
            # Send the full prompt to Gemini-Pro and get the response
            gemini_response = st.session_state.chat_session.send_message(full_prompt)

            # Check the response structure
            if hasattr(gemini_response, 'text'):
                translated_response = gemini_response.text
            else:
                translated_response = "No response from the model."

            # Display response and play audio
            temp_dir = "C:/Temp"
            os.makedirs(temp_dir, exist_ok=True)

            audio_file = os.path.join(temp_dir, "response.mp3")
            tts = gTTS(text=translated_response, lang=detected_language)
            tts.save(audio_file)

            if os.path.exists(audio_file):
                audio = AudioSegment.from_mp3(audio_file)
                play(audio)

            with st.chat_message("assistant"):
                st.markdown(translated_response)

            st.session_state.chat_session.history.append({"role": "model", "content": translated_response})

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
            language_code = {
                "Hindi": "hi",
                "Malayalam": "ml",
                "Kannada": "kn",
                "English": "en"
            }[language_choice]

            voice_input = recognizer.recognize_google(audio, language=language_code)
            detected_language = language_code
            st.chat_message("user").markdown(voice_input)

            full_voice_input = f"{system_instruction}\nUser: {voice_input}\nAssistant:"

            with st.spinner("Thinking..."):
                gemini_response = st.session_state.chat_session.send_message(full_voice_input)

                if hasattr(gemini_response, 'text'):
                    translated_response = gemini_response.text
                else:
                    translated_response = "No response from the model."

                audio_file = os.path.join(temp_dir, "response.mp3")
                tts = gTTS(text=translated_response, lang=detected_language)
                tts.save(audio_file)

                if os.path.exists(audio_file):
                    audio = AudioSegment.from_mp3(audio_file)
                    play(audio)

                with st.chat_message("assistant"):
                    st.markdown(translated_response)

                st.session_state.chat_session.history.append({"role": "model", "content": translated_response})

        except sr.UnknownValueError:
            st.error("Sorry, I could not understand the audio.")
        except sr.RequestError:
            st.error("Could not request results from Google Speech Recognition service.")

# File upload feature
uploaded_file = st.file_uploader("Upload an image for recognition:", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Read the uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    # Extract text from the image
    extracted_text = pytesseract.image_to_string(image)
    st.write("Extracted Text:")
    st.write(extracted_text)

    # Prepend system instruction to extracted text
    full_image_input = f"{system_instruction}\nUser: {extracted_text}\nAssistant:"

    if extracted_text.strip():
        with st.spinner("Processing extracted text..."):
            try:
                gemini_response = st.session_state.chat_session.send_message(full_image_input)

                if hasattr(gemini_response, 'text'):
                    translated_response = gemini_response.text
                else:
                    translated_response = "No response from the model."

                # Display the response and play audio
                audio_file = os.path.join(temp_dir, "response_image.mp3")
                tts = gTTS(text=translated_response, lang=detected_language)
                tts.save(audio_file)

                if os.path.exists(audio_file):
                    audio = AudioSegment.from_mp3(audio_file)
                    play(audio)

                with st.chat_message("assistant"):
                    st.markdown(translated_response)

                st.session_state.chat_session.history.append({"role": "model", "content": translated_response})

            except Exception as e:
                st.error(f"Error occurred: {str(e)}")
