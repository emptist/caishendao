import streamlit as st
import os


def set_page_background_color(df):
    """set page background color based on signals in df
    Args:
        df: data frame with signals
    """

    if len(df) == 0:
        return
        
    # default to white background
    bg_color = '#ffffff'
    try:
        if df.sell.iloc[-1]:
            bg_color = '#c62828'
        elif df.scall.iloc[-1]:
            bg_color = '#e63c5e'
        elif df.buy.iloc[-1]:
            bg_color = '#f4edd5' #'#ffffff'
        elif df.sput.iloc[-1]: #| df.buy.iloc[-1]:
            bg_color = '#f4edd5' #'#ffffff'
        else:
            bg_color = '#4713ea' #'#9ba9f4'

    except Exception as e:
        # If any error occurs, use the default background color and print the error message
        print(f"Error setting background color: {e}")
        bg_color = '#9ba9f4'
    
    # Using CSS to set page background
    st.markdown(
        f"""<style>
            .main {{ background-color: {bg_color}; }}
            .stApp {{ background-color: {bg_color}; }}
        </style>""",
        unsafe_allow_html=True
    )


def set_custom_background_color(color):
    """Set custom page background color
    
    Args:
        color: CSS color code, e.g. '#ffffff' or 'white'
    """
    try:
        # Using CSS to set page background
        st.markdown(
            f"""<style>
                .main {{ background-color: {color}; }}
                .stApp {{ background-color: {color}; }}
            </style>""",
            unsafe_allow_html=True
        )
    except Exception as e:
            print(f"Error setting custom background color: {e}")



def play_audio():
    local_file_path = './dizang.mp3'  # Ensure the file is in the same directory as your script
    # Read the local audio file with error handling
    if os.path.exists(local_file_path):
        try:
            with open(local_file_path, 'rb') as audio_file:
                data = audio_file.read()
            st.audio(data,format='audio/mpeg',autoplay=True,loop=True)
        except Exception as e:
            st.warning(f"Can't play audio: {e}")
    else:
        st.info(f"File not found: {local_file_path}")