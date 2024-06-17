import streamlit as st
from openai import OpenAI
from io import BytesIO
from PIL import Image
import base64
import pandas as pd
from io import StringIO

st.session_state['ai_reply'] = ''


# Function for openai response
def generate_openai_response():
    client = OpenAI(api_key=api_key)
    for chunk in client.chat.completions.create(
        model='gpt-4o',
        temperature=0.0,
        max_tokens=300,
        messages=[msg],
        stream=True
    ):
        try:
            st.session_state['ai_reply'] += chunk.choices[0].delta.content
        except:
            pass
        yield chunk


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
                image_container.image(image, caption=img.name)

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


    response_stream = generate_openai_response()
    
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

        st.write_stream(response_stream)

        # Assuming ai_reply is a string containing the markdown table
        ai_md_table = st.session_state['ai_reply']

        # Read markdown table into a dataframe
        df = pd.read_csv(
            StringIO(ai_md_table),
            sep='|',
            skipinitialspace=True,  # Handle leading/trailing spaces
            header=0
        ).dropna(
            axis=1,
            how='all'
        ).iloc[1:]

        # Clean up the column names
        df.columns = df.columns.str.strip()
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

        # Create a downloadable CSV file
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()

        # Create a download link with button styling
        href = f'''
        <a href="data:file/csv;base64,{b64}" download="ai_output.csv">
            <button style="background-color: #4CAF50; border: none; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer;">Download CSV File</button>
        </a>
        '''
        st.markdown(href, unsafe_allow_html=True)


