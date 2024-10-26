import json
import os
from collections import defaultdict
import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title='Personalized Coversation Evaluation System', page_icon=':smiley:', layout='wide')

# Load configuration from config.json
with open('config.json', 'r') as f:
    config = json.load(f)

MODEL_LIST = config["MODEL_LIST"]
LABELER_LIST = config["LABELER_LIST"]
DATA_PATH = config["DATA_PATH"]

# Initialize MODEL_LIST in session_state if not already set
if "MODEL_LIST" not in st.session_state:
    random.shuffle(MODEL_LIST)
    st.session_state.MODEL_LIST = MODEL_LIST
else:
    MODEL_LIST = st.session_state.MODEL_LIST

SCORE_ITEMS = ["consistency", "engagingness", "humanness", "memorability"]

# Initialize data_store in session_state if not already set
if "data_store" not in st.session_state:
    st.session_state.data_store = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
        "consistency": None,
        "engagingness": None,
        "humanness": None,
        "memorability": None
    })))

data_store = st.session_state.data_store

def load_data(data_path):
    data = []
    with open(data_path, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def convert_data_to_df(data):
    df = pd.DataFrame(data)
    return df

def display_session_dialogue(session):
    with st.container(height=500):
        for turn_idx, turn in enumerate(session):
            if turn_idx % 2 == 0:
                human_message = st.chat_message('human')
                human_message.write(turn['utterance'])
            else:
                assistant_message = st.chat_message('assistant')
                assistant_message.write(turn['utterance'])

def display_history_dialogue(history):
    session1_tab, session2_tab, session3_tab = st.tabs(['Session 1', 'Session 2', 'Session 3'])
    with session1_tab:
        display_session_dialogue(history[0])
    with session2_tab:
        display_session_dialogue(history[1])
    with session3_tab:
        display_session_dialogue(history[2])

def show_row_info(row, doc_id, user_id):
    st.write('History Conversation')
    history_dialogues = row['History']
    col1, col2 = st.columns(2)
    with col1:
        display_history_dialogue(history_dialogues)
    with col2:
        st.write('Current Conversation')
        current_dialogues = row['Current']
        display_session_dialogue(current_dialogues)
    st.write('Current Conversation')
    model_tabs = st.tabs([f"Model {i+1}" for i in range(len(MODEL_LIST))])

    for idx, model in enumerate(MODEL_LIST):
        with model_tabs[idx]:
            st.write(f"Model {idx+1}")
            st.write('Response')
            message = st.chat_message('assistant')
            message.write(row[model])

            id = f"{model}_{doc_id}_{user_id}"

            # Ensure doc_id is a string
            doc_id_str = str(doc_id)

            # Get or initialize scores
            if user_id not in data_store:
                data_store[user_id] = defaultdict(lambda: defaultdict(lambda: {
                    "consistency": None,
                    "engagingness": None,
                    "humanness": None,
                    "memorability": None
                }))
            if doc_id_str not in data_store[user_id]:
                data_store[user_id][doc_id_str] = defaultdict(lambda: {
                    "consistency": None,
                    "engagingness": None,
                    "humanness": None,
                    "memorability": None
                })
            if model not in data_store[user_id][doc_id_str]:
                data_store[user_id][doc_id_str][model] = {
                    "consistency": None,
                    "engagingness": None,
                    "humanness": None,
                    "memorability": None
                }

            scores = data_store[user_id][doc_id_str][model]

            # Initialize feedback values in session state if not already set
            if f"consistency_{id}" not in st.session_state:
                st.session_state[f"consistency_{id}"] = scores["consistency"]
            if f"engagingness_{id}" not in st.session_state:
                st.session_state[f"engagingness_{id}"] = scores["engagingness"]
            if f"humanness_{id}" not in st.session_state:
                st.session_state[f"humanness_{id}"] = scores["humanness"]
            if f"memorability_{id}" not in st.session_state:
                st.session_state[f"memorability_{id}"] = scores["memorability"]

            st.text("Consistency(행동, 결과의 일관성)")
            consistency_selected = st.feedback("stars", key=f"consistency_{id}")
            st.text("Engagingness(흥미로움)")
            engagingness_selected = st.feedback("stars", key=f"engagingness_{id}")
            st.text("Humanness(인간다움)")
            humanness_selected = st.feedback("stars", key=f"humanness_{id}")
            st.text("Memorability(기억력)")
            memorability_selected = st.feedback("stars", key=f"memorability_{id}")
            score_map = {
                "consistency": consistency_selected,
                "engagingness": engagingness_selected,
                "humanness": humanness_selected,
                "memorability": memorability_selected
            }

            # Save scores to data_store
            data_store[user_id][doc_id_str][model] = score_map
            st.write(score_map)

def prepare_data_for_annotation(data_path = DATA_PATH):
    source_data_df = convert_data_to_df(load_data(data_path))
    return source_data_df

data_df = prepare_data_for_annotation(DATA_PATH)

def save_defaultdict_json(data: defaultdict, file_path: str) -> None:
    with open(file_path, "w") as f:
        json.dump({k: dict(v) for k, v in data.items()}, f, ensure_ascii=False, indent=4)

def load_defaultdict_json(file_path: str) -> defaultdict:
    with open(file_path, "r") as f:
        loaded_data = json.load(f)
    return defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
        "consistency": None,
        "engagingness": None,
        "humanness": None,
        "memorability": None
    })), loaded_data)

def save_data_store_to_json(file_path):
    save_defaultdict_json(st.session_state.data_store, file_path)

def load_data_store_from_json(file_path):
    global data_store
    if not os.path.exists(file_path):
        # Initialize an empty data_store if the file does not exist
        print("Data store file does not exist. Initializing an empty data store.")
        data_store = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
            "consistency": None,
            "engagingness": None,
            "humanness": None,
            "memorability": None
        })))
        save_data_store_to_json(file_path)
    else:
        data_store = load_defaultdict_json(file_path)
    st.session_state.data_store = data_store

def main():
    load_data_store_from_json('data_store.json')
    st.title('Personalized Coversation Evaluation System')
    st.sidebar.title('Settings')
    user = st.sidebar.selectbox('Select User', LABELER_LIST)

    if "row_id" not in st.session_state:
        st.session_state.row_id = 0

    row_id = st.sidebar.selectbox('Select Row', data_df.index, index=st.session_state.row_id)
    st.session_state.row_id = row_id

    show_row_info(data_df.iloc[row_id], f"doc_{row_id}", user)

    def save_and_previous():
        save_data_store_to_json('data_store.json')
        st.session_state.row_id = (st.session_state.row_id - 1) % len(data_df)

    def save_and_next():
        save_data_store_to_json('data_store.json')
        st.session_state.row_id = (st.session_state.row_id + 1) % len(data_df)

    def export_data_store():
        save_data_store_to_json('data_store.json')
        with open('data_store.json', 'r') as f:
            st.download_button('Download data_store.json', f, file_name='data_store.json')

    st.button('Save & Previous Conversation', on_click=save_and_previous)
    st.button('Save & Next Conversation', on_click=save_and_next)
    export_data_store()

if __name__ == '__main__':
    main()
