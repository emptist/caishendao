import streamlit as st
import os


def set_page_background_color(df):
    """set page background color based on signals in df
    
    color mapping:
    - deep red (#c62828)
    - shallow red (#ffe6e6)
    - deep green (#2e7d32)
    - shallow green (#e8f5e8)
    - deep blue: #0022ff
    - shallow blue: #e6f7ff #0007ff
    
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
            bg_color = '#ffe6e6'
        elif df.buy.iloc[-1]:
            bg_color = '#e6f7ff'
        elif df.sput.iloc[-1]: #| df.buy.iloc[-1]:
            bg_color = '#0007ff'

    except Exception as e:
        # 如果出现任何错误，使用默认背景色并打印错误信息
        print(f"设置背景色时出错: {e}")
        bg_color = '#ffffff'
    
    # 使用CSS设置页面背景
    st.markdown(
        f"""<style>
            .main {{ background-color: {bg_color}; }}
            .stApp {{ background-color: {bg_color}; }}
        </style>""",
        unsafe_allow_html=True
    )


def set_custom_background_color(color):
    """设置自定义页面背景颜色
    
    Args:
        color: CSS颜色代码，例如 '#ffffff' 或 'white'
    """
    try:
        # 使用CSS设置页面背景
        st.markdown(
            f"""<style>
                .main {{ background-color: {color}; }}
                .stApp {{ background-color: {color}; }}
            </style>""",
            unsafe_allow_html=True
        )
    except Exception as e:
        print(f"设置自定义背景色时出错: {e}")



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