import os
import streamlit as st
import google.generativeai as gen_ai
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
from langdetect import detect

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
st.title("🤖 AgriBot")

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

            # Display the response based on the selected language
            # Use a custom directory for temporary files
            temp_dir = "C:/Temp"  # Change this to a directory you know you have permission to write
            os.makedirs(temp_dir, exist_ok=True)  # Create the directory if it doesn't exist

            # Use a temporary file for saving audio
            audio_file = os.path.join(temp_dir, "response.mp3")

            # Convert Gemini's response to speech
            tts = gTTS(text=translated_response, lang=detected_language)  # Use detected_language here
            tts.save(audio_file)

            # Play the audio if the file was created
            if os.path.exists(audio_file):
                audio = AudioSegment.from_mp3(audio_file)
                play(audio)

            # Display Gemini-Pro's response
            with st.chat_message("assistant"):
                st.markdown(translated_response)

            # Update the chat session history
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
            # Adjusted language code mapping
            language_code = {
                "Hindi": "hi",
                "Malayalam": "ml",
                "Kannada": "kn",
                "English": "en"
            }[language_choice]

            # Convert audio to text
            voice_input = recognizer.recognize_google(audio, language=language_code)
            detected_language = language_code  # Set detected_language to the chosen language code
            st.chat_message("user").markdown(voice_input)

            # Prepend system instruction to voice input
            full_voice_input = f"{system_instruction}\nUser: {voice_input}\nAssistant:"

            # Use st.spinner to indicate that processing is happening
            with st.spinner("Thinking..."):
                try:
                    # Send voice input to Gemini-Pro and get the response
                    gemini_response = st.session_state.chat_session.send_message(full_voice_input)

                    # Check the response structure
                    if hasattr(gemini_response, 'text'):
                        translated_response = gemini_response.text
                    else:
                        translated_response = "No response from the model."

                    # Use a custom directory for temporary files
                    temp_dir = "C:/Temp"  # Change this to a directory you know you have permission to write
                    os.makedirs(temp_dir, exist_ok=True)  # Create the directory if it doesn't exist

                    # Use a temporary file for saving audio
                    audio_file = os.path.join(temp_dir, "response.mp3")

                    # Convert response to speech
                    tts = gTTS(text=translated_response, lang=detected_language)  # Use detected_language here
                    tts.save(audio_file)

                    # Play the audio if the file was created
                    if os.path.exists(audio_file):
                        audio = AudioSegment.from_mp3(audio_file)
                        play(audio)

                    # Display Gemini-Pro's response
                    with st.chat_message("assistant"):
                        st.markdown(translated_response)

                    # Update the chat session history
                    st.session_state.chat_session.history.append({"role": "model", "content": translated_response})

                except Exception as e:
                    st.error(f"Error occurred: {str(e)}")

        except sr.UnknownValueError:
            st.error("Sorry, I could not understand the audio.")
        except sr.RequestError:
            st.error("Could not request results from Google Speech Recognition service.")
