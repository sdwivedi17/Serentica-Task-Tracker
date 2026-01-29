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
# DATA MODEL
# =====================================================
COLUMNS = [
    "task_id", "assignee", "department", "task",
    "start_date", "due_date", "status", "priority", "created_by"
]

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)

# =====================================================
# DATE HANDLING
# =====================================================
def load_tasks():
    df = pd.read_csv(DATA_FILE)
    df["task_id"] = df["task_id"].astype(str)
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce")
    return df

def save_tasks(df):
    df_save = df.copy()
    df_save["start_date"] = df_save["start_date"].apply(
        lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else ""
    )
    df_save["due_date"] = df_save["due_date"].apply(
        lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else ""
    )
    df_save.to_csv(DATA_FILE, index=False)

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
    st.title("Serentica Renewables")
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
h1.markdown(f"## Hello, {st.session_state.user}")
h2.markdown(f"🕒 **{now_ist}**")

if h3.button("Dark / Light"):
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
    "Overdue",
    (
        df["due_date"].notna()
        & (df["due_date"] < today_ts)
        & (df["status"] != "Completed")
    ).sum()
)

# =====================================================
# ADD TASK (ADMIN ONLY)
# =====================================================
if st.session_state.role == "Admin":
    with st.expander("➕ Add New Task"):
        assignee = st.text_input("Assignee")
        department = st.selectbox(
            "Department",
            ["Solar", "Wind", "Trading", "Operations", "Finance"]
        )
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
                "start_date": pd.to_datetime(start_date),
                "due_date": pd.to_datetime(due_date) if due_date else pd.NaT,
                "status": status,
                "priority": priority,
                "created_by": st.session_state.user
            }
            df = pd.concat([df, pd.DataFrame([new_task])], ignore_index=True)
            save_tasks(df)
            st.success("Task added successfully")
            st.rerun()

# =====================================================
# DELETE TASK (VISIBLE & SAFE)
# =====================================================
st.subheader("🗑 Delete Task")

if st.session_state.role == "Admin" and not df.empty:

    # Create safe labels
    df["delete_label"] = df.apply(
        lambda x: f"{x['task']} | {x['assignee']} | {x['department']}",
        axis=1
    )

    label_to_id = dict(zip(df["delete_label"], df["task_id"]))

    selected_label = st.selectbox(
        "Select task to delete",
        list(label_to_id.keys())
    )

    selected_id = label_to_id[selected_label]

    st.warning("This action is permanent.")

    if st.button("❌ Delete Selected Task"):
        df = df[df["task_id"] != selected_id]
        save_tasks(df)
        st.success("Task deleted successfully")
        st.rerun()

elif st.session_state.role == "Admin":
    st.info("No tasks available to delete")

# =====================================================
# TASK TABLE
# =====================================================
st.subheader("📋 Task List")

if not df.empty:
    display_df = df.copy()
    display_df["Start Date"] = display_df["start_date"].dt.strftime("%d-%b-%Y")
    display_df["Expected Completion"] = display_df["due_date"].dt.strftime("%d-%b-%Y")
    display_df["Expected Completion"] = display_df["Expected Completion"].fillna("TBD")

    st.dataframe(
        display_df[
            [
                "task", "assignee", "department",
                "Start Date", "Expected Completion",
                "status", "priority"
            ]
        ],
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
        color="department"
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No tasks with defined completion dates")
