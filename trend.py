import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import httpx
import json
import asyncio

# --------- Streamlit UI ---------
st.set_page_config(layout="wide")
st.title("📊 Workshop Feedback Trend Dashboard")

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel("B2B-B2C.xlsx")
    df["Date"] = pd.to_datetime(df["Date"])
    return df.dropna(subset=["Date"])

df = load_data()

# Filters
client = st.selectbox("Select Client", df["Client"].dropna().unique())
program = st.selectbox("Select Program", df[df["Client"] == client]["Program"].dropna().unique())
instructor = st.selectbox("Select Instructor", df[df["Program"] == program]["Instructor"].dropna().unique())

# Filtered data
filtered = df[
    (df["Client"] == client) &
    (df["Program"] == program) &
    (df["Instructor"] == instructor)
].sort_values("Date")

st.subheader(f"🧾 Filtered Records: {len(filtered)}")
st.dataframe(filtered[["Date", "NPS", "Instructor Rating"]])

# --------- Chart ---------
st.subheader("📈 Trend Over Time")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(filtered["Date"], filtered["NPS"], label="NPS", marker="o")
ax.plot(filtered["Date"], filtered["Instructor Rating"], label="Instructor Rating %", marker="s")
ax.set_xlabel("Date")
ax.set_ylabel("Score")
ax.set_title(f"Trend Analysis - {program} ({instructor})")
ax.legend()
ax.grid(True)
plt.xticks(rotation=45)
st.pyplot(fig)

# --------- AI Insights ---------
st.subheader("🤖 AI Insights")

# Generate dynamic prompt
data_text = filtered[["Date", "NPS", "Instructor Rating", "Quote"]].to_string(index=False)
prompt = f"""
You are an AI analyst specializing in evaluating corporate training sessions. Based on the following inputs — **program name**, **facilitator name**, and **client** — generate a performance summary that includes:
1.  **Program Effectiveness**  
    Summarize how well the program delivered by the specified facilitator performed, based on historical participant feedback. Highlight key themes from qualitative comments and overall satisfaction scores (if available).
2.  **Comparative Analysis with Previous Sessions**  
    Compare the current session with previous sessions of the same program and/or facilitator, using available feedback data. Identify trends or changes in performance, such as improvements in delivery, engagement, or participant satisfaction.  
Client: {client}
Program: {program}
Instructor: {instructor}
Feedback Data:
{data_text}
 
Output Format Example:
 
Program Effectiveness: The "[Program Name]" conducted for [Client] by [Facilitator Name] received high satisfaction from participants, with consistent scores of X/10. Participants highlighted [e.g., facilitator expertise, engaging delivery, practical relevance] as key strengths.
 
Comparison with Previous Sessions: Compared to prior deliveries, this session maintained a high standard. Notably, feedback suggests [e.g., improved clarity in concepts, more interactive group work, stronger case study design]. Average satisfaction rose/fell by X% from the previous session.

Give the output in bullet points
"""

# Async function to fetch insights
async def get_ai_insights(prompt):
    url = "https://guideline.randomw.dev/api/chat/completions"
    # api_key = os.getenv("NEXT_PUBLIC_API_KEY")
    api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjgyM2RkNDBhLWVhYjYtNDYyNC1hZDAxLTk3NjAyMDM2ZGM1ZiJ9.LAjtg_MgeRu4m92IV_gYGoAZVwec4xYdMD7z6aLQx_s"
    knowledge_base_id = "71c70e76-a0e1-43d8-8422-97c9efaf4cf1"

    payload = {
        "model": "chatgpt-4o-latest",
        "messages": [{"role": "user", "content": prompt}],
        "files": [{"type": "collection", "id": knowledge_base_id}]
    }

    timeout = httpx.Timeout(30.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
        response.raise_for_status()
        result_data = response.json()
        content = result_data['choices'][0]['message']['content']
        cleaned = content.strip('```json').strip('```').strip()
        return cleaned
    except Exception as e:
        return f"❌ Error generating insights: {e}"

# Button to generate insights
if st.button("🔍 Generate AI Insights"):
    with st.spinner("Generating insights..."):
        ai_result = asyncio.run(get_ai_insights(prompt))
        # if ai-result contains [1] then remove
        if ai_result.startswith("[1]"):
            ai_result = ai_result[3:].strip()
        st.markdown(ai_result)
