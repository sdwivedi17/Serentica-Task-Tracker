import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
from io import BytesIO
import os
from streamlit_autorefresh import st_autorefresh

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Serentica Renewables | Task Dashboard",
    layout="wide"
)
st_autorefresh(interval=30000, key="refresh")

os.chdir(os.path.dirname(os.path.abspath(__file__)))

DATA_FILE = "tasks.csv"

COLUMNS = [
    "id", "owner", "assignee", "department",
    "task", "start_date", "due_date",
    "status", "priority", "created_at"
]

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)

# =====================================================
# DATA FUNCTIONS
# =====================================================
def load_tasks():
    df = pd.read_csv(DATA_FILE)
    if not df.empty:
        df["start_date"] = pd.to_datetime(df["start_date"])
        df["due_date"] = pd.to_datetime(df["due_date"])
    return df

def save_tasks(df):
    df.to_csv(DATA_FILE, index=False)

# =====================================================
# LOGIN
# =====================================================
if "user" not in st.session_state:
    st.session_state.user = None

st.sidebar.title("🔐 Login")

if not st.session_state.user:
    user = st.sidebar.text_input("Your Name")
    if st.sidebar.button("Login") and user:
        st.session_state.user = user
        st.rerun()
else:
    st.sidebar.success(f"Logged in as {st.session_state.user}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

if not st.session_state.user:
    st.stop()

USER = st.session_state.user

# =====================================================
# NAVIGATION
# =====================================================
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "📝 My Tasks",
        "📊 Analytics",
        "🗓 Calendar View",
        "🧱 Gantt View"
    ]
)

# =====================================================
# LOAD DATA
# =====================================================
df = load_tasks()

if USER.lower() != "admin" and not df.empty:
    df = df[df["owner"] == USER]

# =====================================================
# HEADER
# =====================================================
st.markdown(
    f"""
    <h2>Hello, {USER} 👋</h2>
    <p style="color:grey;">Renewable operations task dashboard</p>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# =====================================================
# HOME
# =====================================================
if page == "🏠 Home":

    if df.empty:
        st.info("No tasks available.")
        st.stop()

    overdue = (
        (df["due_date"].dt.date < date.today()) &
        (df["status"] != "Completed")
    ).sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tasks", len(df))
    c2.metric("Completed", (df["status"] == "Completed").sum())
    c3.metric("In Progress", (df["status"] == "In Progress").sum())
    c4.metric("Overdue", overdue)

    st.markdown("### 📋 Task Buckets")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🟡 To Do")
        st.dataframe(df[df["status"] == "To Do"], use_container_width=True)

    with col2:
        st.subheader("🔵 In Progress")
        st.dataframe(df[df["status"] == "In Progress"], use_container_width=True)

    with col3:
        st.subheader("🟢 Completed")
        st.dataframe(df[df["status"] == "Completed"], use_container_width=True)

# =====================================================
# TASK CREATION
# =====================================================
elif page == "📝 My Tasks":

    st.subheader("➕ Create New Task")

    with st.form("add_task"):
        assignee = st.text_input("Assignee")
        department = st.selectbox(
            "Department",
            [
                "Solar", "Wind", "Trading",
                "Operations", "Finance",
                "Grid & Scheduling", "Asset Management"
            ]
        )
        task = st.text_area("Task Description")
        start_date = st.date_input("Start Date", date.today())
        due_date = st.date_input("Due Date", date.today() + timedelta(days=3))
        status = st.selectbox("Status", ["To Do", "In Progress", "Completed"])
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        submit = st.form_submit_button("Add Task")

    if submit:
        new_task = {
            "id": int(datetime.now().timestamp()),
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

    st.markdown("### 📋 Your Tasks")
    st.dataframe(df, use_container_width=True)

# =====================================================
# ANALYTICS
# =====================================================
elif page == "📊 Analytics":

    if df.empty:
        st.info("No data available.")
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(
            px.pie(df, names="status", title="Task Status Distribution"),
            use_container_width=True
        )

    with col2:
        st.plotly_chart(
            px.bar(
                df,
                x="department",
                title="Department-wise Workload",
                color="department"
            ),
            use_container_width=True
        )

# =====================================================
# CALENDAR VIEW
# =====================================================
elif page == "🗓 Calendar View":

    st.subheader("🗓 Task Calendar")

    if df.empty:
        st.info("No tasks available.")
        st.stop()

    df["due_day"] = df["due_date"].dt.date

    selected_day = st.date_input("Select Date", date.today())

    day_tasks = df[df["due_day"] == selected_day]

    if day_tasks.empty:
        st.info("No tasks scheduled for this day.")
    else:
        st.dataframe(day_tasks, use_container_width=True)

# =====================================================
# GANTT VIEW
# =====================================================
elif page == "🧱 Gantt View":

    st.subheader("🧱 Task Timeline (Gantt View)")

    if df.empty:
        st.info("No tasks available.")
        st.stop()

    gantt_df = df.copy()
    gantt_df["Task"] = gantt_df["task"]
    gantt_df["Start"] = gantt_df["start_date"]
    gantt_df["Finish"] = gantt_df["due_date"]

    fig = px.timeline(
        gantt_df,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="department",
        title="Project Timeline – Renewable Operations"
    )

    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# FOOTER
# =====================================================
st.caption(" Serentica Renewables • Live • Multi-user • Gantt • Calendar")
