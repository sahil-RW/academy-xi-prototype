import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import httpx
import json
import asyncio

# --------- Streamlit UI ---------
st.set_page_config(layout="wide")
st.title("📊 AcademyXi Workshop Feedback Trend Dashboard")

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

st.subheader(f"🧾 Trainer Benchmark Ratings: {len(filtered)}")
st.dataframe(filtered[["Date", "NPS", "Instructor Rating"]])

# --------- Chart ---------
st.subheader("📈 Trainer Benchmark Trend Over Time")
fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(filtered["Date"], filtered["NPS"], label="NPS", marker=".")
ax.plot(filtered["Date"], filtered["Instructor Rating"], label="Instructor Rating %", marker=".")
ax.plot(filtered["Date"], filtered["CSAT"], label="CSAT", marker=".")
ax.set_xlabel("Date")
ax.set_ylabel("Score")
ax.set_title(f"{program} - {instructor}")
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

 1.Program Effectiveness
Summarize how well the program delivered by the specified facilitator performed, based on historical participant feedback. Include:
- Quantitative indicators (NPS, Instructor Rating, CSAT)
- Comparison with country-level industry benchmarks:
    - NPS benchmark: 14  
    - Instructor rating benchmark: 82  
    - CSAT benchmark: 4.2 (assumed 5-point scale)
- Key strengths and any qualitative themes from participant comments.

 2. Comparative Analysis with Previous Sessions
Compare the current session’s performance with past sessions delivered by the same facilitator and/or for the same program using available feedback data. Highlight trends in delivery quality, engagement, or satisfaction over time.

Input Format:

- Client: {client}  
- Program: {program}  
- Instructor: {instructor}  
- Feedback Data:  
{data_text}

Output Format Example:


Program: Product Management Essentials (Nithin)

*   NPS of **69.3** places this session **well above the industry average** of 14, reflecting strong learner advocacy and engagement.  
*   Instructor Rating of **89.6** significantly **exceeds the national benchmark** of 82, suggesting high confidence in the facilitator’s delivery and expertise.  
*   A CSAT score of **5.0** (on a 5-point scale) indicates **maximum participant satisfaction**.  
*   Participant comments describe the session as “engaging” and the facilitator as “knowledgeable” and “well-prepared.”

Comparison with Previous Sessions:  
This session performed **consistently well compared to prior deliveries of the same program, maintaining high satisfaction and engagement. Compared to historical averages, this session saw a **+6.8% improvement** in overall participant satisfaction, indicating strong program stability and delivery quality over time.

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
