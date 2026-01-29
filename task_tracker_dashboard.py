import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import os
import base64

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Serentica Renewables | Task Manager",
    layout="wide",
    initial_sidebar_state="collapsed"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

DATA_FILE = "tasks.csv"
BG_IMAGE_PATH = "assets/renewable_bg.jpg"

# =====================================================
# BACKGROUND IMAGE (BASE64)
# =====================================================
def get_base64_bg(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

BG_BASE64 = get_base64_bg(BG_IMAGE_PATH)

# =====================================================
# DATA SETUP (SAFE + NORMALIZED)
# =====================================================
COLUMNS = [
    "task_id", "owner", "assignee", "department",
    "task", "start_date", "due_date",
    "status", "priority", "created_at"
]

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)

def load_tasks():
    df = pd.read_csv(DATA_FILE)

    # Ensure columns
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = None

    #  CRITICAL FIX: normalize task_id
    df["task_id"] = df["task_id"].astype(str)

    # Safe date parsing
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce")

    df["start_date"] = df["start_date"].fillna(pd.Timestamp.today())
    df["due_date"] = df["due_date"].fillna(df["start_date"] + pd.Timedelta(days=3))

    return df

def save_tasks(df):
    df.to_csv(DATA_FILE, index=False)

# =====================================================
# SESSION STATE
# =====================================================
if "user" not in st.session_state:
    st.session_state.user = None

if "settings" not in st.session_state:
    st.session_state.settings = {
        "show_completed": True,
        "enable_calendar": True,
        "enable_gantt": True,
        "default_status": "To Do",
        "default_priority": "Medium"
    }

# =====================================================
# LOGIN SCREEN
# =====================================================
if st.session_state.user is None:

    if BG_BASE64:
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpg;base64,{BG_BASE64}");
                background-size: cover;
                background-position: center;
            }}
            .login-box {{
                background: rgba(255,255,255,0.94);
                padding: 2.5rem;
                border-radius: 16px;
                width: 360px;
                margin: auto;
                margin-top: 15vh;
                box-shadow: 0px 10px 30px rgba(0,0,0,0.25);
                text-align: center;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown(" Serentica Renewables")
    st.markdown(" Task Manager Portal")

    username = st.text_input("👤 Enter your name")
    if st.button("🔐 Login") and username.strip():
        st.session_state.user = username.strip()
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# =====================================================
# USER LOGGED IN
# =====================================================
USER = st.session_state.user
df = load_tasks()

if USER.lower() != "admin":
    df = df[df["owner"] == USER]

if not st.session_state.settings["show_completed"]:
    df = df[df["status"] != "Completed"]

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title(" Serentica")
st.sidebar.success(f"Logged in as {USER}")

pages = ["🏠 Overview", "📝 Task Board", "👤 Assignee View", "📊 Analytics", "⚙️ Settings"]

if st.session_state.settings["enable_calendar"]:
    pages.insert(3, "🗓 Calendar")

if st.session_state.settings["enable_gantt"]:
    pages.insert(4, "🧱 Gantt")

page = st.sidebar.radio("Navigation", pages)

if st.sidebar.button("🚪 Logout"):
    st.session_state.user = None
    st.rerun()

# =====================================================
# HEADER
# =====================================================
st.markdown(
    f"""
    <h2>Hello, {USER} 👋</h2>
    <p style="color:grey;">Task Tracker</p>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# =====================================================
# TASK BOARD (ADD + DELETE FIXED)
# =====================================================
if page == "📝 Task Board":

    st.subheader("➕ Add Task")

    with st.form("add_task"):
        assignee = st.text_input("Assignee")
        department = st.selectbox(
            "Department",
            ["Solar", "Wind", "Trading", "Operations", "Finance", "Grid & Scheduling", "Asset Management"]
        )
        task = st.text_area("Task Description")
        start_date = st.date_input("Start Date", date.today())
        due_date = st.date_input("Expected Completion Date", date.today() + timedelta(days=5))
        status = st.selectbox("Status", ["To Do", "In Progress", "Completed"])
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        submit = st.form_submit_button("➕ Add Task")

    if submit:
        new_task = {
            "task_id": str(int(datetime.now().timestamp())),
            "owner": USER,
            "assignee": assignee,
            "department": department,
            "task": task,
            "start_date": start_date,
            "due_date": due_date,
            "status": status,
            "priority": priority,
            "created_at": datetime.now().isoformat()
        }
        df = pd.concat([df, pd.DataFrame([new_task])], ignore_index=True)
        save_tasks(df)
        st.success("Task added successfully")
        st.rerun()

    st.markdown("### 🗑 Delete Task (Safe)")

    if not df.empty:
        delete_id = st.selectbox(
            "Select Task ID",
            df["task_id"].tolist()
        )

        task_preview = df[df["task_id"] == delete_id].iloc[0]
        st.warning(f"Task: **{task_preview['task']}** | Assignee: **{task_preview['assignee']}**")

        confirm = st.checkbox("I confirm I want to delete this task")

        if st.button("❌ Permanently Delete") and confirm:
            df = df[df["task_id"] != delete_id]
            save_tasks(df)
            st.success("Task deleted successfully")
            st.rerun()

    st.markdown("### 📋 Current Tasks")
    st.dataframe(df, use_container_width=True)

# =====================================================
# OTHER PAGES (UNCHANGED)
# =====================================================
elif page == "👤 Assignee View":
    assignee = st.selectbox("Select Assignee", sorted(df["assignee"].dropna().unique()))
    st.dataframe(df[df["assignee"] == assignee], use_container_width=True)

elif page == "🗓 Calendar":
    selected = st.date_input("Select Date", date.today())
    st.dataframe(df[df["due_date"].dt.date == selected], use_container_width=True)

elif page == "🧱 Gantt":
    fig = px.timeline(df, x_start="start_date", x_end="due_date", y="task", color="assignee")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

elif page == "📊 Analytics":
    st.plotly_chart(px.pie(df, names="status"), use_container_width=True)
    st.plotly_chart(px.bar(df, x="department", color="department"), use_container_width=True)

elif page == "⚙️ Settings":
    st.session_state.settings["show_completed"] = st.toggle("Show Completed Tasks", st.session_state.settings["show_completed"])
    st.session_state.settings["enable_calendar"] = st.toggle("Enable Calendar View", st.session_state.settings["enable_calendar"])
    st.session_state.settings["enable_gantt"] = st.toggle("Enable Gantt View", st.session_state.settings["enable_gantt"])
    st.success("Settings applied")

# =====================================================
# FOOTER
# =====================================================
st.caption(" Serentica Renewables • Market & Operations • Task Manager")

