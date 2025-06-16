import streamlit as st
from openai import OpenAI
import json
from datetime import datetime
import os

# ------------------------
# Constants
# ------------------------
ADMIN_PASSWORD = "admin123"
CHAT_LOGS_FOLDER = "chat_logs"

# ------------------------
# ChatGPT API Setup
# ------------------------
# It is recommended to use Streamlit secrets for your API key
# client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"]) 
# For local testing, you can use a placeholder.
# Make sure to replace "YOUR_API_KEY" with your actual key to run the chat feature.
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    #client = OpenAI(api_key="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") 
except Exception as e:
    # This will prevent the app from crashing if the API key is not set
    client = None

# ------------------------
# Main Navigation Controller
# ------------------------
def main():
    if 'page' not in st.session_state:
        st.session_state.page = 0

    # Page routing dictionary
    pages = {
        0: page1,
        1: survey_page,
        2: personality_and_ai_survey_page,
        3: page2,
        4: page3, # Chat page
        5: page4,
        6: feedback_page,
        7: page5,
        99: admin_view
    }
    
    page_function = pages.get(st.session_state.page)
    if page_function:
        page_function()
    else:
        st.session_state.page = 0 # Default to first page if state is invalid
        page1()


# ------------------------
# Restart Button Helper
# ------------------------
def restart_button():
    if st.button("Return to Start"):
        saved_id = st.session_state.get("prolific_id", "")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.prolific_id = saved_id
        st.session_state.page = 0
        st.rerun()

# ------------------------
# Chat History Persistence
# ------------------------
def save_chat_to_file():
    prolific_id = st.session_state.get("prolific_id", "anonymous")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(CHAT_LOGS_FOLDER, exist_ok=True)
    filename = f"chat_{prolific_id}_{timestamp}.json"

    data = {
        "prolific_id": prolific_id,
        "timestamp": timestamp,
        "survey_responses": st.session_state.get("survey_responses", {}),
        "chat_history": st.session_state.get("chat_history", []),
        "summary": st.session_state.get("summary_text", ""),
        "feedback": st.session_state.get("feedback_responses", {})
    }

    file_path = os.path.join(CHAT_LOGS_FOLDER, filename)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
    st.success(f"Data saved to {file_path}")


# ------------------------
# Page 1: Login
# ------------------------
def page1():
    st.title("Research Participation")
    login_type = st.radio("Login as:", ["Participant", "Admin"], horizontal=True)

    if login_type == "Participant":
        new_id = st.text_input("Enter your Prolific ID:", key="prolific_id_input")
        if st.button("Next") and new_id:
            st.session_state.prolific_id = new_id
            st.session_state.page = 1
            st.rerun()
    else:
        admin_password = st.text_input("Enter Admin Password:", type="password")
        if st.button("Login"):
            if admin_password == ADMIN_PASSWORD:
                st.session_state.page = 99
                st.rerun()
            else:
                st.error("Incorrect password")

# ------------------------
# Page 1.5: Survey
# ------------------------
def survey_page():
    st.title("Pre-Chat Survey")
    with st.form("pre_chat_survey_form"):
        responses = {}
        
        responses['age'] = st.number_input("How old are you?", min_value=0, max_value=120, step=1)
        responses['gender'] = st.radio("Which gender do you identify with?", ["Male", "Female", "Non-binary / third gender", "Prefer not to say"])
        responses['education'] = st.radio("What is the highest level of education that you have completed?", ["Highschool", "Bachelor's Degree", "Master's degree", "Doctorate", "Other"])
        if responses['education'] == "Other":
            responses['education_other'] = st.text_input("Please specify your education level:")
        responses['religion'] = st.text_input("Which religion do you align with, if any?")

        responses['experience_with_ai'] = st.radio("How familiar are you with AI tools like ChatGPT?", ["Not familiar", "Somewhat familiar", "Very familiar"])
        responses['creative_writing_frequency'] = st.radio("How often do you engage in creative writing (e.g., stories, blogs)?", ["Never", "Sometimes", "Often"])
        
        st.markdown("---")
        st.subheader("Block 2: Current Emotional State (SAM)")
        if os.path.exists("images/SAM Model.jpeg"):
            st.image("images/SAM Model.jpeg", caption="Self-Assessment Manikin (SAM)", use_column_width=True)
        else:
            st.warning("SAM Model image not found. Make sure it's in an 'images' subfolder.")

        responses['valence'] = st.slider("Valence (Unpleasant ← → Pleasant)", 1, 9, 5)
        responses['arousal'] = st.slider("Arousal (Calm ← → Excited)", 1, 9, 5)
        
        submitted = st.form_submit_button("Next")
        if submitted:
            st.session_state.survey_responses = responses
            st.session_state.page = 2
            st.rerun()

# ------------------------
# Page 2: Personality and AI Survey
# ------------------------
def personality_and_ai_survey_page():
    st.title("Follow-up Survey")

    st.markdown("""
        <style>
            div.row-widget.stRadio > div {
                display: flex;
                flex-direction: row;
                justify-content: center;
            }
            div.row-widget.stRadio > div > label > div:nth-of-type(2) {
                display: none;
            }
            div.row-widget.stRadio > div > label {
                padding: 0 20px;
            }
        </style>
    """, unsafe_allow_html=True)

    matrix_questions = {
        "Please rate the following statement: I see myself as someone who...": [
            "is reserved",
            "is generally trusting",
            "tends to be lazy",
            "is relaxed, handles stress well",
            "has few artistic interests",
            "is outgoing, sociable",
            "tends to find faults with others",
            "does a thorough job",
            "gets nervous easily"
        ],
        "Work Style Preference": [
            "I prefer to work with other in a group, rather than working alone",
            "If given a choice: I would rather do a job where I can work alone, rather do a job where I have to work with others",
            "Working in a group is better than working alone"
        ],
        "Please rate each statement regarding Artificial Intelligence (AI)": [
            "Generally I would trust AI",
            "AI can help me solve many problems",
            "I think it is a good idea to rely on AI for help",
            "I may not trust information I get from AI",
            "AI is reliable",
            "I would rely on AI"
        ]
    }
    
    likert_options = ["Strongly Disagree", "Somewhat Disagree", "Neither Agree or Disagree", "Somewhat Agree", "Strongly Agree"]
    
    with st.form("personality_survey_form"):
        responses = {}
        
        for section, questions in matrix_questions.items():
            st.subheader(section)
            
            header_cols = st.columns([3, 5])
            with header_cols[1]:
                sub_cols = st.columns(len(likert_options))
                for i, option in enumerate(likert_options):
                    with sub_cols[i]:
                        st.markdown(f'<p style="text-align: center; font-weight: bold;">{option}</p>', unsafe_allow_html=True)
            st.divider()

            for stmt in questions:
                row_cols = st.columns([3, 5])
                with row_cols[0]:
                    st.write(stmt)
                with row_cols[1]:
                    responses[stmt] = st.radio(
                        label=stmt, 
                        options=likert_options, 
                        key=f"personality_{stmt}",
                        horizontal=True,
                        label_visibility="collapsed"
                    )
            st.markdown("---")

        submitted = st.form_submit_button("Next")
        if submitted:
            st.session_state.survey_responses.update(responses)
            st.session_state.page = 3
            st.rerun()


# ------------------------
# Page 3: Instructions
# ------------------------
def page2():
    st.title("Instructions")
    st.markdown("""
        ### Let’s imagine something wild together.
        Starting tomorrow, all humans can fly. How would that change cities, society, and daily life? That’s what we’re here to explore.
        - **Your Task:** Brainstorm ideas back and forth with an AI assistant for a limited number of turns.
        - **Goal:** After the brainstorming session concludes, you will be asked to write a short summary of your discussion.
        Click the button below to begin.
    """)
    if st.button("Start Brainstorming"):
        st.session_state.page = 4
        st.rerun()

# ------------------------
# Page 4: Chat Interface 
# ------------------------
def page3():
    st.title("Brainstorm with Your Teammate")

    # This system prompt contains the rules you provided.
    system_prompt = """You are brainstorming with the user like a creative teammate. Respond with vivid ideas, challenges, and twists. Never just ask questions—build on what the user says. You will have exactly 10 user turns. After the user's 10th message, do not wait for further input. Instead, say something like: 'That's a great idea: Looks like we’ve explored a lot of wild ideas together! I’ll go ahead and wrap this up with a summary story. Please press the next button to move on to the summary page' Then write a fun, creative summary that blends your ideas and the user’s ideas into a cohesive short story. At the end of the story, remind the user to click 'Next' to proceed to the summary page."""

    # Initialize chat history and turn counter
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = [{"role": "system", "content": system_prompt}]
        st.session_state.user_turns = 0

    # Display chat messages
    for msg in st.session_state.chat_history:
        if msg["role"] != "system":
            st.chat_message(msg["role"]).write(msg["content"])

    # Turn counting and input disabling logic
    if 'user_turns' not in st.session_state:
        st.session_state.user_turns = 0
    
    chat_limit_reached = st.session_state.user_turns >= 10
    
    if chat_limit_reached:
         st.info("Brainstorming session complete! Please review the final story and click 'Next' to continue.")

    # Get user input, disable if limit is reached
    user_input = st.chat_input("Your message...", disabled=chat_limit_reached)

    if user_input:
        # Increment turn counter and add user message to history
        st.session_state.user_turns += 1
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Call the API for a response
        with st.spinner("Your teammate is thinking..."):
            try:
                response = client.chat.completions.create(model="gpt-4", messages=st.session_state.chat_history)
                reply = response.choices[0].message.content
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"An error occurred with the API call: {e}")
        st.rerun()

    # Navigation to the next page
    if st.button("Next: Write Summary"):
        st.session_state.page = 5
        st.rerun()

# ------------------------
# Page 5: Summary
# ------------------------
def page4():
    st.title("Summary")
    st.text_area("Please summarize your discussion:", key="summary_text", height=300)
    if st.button("Submit Summary"):
        st.session_state.page = 6
        st.rerun()

# ------------------------
# Page 6: Post-Task Feedback
# ------------------------
def feedback_page():
    st.title("Post-Task Feedback")

    st.markdown("""
        <style>
            div.row-widget.stRadio > div {
                display: flex;
                flex-direction: row;
                justify-content: center;
            }
            div.row-widget.stRadio > div > label > div:nth-of-type(2) {
                display: none;
            }
            div.row-widget.stRadio > div > label {
                padding: 0 20px;
            }
        </style>
    """, unsafe_allow_html=True)


    matrix_questions = {
        "Feedback on the Writing Process": [
            "I was satisfied with the writing process",
            "I enjoyed the writing process",
            "I found it easy to complete the writing process",
            "I was able to express my creative goals during the writing process",
        ],
        "Feedback on the Final Outcome": [
            "I am satisfied with the quality of the final outcome",
            "I feel a sense of ownership of the final outcome",
            "I am proud of the final outcome",
            "I found the final outcome to be unique",
        ],
        "Accountability of Final Outcome": [
            "I'm willing to take the responsibility if my product is criticized for containing deceptive content.",
            "I'm willing to take the responsibility if my product is criticized for containing content that is highly similar to someone else's writing.",
            "I'm willing to take the responsibility if my product is criticized for containing content that invades someone else's privacy.",
            "I'm willing to take the responsibility if my product is criticized for exhibiting bias and discrimination.",
        ],
    }
    
    likert_options = ["Strongly Disagree", "Somewhat Disagree", "Neither Agree nor Disagree", "Somewhat Agree", "Strongly Agree"]
    
    with st.form("feedback_form"):
        responses = {}
        
        for section, questions in matrix_questions.items():
            st.subheader(section)
            
            header_cols = st.columns([3, 5])
            with header_cols[1]:
                sub_cols = st.columns(len(likert_options))
                for i, option in enumerate(likert_options):
                    with sub_cols[i]:
                        st.markdown(f'<p style="text-align: center; font-weight: bold;">{option}</p>', unsafe_allow_html=True)
            st.divider()

            for stmt in questions:
                row_cols = st.columns([3, 5])
                
                with row_cols[0]:
                    st.write(stmt)
                
                with row_cols[1]:
                    responses[stmt] = st.radio(
                        label=stmt, 
                        options=likert_options, 
                        key=f"fb_{stmt}",
                        horizontal=True,
                        label_visibility="collapsed"
                    )
            st.markdown("---")

        st.subheader("Post-Task Emotional State (SAM)")
        if os.path.exists("images/SAM Model.jpeg"):
            st.image("images/SAM Model.jpeg", caption="SAM Model", use_column_width=True)
        else:
            st.warning("SAM Model image not found.")
        
        responses['arousal_post'] = st.slider("Arousal after task (Calm ← → Excited)", 1, 9, 5)
        responses['valence_post'] = st.slider("Valence after task (Unpleasant ← → Pleasant)", 1, 9, 5)

        submitted = st.form_submit_button("Finish")
        if submitted:
            st.session_state.feedback_responses = responses
            save_chat_to_file()
            st.session_state.page = 7
            st.rerun()

# ------------------------
# Page 7: Acknowledgement
# ------------------------
def page5():
    st.title("Thank You!")
    st.markdown("You're all done! Your data has been saved. Please close this window.")
    st.balloons()
    restart_button()

# ------------------------
# Page 99: Admin Dashboard
# ------------------------
def admin_view():
    st.title("Admin Dashboard: All Submissions")
    os.makedirs(CHAT_LOGS_FOLDER, exist_ok=True)
    files = sorted([f for f in os.listdir(CHAT_LOGS_FOLDER) if f.endswith('.json')])
    
    if not files:
        st.warning("No submission files found.")
    else:
        for fname in files:
            with st.expander(f"View Submission: **{fname}**"):
                try:
                    with open(os.path.join(CHAT_LOGS_FOLDER, fname)) as f:
                        entry = json.load(f)
                    st.json(entry)
                except Exception as e:
                    st.error(f"Could not read file {fname}: {e}")
                    
    restart_button()

# ------------------------
# Main execution
# ------------------------
if __name__ == "__main__":
    main()