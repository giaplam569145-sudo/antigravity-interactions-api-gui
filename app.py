import os
import streamlit as st
import google.genai as genai

# Page Config
st.set_page_config(page_title="Antigravity Interactions Explorer", layout="wide")
st.title("Antigravity Interactions Explorer")

st.markdown("""
This app provides a simple GUI to experiment with Google's Interactions API, targeting the **antigravity** agent preview model.
""")

# Initialize Session State
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'env_id' not in st.session_state:
    st.session_state.env_id = None
if 'client' not in st.session_state:
    try:
        st.session_state.client = genai.Client(http_options={"api_version": "v1beta"})
        envs = list(st.session_state.client.environments.list())
        if envs and envs[0][1]:
            st.session_state.env_id = envs[0][1][0].id
        else:
            env_resp = st.session_state.client.environments.create_environment()
            st.session_state.env_id = env_resp.id
    except Exception as e:
        st.error(f"Failed to initialize client or environment: {e}")

agent_name = "antigravity-preview-latest"

st.sidebar.header("Configuration")
stream_output = st.sidebar.checkbox("Stream Output", value=True)

st.sidebar.header("API Request Code")
st.sidebar.markdown(f"""
### Python Snippet
```python
import google.genai as genai

client = genai.Client(http_options={{"api_version": "v1beta"}})

response = client.interactions.create(
    agent="{agent_name}",
    environment="{st.session_state.env_id if st.session_state.env_id else 'your_env_id'}",
    input="Your message here",
    stream={stream_output}
)

if {stream_output}:
    for chunk in response:
        if getattr(chunk, 'interaction', None) and getattr(chunk.interaction, 'output_text', None):
            print(chunk.interaction.output_text, end='')
else:
    print(response.output_text)
```
""")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Say something to antigravity..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            if stream_output:
                response = st.session_state.client.interactions.create(
                    agent=agent_name,
                    environment=st.session_state.env_id,
                    input=prompt,
                    stream=True
                )
                for stream_resp in response:
                    if getattr(stream_resp, 'interaction', None) and getattr(stream_resp.interaction, 'output_text', None):
                        # The output_text contains the *full accumulated text* in each chunk
                        # Let's just update the placeholder with the latest full text
                        full_response = stream_resp.interaction.output_text
                        message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            else:
                response = st.session_state.client.interactions.create(
                    agent=agent_name,
                    environment=st.session_state.env_id,
                    input=prompt,
                    stream=False
                )
                full_response = response.output_text
                message_placeholder.markdown(full_response)

        except Exception as e:
            message_placeholder.markdown(f"**Error:** {e}")
            full_response = f"Error: {e}"
            import traceback
            traceback.print_exc()

    st.session_state.messages.append({"role": "assistant", "content": full_response})
