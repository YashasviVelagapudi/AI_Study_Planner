import streamlit as st
from datetime import date
from groq import Groq

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="AI Study Planner",
    page_icon="📓",
    layout="wide"
)

# --------------------------------------------------
# Session State Initialization
# --------------------------------------------------
defaults = {
    "name": "",
    "subject": "",
    "exam_date": date.today(),
    "hours_per_day": 2,
    "syllabus": "",
    "ai_plan": None,
    "plan_active": False,
    "plan_locked": False,
    "plan_topics": [],
    "progress_data": []
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --------------------------------------------------
# Custom CSS
# --------------------------------------------------
st.markdown("""
<style>
.title {
    text-align: center;
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(90deg, #8e2de2, #4a00e0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
}
.subtitle {
    text-align: center;
    color: #777;
    font-size: 1.1rem;
    margin-bottom: 1.8rem;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown('<div class="title">📖 AI Study Planner</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Plan your studies smartly with AI-powered scheduling ✨</div>',
    unsafe_allow_html=True
)

# --------------------------------------------------
# Sidebar Navigation
# --------------------------------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to:", ["Home", "Progress Tracker", "About"])

# ==================================================
# HOME PAGE
# ==================================================
if page == "Home":
    st.subheader("📝 Enter Your Study Details")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("👤 Your Name", value=st.session_state.name)
        subject = st.text_input("📚 Subject Name", value=st.session_state.subject)

    with col2:
        exam_date = st.date_input(
            "📅 Exam Date",
            value=st.session_state.exam_date,
            min_value=date.today()
        )
        hours_per_day = st.slider(
            "⏱️ Study hours per day",
            1, 10,
            value=st.session_state.hours_per_day
        )

    syllabus = st.text_area(
        "🧾 Enter your syllabus/topics (comma-separated)",
        value=st.session_state.syllabus
    )

    # -------------------------------
    # Show existing plan
    # -------------------------------
    if st.session_state.ai_plan:
        st.write("### 📅 Your AI-Generated Study Plan")
        st.markdown(st.session_state.ai_plan)

        if st.session_state.plan_locked:
            st.info("🔒 Plan is locked because progress has started.")

            if st.button("🔄 Reset Plan"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.success("Plan reset. You can generate a new plan now.")
                st.rerun()

        else:
            st.warning("⚠️ Regenerating the plan will erase all progress.")

            if st.button("🔁 Regenerate Plan"):
                st.session_state.ai_plan = None
                st.session_state.plan_active = False
                st.session_state.plan_locked = False
                st.session_state.plan_topics = []
                st.session_state.progress_data = []
                st.success("Plan cleared. Generate a new one.")
                st.rerun()

    # -------------------------------
    # Generate plan (single-click)
    # -------------------------------
    MODEL_NAME = "llama-3.1-8b-instant"

    if st.button("✨ Generate Study Plan"):
        if st.session_state.ai_plan:
            st.warning("A plan already exists. Reset or regenerate it first.")
            st.stop()

        if not name or not subject or not syllabus:
            st.warning("😩 Please fill in all the details.")
            st.stop()

        days_left = (exam_date - date.today()).days
        if days_left <= 0:
            st.error("Please select a valid future exam date.")
            st.stop()

        # Save inputs
        st.session_state.name = name
        st.session_state.subject = subject
        st.session_state.exam_date = exam_date
        st.session_state.hours_per_day = hours_per_day
        st.session_state.syllabus = syllabus

        with st.spinner("🤖 Generating your personalized study plan..."):
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])

            prompt = f"""
You are an expert AI study planner.

Create a {days_left}-day study plan for a student named {name}.

Subject: {subject}
Topics: {syllabus}
Daily study time: {hours_per_day} hours
Guidelines: 
- Structured day-by-day 
- Practical and realistic 
- Simple language 
- Break topics into manageable chunks 
- Prioritize difficult topics earlier 
- Balance workload 
- Include short breaks 
- End with revision days 
- Add light motivation and a few emojis
"""

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800
            )

            st.session_state.ai_plan = response.choices[0].message.content

        st.session_state.plan_active = True
        st.session_state.plan_locked = False
        st.session_state.plan_topics = [
            t.strip() for t in syllabus.split(",") if t.strip()
        ]
        st.session_state.progress_data = []

        st.success("Study plan generated successfully!")
        st.rerun()


# ==================================================
# PROGRESS TRACKER
# ==================================================
elif page == "Progress Tracker":
    st.subheader("📊 Track Your Progress")

    if not st.session_state.plan_active:
        st.warning("⚠️ Generate a study plan first.")
        st.stop()

    allowed_topics = st.session_state.plan_topics

    with st.form("progress_form", clear_on_submit=True):
        topic = st.selectbox("📘 Select Topic", allowed_topics)
        progress = st.slider("✅ Completion (%)", 0, 100, 0)
        submitted = st.form_submit_button("💾 Save Progress")

    if submitted:
        st.session_state.plan_locked = True

        existing = next(
            (item for item in st.session_state.progress_data if item["Topic"] == topic),
            None
        )

        if existing:
            if progress < existing["Progress"]:
                st.warning("Progress cannot go backwards.")
            else:
                existing["Progress"] = progress
        else:
            st.session_state.progress_data.append({
                "Topic": topic,
                "Progress": progress
            })

    if st.session_state.progress_data:
        st.dataframe(st.session_state.progress_data)

        total = sum(item["Progress"] for item in st.session_state.progress_data)
        avg = total / len(allowed_topics)

        st.progress(int(avg))
        st.info(f"Overall completion: **{avg:.1f}%**")

        if avg >= 100:
            st.success("🎉 Study plan completed!")

            if st.button("🔄 Reset Plan"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.stop()

# ==================================================
# ABOUT PAGE
# ==================================================
else:
    st.subheader("ℹ️ About This App")
    st.write("""
**AI Study Planner** helps students create personalized study schedules
and track progress efficiently.

**Tech Stack**
- Streamlit
- Groq (LLaMA-based models)
- Python

**Design Highlights**
- Explicit lifecycle management
- State-safe progress tracking
- No silent regeneration
""")

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.markdown("""
---
<center>Made with ❤️ by Yashasvi | Powered by Streamlit & Groq 🤖</center>
""", unsafe_allow_html=True)
