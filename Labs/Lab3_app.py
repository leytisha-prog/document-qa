from openai import OpenAI
import streamlit as st


st.title ("Chatty G - Lab 3: Streamlit Chat Interface")

# Below is the code to set up OpenAI client and default model - pull responses from secrets

# Set OpenAI API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])

# Set a default model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

# Below is the code for a simple chat interface using Streamlit's chat components

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun 
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Hello! I'm Chatty G, your AI assistant. How can I help you today?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

# Display assistant response in chat message container
with st.chat_message("assistant"):
     stream = client.chat.completions.create(
         model=st.session_state["openai_model"],
         messages=[
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
         ],
         stream=True,
     )
     response = st.write_stream(stream)
st.session_state.messages.append({"role": "assistant", "content": response})        
   



    





