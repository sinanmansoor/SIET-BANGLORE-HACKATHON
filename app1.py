import os
import streamlit as st
import google.generativeai as gen_ai
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
from langdetect import detect
import tempfile

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
        # Check if message is a dict or has attributes and access accordingly
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

if user_prompt:
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

            # Check if the response indicates the input was out of scope
            response_text = gemini_response.text
            if "I'm here to assist you with agriculture-related topics" in response_text:
                # Display the out-of-scope message
                with st.chat_message("assistant"):
                    st.markdown(response_text)
            else:
                # Detect language of the user prompt
                language = detect(user_prompt)
                # Check if the detected language is supported
                if language not in ['en', 'hi', 'ml', 'kn']:  # Supported languages
                    language = 'en'  # Default to English if not supported

                # Use a custom directory for temporary files
                temp_dir = "C:/Temp"  # Change this to a directory you know you have permission to write
                os.makedirs(temp_dir, exist_ok=True)  # Create the directory if it doesn't exist

                # Use a temporary file for saving audio
                audio_file = os.path.join(temp_dir, "response.mp3")

                # Convert Gemini's response to speech
                tts = gTTS(text=response_text, lang=language)
                tts.save(audio_file)

                # Play the audio if file was created
                if os.path.exists(audio_file):
                    audio = AudioSegment.from_mp3(audio_file)
                    play(audio)

                # Display Gemini-Pro's response
                with st.chat_message("assistant"):
                    st.markdown(response_text)

                # Update the chat session history
                st.session_state.chat_session.history.append({"role": "model", "parts": [{"text": response_text}]})

        except Exception as e:
            # Handle all exceptions and show an error message
            st.error(f"Error occurred: {str(e)}")

# Voice input feature
if st.button("Speak"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        audio = recognizer.listen(source)
        st.write("Processing...")
        try:
            # Convert audio to text
            voice_input = recognizer.recognize_google(audio)
            st.chat_message("user").markdown(voice_input)

            # Prepend system instruction to voice input
            full_voice_input = f"{system_instruction}\nUser: {voice_input}\nAssistant:"

            # Use st.spinner to indicate that processing is happening
            with st.spinner("Thinking..."):
                try:
                    # Send voice input to Gemini-Pro and get the response
                    gemini_response = st.session_state.chat_session.send_message(full_voice_input)

                    # Check if the response indicates the input was out of scope
                    response_text = gemini_response.text
                    if "I'm here to assist you with agriculture-related topics" in response_text:
                        # Display the out-of-scope message
                        with st.chat_message("assistant"):
                            st.markdown(response_text)
                    else:
                        # Detect language of the voice input
                        language = detect(voice_input)
                        # Check if the detected language is supported
                        if language not in ['en', 'hi', 'ml', 'kn']:  # Supported languages
                            language = 'en'  # Default to English if not supported

                        # Use a custom directory for temporary files
                        temp_dir = "C:/Temp"  # Change this to a directory you know you have permission to write
                        os.makedirs(temp_dir, exist_ok=True)  # Create the directory if it doesn't exist

                        # Use a temporary file for saving audio
                        audio_file = os.path.join(temp_dir, "response.mp3")

                        # Convert response to speech
                        tts = gTTS(text=response_text, lang=language)
                        tts.save(audio_file)

                        # Play the audio if file was created
                        if os.path.exists(audio_file):
                            audio = AudioSegment.from_mp3(audio_file)
                            play(audio)

                        # Display Gemini-Pro's response
                        with st.chat_message("assistant"):
                            st.markdown(response_text)

                        # Update the chat session history
                        st.session_state.chat_session.history.append({"role": "model", "parts": [{"text": response_text}]})

                except Exception as e:
                    # Handle all exceptions and show an error message
                    st.error(f"Error occurred: {str(e)}")

        except sr.UnknownValueError:
            st.error("Sorry, I could not understand the audio.")
        except sr.RequestError:
            st.error("Could not request results from Google Speech Recognition service.")
