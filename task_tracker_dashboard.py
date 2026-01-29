import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
from io import BytesIO
import os

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Serentica Renewables | PM Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

DATA_FILE = "tasks.csv"
BG_IMAGE = "assets/IMG_4203.jpeg"

# =====================================================
# DATA SETUP
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
    if not df.empty:
        df["start_date"] = pd.to_datetime(df["start_date"])
        df["due_date"] = pd.to_datetime(df["due_date"])
    return df

def save_tasks(df):
    df.to_csv(DATA_FILE, index=False)

# =====================================================
# SESSION STATE DEFAULTS
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
# LOGIN SCREEN (CENTERED WITH BACKGROUND)
# =====================================================
if st.session_state.user is None:

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{BG_IMAGE}");
            background-size: cover;
            background-position: center;
        }}
        .login-card {{
            background: rgba(255,255,255,0.92);
            padding: 2.5rem;
            border-radius: 16px;
            width: 380px;
            margin: auto;
            margin-top: 15vh;
            box-shadow: 0px 10px 30px rgba(0,0,0,0.25);
            text-align: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown("## ⚡ Serentica Renewables")
    st.markdown("### Project Management Portal")

    username = st.text_input("👤 Enter your name")
    login = st.button("🔐 Login")

    if login and username.strip():
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
# SIDEBAR NAVIGATION
# =====================================================
st.sidebar.title("⚡ Serentica")
st.sidebar.success(f"Logged in as {USER}")

page_list = ["🏠 Overview", "📝 Task Board", "👤 Assignee View", "📊 Analytics", "⚙️ Settings"]

if st.session_state.settings["enable_calendar"]:
    page_list.insert(3, "🗓 Calendar")

if st.session_state.settings["enable_gantt"]:
    page_list.insert(4, "🧱 Gantt")

page = st.sidebar.radio("Navigation", page_list)

if st.sidebar.button("🚪 Logout"):
    st.session_state.user = None
    st.rerun()

# =====================================================
# HEADER
# =====================================================
st.markdown(
    f"""
    <h2>Hello, {USER} 👋</h2>
    <p style="color:grey;">Renewable energy project management dashboard</p>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# =====================================================
# OVERVIEW
# =====================================================
if page == "🏠 Overview":

    if df.empty:
        st.info("No tasks available.")
        st.stop()

    overdue = ((df["due_date"].dt.date < date.today()) & (df["status"] != "Completed")).sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tasks", len(df))
    c2.metric("Completed", (df["status"] == "Completed").sum())
    c3.metric("In Progress", (df["status"] == "In Progress").sum())
    c4.metric("Overdue", overdue)

    st.markdown("### 📌 Task Buckets")

    for status in ["To Do", "In Progress", "Completed"]:
        st.subheader(status)
        st.dataframe(df[df["status"] == status], use_container_width=True)

# =====================================================
# TASK BOARD
# =====================================================
elif page == "📝 Task Board":

    with st.form("add_task"):
        assignee = st.text_input("Assignee")
        department = st.selectbox(
            "Department",
            ["Solar", "Wind", "Trading", "Operations", "Finance", "Grid & Scheduling", "Asset Management"]
        )
        task = st.text_area("Task Description")
        start_date = st.date_input("Start Date", date.today())
        due_date = st.date_input("Expected Completion Date", date.today() + timedelta(days=5))
        status = st.selectbox("Status", ["To Do", "In Progress", "Completed"],
                              index=["To Do", "In Progress", "Completed"].index(
                                  st.session_state.settings["default_status"]))
        priority = st.selectbox("Priority", ["Low", "Medium", "High"],
                                index=["Low", "Medium", "High"].index(
                                    st.session_state.settings["default_priority"]))
        submit = st.form_submit_button("➕ Add Task")

    if submit:
        new_task = {
            "task_id": int(datetime.now().timestamp()),
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

    st.dataframe(df, use_container_width=True)

# =====================================================
# ASSIGNEE VIEW
# =====================================================
elif page == "👤 Assignee View":
    assignee = st.selectbox("Select Assignee", sorted(df["assignee"].unique()))
    st.dataframe(df[df["assignee"] == assignee], use_container_width=True)

# =====================================================
# CALENDAR
# =====================================================
elif page == "🗓 Calendar":
    selected = st.date_input("Select Date", date.today())
    st.dataframe(df[df["due_date"].dt.date == selected], use_container_width=True)

# =====================================================
# GANTT
# =====================================================
elif page == "🧱 Gantt":
    fig = px.timeline(
        df,
        x_start="start_date",
        x_end="due_date",
        y="task",
        color="assignee",
        title="Renewable Operations – Task Timeline"
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# ANALYTICS
# =====================================================
elif page == "📊 Analytics":
    st.plotly_chart(px.pie(df, names="status"), use_container_width=True)
    st.plotly_chart(px.bar(df, x="department", color="department"), use_container_width=True)

# =====================================================
# SETTINGS
# =====================================================
elif page == "⚙️ Settings":

    st.subheader("⚙️ Dashboard Settings")

    st.session_state.settings["show_completed"] = st.toggle(
        "Show Completed Tasks", st.session_state.settings["show_completed"])

    st.session_state.settings["enable_calendar"] = st.toggle(
        "Enable Calendar View", st.session_state.settings["enable_calendar"])

    st.session_state.settings["enable_gantt"] = st.toggle(
        "Enable Gantt View", st.session_state.settings["enable_gantt"])

    st.session_state.settings["default_status"] = st.selectbox(
        "Default Task Status", ["To Do", "In Progress", "Completed"],
        index=["To Do", "In Progress", "Completed"].index(
            st.session_state.settings["default_status"]))

    st.session_state.settings["default_priority"] = st.selectbox(
        "Default Task Priority", ["Low", "Medium", "High"],
        index=["Low", "Medium", "High"].index(
            st.session_state.settings["default_priority"]))

    st.success("Settings apply immediately")

# =====================================================
# FOOTER
# =====================================================
st.caption("⚡ Serentica Renewables • Modern PM Dashboard • Secure Login • Live Views")
