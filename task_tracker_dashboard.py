import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import pytz
import os

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Serentica Renewables | Task Tracker",
    layout="wide"
)

DATA_FILE = "tasks.csv"
IST = pytz.timezone("Asia/Kolkata")

# =====================================================
# DEPARTMENT LOGOS (UI ENHANCEMENT)
# =====================================================
DEPARTMENT_LOGOS = {
    "Solar": "☀️ Solar",
    "Wind": "🌬️ Wind",
    "Trading": "💹 Trading",
    "Market & Operations": "⚙️ Market & Operations",
    "Finance": "💰 Finance"
}

LOGO_TO_DEPT = {v: k for k, v in DEPARTMENT_LOGOS.items()}

# =====================================================
# DATA MODEL
# =====================================================
COLUMNS = [
    "task_id", "assignee", "department", "task",
    "start_date", "due_date", "status", "priority", "created_by"
]

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)

def normalize_dates(df):
    for col in ["start_date", "due_date"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def load_tasks():
    df = pd.read_csv(DATA_FILE, dtype=str)
    df = normalize_dates(df)
    df["task_id"] = df["task_id"].astype(str)
    return df

def save_tasks(df):
    df = normalize_dates(df)
    df.to_csv(DATA_FILE, index=False)

# =====================================================
# SESSION STATE
# =====================================================
if "user" not in st.session_state:
    st.session_state.user = None

if "role" not in st.session_state:
    st.session_state.role = None

if "theme" not in st.session_state:
    st.session_state.theme = "light"

# =====================================================
# THEME
# =====================================================
if st.session_state.theme == "dark":
    st.markdown(
        "<style>.stApp { background-color:#0E1117; color:white; }</style>",
        unsafe_allow_html=True
    )

# =====================================================
# LOGIN
# =====================================================
if st.session_state.user is None:
    st.title("⚡ Serentica Renewables")
    st.subheader("Task Management Portal")

    username = st.text_input("Username")
    role = st.selectbox("Role", ["User", "Admin"])

    if st.button("Login") and username.strip():
        st.session_state.user = username.strip()
        st.session_state.role = role
        st.rerun()

    st.stop()

# =====================================================
# HEADER
# =====================================================
now_ist = datetime.now(IST).strftime("%d %b %Y | %H:%M:%S IST")

h1, h2, h3 = st.columns([5, 2, 1])
h1.markdown(f"## 👋 Hello, {st.session_state.user}")
h2.markdown(f"🕒 **{now_ist}**")

if h3.button("🌙 / ☀️"):
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
    st.rerun()

st.markdown("---")

# =====================================================
# LOAD DATA
# =====================================================
df = load_tasks()

if st.session_state.role == "User":
    df = df[df["assignee"] == st.session_state.user]

# =====================================================
# KPI METRICS
# =====================================================
today_ts = pd.Timestamp(date.today())

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Tasks", len(df))
k2.metric("Completed", (df["status"] == "Completed").sum())
k3.metric("TBD", df["due_date"].isna().sum())
k4.metric(
    (
        df["due_date"].notna() &
        (df["due_date"] < today_ts) &
        (df["status"] != "Completed")
    ).sum(),
    label="Overdue"
)

# =====================================================
# ADD TASK (ADMIN ONLY)
# =====================================================
if st.session_state.role == "Admin":
    with st.expander("➕ Add New Task"):
        assignee = st.text_input("Assignee")

        dept_logo = st.selectbox(
            "Department",
            list(DEPARTMENT_LOGOS.values())
        )
        department = LOGO_TO_DEPT[dept_logo]

        task = st.text_area("Task Description")
        start_date = st.date_input("Start Date", date.today())

        tbd = st.checkbox("Expected Completion Date = TBD")
        due_date = None if tbd else st.date_input(
            "Expected Completion Date",
            date.today() + timedelta(days=5)
        )

        status = st.selectbox("Status", ["To Do", "In Progress", "Completed"])
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])

        if st.button("Add Task"):
            new_task = {
                "task_id": str(int(datetime.now().timestamp())),
                "assignee": assignee,
                "department": department,
                "task": task,
                "start_date": start_date,
                "due_date": due_date,
                "status": status,
                "priority": priority,
                "created_by": st.session_state.user
            }
            df = pd.concat([df, pd.DataFrame([new_task])], ignore_index=True)
            save_tasks(df)
            st.success("Task added successfully")
            st.rerun()

# =====================================================
# TASK LIST
# =====================================================
st.subheader("📝 Task List")

if not df.empty:
    df["Department"] = df["department"].map(DEPARTMENT_LOGOS)
    df["Expected Completion"] = df["due_date"].apply(
        lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else "TBD"
    )

    st.dataframe(
        df.drop(columns=["department"]),
        use_container_width=True
    )

else:
    st.info("No tasks available")

# =====================================================
# GANTT VIEW
# =====================================================
st.subheader("🧱 Gantt Chart")

gantt_df = df[df["due_date"].notna()]

if not gantt_df.empty:
    fig = px.timeline(
        gantt_df,
        x_start="start_date",
        x_end="due_date",
        y="task",
        color="Department"
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No tasks with defined completion dates")
