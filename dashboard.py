import streamlit as st
from core import rewrite_email

st.set_page_config(page_title="Email Rewriter", page_icon="✉️")
st.title("✉️ Email Rewriter")

tone = st.selectbox("Tone", ["professional", "friendly", "short", "firm"])
email = st.text_area("Paste your email", height=200)

if st.button("Rewrite"):
    with st.spinner("Rewriting..."):
        result = rewrite_email(email, tone)
    st.subheader("Result")
    st.text_area("Rewritten email (copy from here)", result, height=200)