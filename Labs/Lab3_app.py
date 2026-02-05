from openai import OpenAI
import streamlit as st


st.title ("Chatty G - Lab 3: Streamlit Chat Interface")

# Below is the code to set up OpenAI client and default model - pull responses from secrets

# Set OpenAI API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])

# Set a default model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4-turbo"

# Below is the code for a simple chat interface using Streamlit's chat components

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": (
                "You are Chatty G, a helpful and friendly AI assistant."
                "After answering a question, ask the user if they have any follow-up questions or if they would like to know more about a specific topic."
                "Do not make up answers if you do not know the answer to a question."
                "Do not repeat this question in later turns."
                "Hello! I'm Chatty G, your AI assistant."
            )
        }   
    ]

# Display chat messages from history on app rerun 
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What would you like to ask Chatty G?"):
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
   

# Conversation Buffer to store the chat history 
def trim_history(max_user_turns: int = 2) -> None:
    """
    Keeps:
    - the system message (the last two messages in the history list)
    - the last 'max_user_turns' user+assistant pairs (2 turns = 4 messages)
    """
    msgs = st.session_state.messages

    system_msgs = [m for m in msgs if m["role"] == "system"]
    chat_msgs = [m for m in msgs if m["role"] != "system" ]

    # Keep the system messages and the last 'max_user_turns' user+assistant pairs
    st.session_state.messages = system_msgs + chat_msgs[-(max_user_turns * 2):]
    


    





