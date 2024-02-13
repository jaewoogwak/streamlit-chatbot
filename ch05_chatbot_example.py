import os
import pandas as pd
import numpy as np
from numpy import dot
from numpy.linalg import norm
import ast
import openai
import streamlit as st
from streamlit_chat import message

client = openai.OpenAI(
    api_key='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')


def get_embedding(text):
    res = client.embeddings.create(
        input=text,
        model='text-embedding-ada-002'
    )

    return res.data[0].embedding


folder_path = './data'
file_name = 'embedding.csv'
file_path = os.path.join(folder_path, file_name)

if os.path.isfile(file_path):
    print(f"File {file_name} exists")
    df = pd.read_csv(file_path)
    df['embedding'] = df['embedding'].apply(ast.literal_eval)

else:
    txt_files = [file for file in os.listdir(
        folder_path) if file.endswith('.txt')]
    data = []

    for file in txt_files:
        file_path = os.path.join(folder_path, file)
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            data.append(text)

    df = pd.DataFrame(data, columns=['text'])

    df['embedding'] = df.apply(lambda row: get_embedding(row['text']), axis=1)

    df.to_csv(file_path, index=False, encoding='utf-8-sig')


def cos_sim(A, B):
    return dot(A, B)/(norm(A)*norm(B))


def return_answer_candidate(df, query):
    query_embedding = get_embedding(query)

    df['similarity'] = df['embedding'].apply(
        lambda x: cos_sim(np.array(x), np.array(query_embedding)))

    top_three_doc = df.sort_values(by='similarity', ascending=False).head(3)

    return top_three_doc


def create_prompt(df, query):
    result = return_answer_candidate(df, query)
    system_role = f"""You are an artificial intelligence language model named "야옹이" that specializes in summarizing \ and answering documents about Seoul's youth policy, developed by 유원준 and 안상준. You need to take a given document and return a very detailed summary of the document in the query language.
    Here are the document:
        doc 1: """ + str(result.iloc[0]['text']) + """
        doc 2: """ + str(result.iloc[1]['text']) + """
        doc 3: """ + str(result.iloc[2]['text']) + """
    You must return in Korean. Return a accurate answer based on the given document.
    """

    user_content = f"""User question: "{str(query)}". """

    messages = [
        {"role": "system", "content": system_role},
        {"role": "user", "content": user_content}
    ]

    return messages


def generate_response(messages):
    result = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.4,
        max_tokens=500
    )

    return result.choices[0].message.content


st.image('images/ask_me_chatbot.png')

if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'past' not in st.session_state:
    st.session_state['past'] = []

with st.form('form', clear_on_submit=True):
    user_input = st.text_input('정책을 물어보세요!', '', key='input')
    submitted = st.form_submit_button('Send')

if submitted and user_input:
    prompt = create_prompt(df, user_input)
    chatbot_response = generate_response(prompt)
    st.session_state['past'].append(user_input)
    st.session_state['generated'].append(chatbot_response)

if st.session_state['generated']:
    for i in reversed(range(len(st.session_state['generated']))):
        message(st.session_state['past'][i],
                is_user=True, key=str(i) + '_user')
        message(st.session_state['generated'][i], key=str(i))
