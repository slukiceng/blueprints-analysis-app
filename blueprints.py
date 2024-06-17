import streamlit as st
from openai import OpenAI
from io import BytesIO
from PIL import Image
import base64

# Set up page configuration
st.set_page_config(page_title='CAD Blueprint Analysis AI', page_icon='👁️', layout='wide')

# Sidebar for user inputs
with st.sidebar:
    st.markdown('# Menu')
    api_key = st.text_input('OpenAI API Key', '', type='password')
    img_input = st.file_uploader('Images', accept_multiple_files=True)
    send_button = st.button('Send')  # Move the Send button to the sidebar

# Main page content
title = st.empty()
title.markdown('# CAD Blueprint Analysis AI')

image_container = st.empty()

# Display placeholder image if no response given yet
if 'response_given' not in st.session_state:
    st.session_state['response_given'] = False

if not st.session_state['response_given']:
    image_container.image('images/cad-placeholder.png', caption='Example contract')

    # Display images if uploaded
    if img_input:
        for img in img_input:
            if img.name.split('.')[-1].lower() not in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                st.warning('Only .jpg, .png, .gif, or .webp are supported')
            else:
                image = Image.open(img)
                image_container.image(image, caption=img.name, use_column_width=True)

# Send API request
if send_button:  # Check if the button is pressed
    if not api_key:
        st.warning('API Key required')
        st.stop()

    msg = {'role': 'user', 'content': []}
    msg['content'].append({'type': 'text', 'text': 'Provide a take-off of the quantities from this engineering drawing returning ONLY as a markdown table.'})
    images = []
    for img in img_input:
        img_format = img.name.split('.')[-1].lower()
        if img_format in ['png', 'jpeg', 'gif', 'webp']:
            image = Image.open(img)
            buffered = BytesIO()
            image.save(buffered, format=img_format.upper())
            encoded_img = base64.b64encode(buffered.getvalue()).decode('utf-8')
            images.append(img)
            msg['content'].append(
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': f'data:image/{img_format};base64,{encoded_img}',
                        'detail': 'low'
                    }
                }
            )
        else:
            st.warning(f"Unsupported image format: {img_format}")
            st.stop()

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model='gpt-4o',
        temperature=0.0,
        max_tokens=300,
        messages=[msg],
        stream=True
    )
    st.session_state['response_given'] = True

    # Clear the image container and display the AI output in columns
    image_container.empty()
    col1, col2 = st.columns(2)
    
    with col1:
        if img_input:
            for img in img_input:
                image = Image.open(img)
                st.image(image, caption=img.name, use_column_width=True)
    
    with col2:
        st.markdown('# AI Output')
        st.write_stream(response)
