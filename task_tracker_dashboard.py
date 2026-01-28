import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from io import BytesIO
import os
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ================= CONFIG =================
st.set_page_config(page_title="Serentica Renewables | Task Tracker", layout="wide")
st_autorefresh(interval=30000, key="refresh")

ATTACH_DIR = "attachments"
os.makedirs(ATTACH_DIR, exist_ok=True)

# ================= LOGIN =================
if "user" not in st.session_state:
    st.session_state.user = None

st.sidebar.title("🔐 Login")
if not st.session_state.user:
    username = st.sidebar.text_input("Enter your name")
    if st.sidebar.button("Login") and username:
        st.session_state.user = username
        st.rerun()
else:
    st.sidebar.success(f"Logged in as {st.session_state.user}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

if not st.session_state.user:
    st.stop()

USER = st.session_state.user

# ================= DATABASE =================
conn = sqlite3.connect("task_tracker.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner TEXT,
    assignee TEXT,
    department TEXT,
    task TEXT,
    due_date DATE,
    status TEXT,
    priority TEXT,
    attachment TEXT,
    remarks TEXT,
    created_at TEXT
)
""")
conn.commit()

# ================= FUNCTIONS =================
def load_tasks():
    return pd.read_sql("SELECT * FROM tasks", conn)

def add_task(row):
    cursor.execute("""
        INSERT INTO tasks VALUES (NULL,?,?,?,?,?,?,?,?,?,?)
    """, row)
    conn.commit()

def update_status(tid, status):
    cursor.execute("UPDATE tasks SET status=? WHERE id=?", (status, tid))
    conn.commit()

# ================= ADD TASK =================
st.sidebar.header("➕ Add Task")

with st.sidebar.form("add_task"):
    assignee = st.text_input("Assignee Name")
    department = st.selectbox("Department", ["Solar", "Wind", "Grid", "Trading", "Operations"])
    task = st.text_area("Task Description")
    due = st.date_input("Expected Completion Date")
    status = st.selectbox("Status", ["Pending", "In Progress", "Completed"])
    priority = st.selectbox("Priority", ["Low", "Medium", "High"])
    file = st.file_uploader("Attach File")
    remarks = st.text_input("Remarks")
    submit = st.form_submit_button("Add Task")

if submit:
    filename = None
    if file:
        filename = f"{datetime.now().timestamp()}_{file.name}"
        with open(os.path.join(ATTACH_DIR, filename), "wb") as f:
            f.write(file.getbuffer())

    add_task((
        USER, assignee, department, task, due,
        status, priority, filename, remarks,
        datetime.now().isoformat()
    ))
    st.sidebar.success("Task Added")
    st.rerun()

# ================= DASHBOARD =================
st.title("⚡ Serentica Renewables – Live Task Tracker")

df = load_tasks()
if USER.lower() != "admin":
    df = df[df["owner"] == USER]

df["due_date"] = pd.to_datetime(df["due_date"])
df["overdue"] = (df["due_date"].dt.date < date.today()) & (df["status"] != "Completed")

# ================= ANALYTICS =================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Tasks", len(df))
c2.metric("Completed", (df["status"] == "Completed").sum())
c3.metric("Pending", (df["status"] == "Pending").sum())
c4.metric("Overdue", df["overdue"].sum())

col1, col2 = st.columns(2)
col1.plotly_chart(px.pie(df, names="status", title="Status Distribution"), use_container_width=True)
col2.plotly_chart(px.bar(df, x="priority", title="Tasks by Priority"), use_container_width=True)

# ================= TASK TABLE =================
st.subheader("📋 Tasks")
st.dataframe(df.drop(columns=["attachment"]), use_container_width=True)

# ================= UPDATE STATUS =================
st.subheader("🔄 Update Task Status")
task_id = st.selectbox("Task ID", df["id"].tolist())
new_status = st.selectbox("New Status", ["Pending", "In Progress", "Completed"])
if st.button("Update"):
    update_status(task_id, new_status)
    st.success("Updated")
    st.rerun()

# ================= DOWNLOAD =================
buffer = BytesIO()
df.to_excel(buffer, index=False, engine="openpyxl")
buffer.seek(0)

st.download_button(
    "⬇ Download Excel",
    buffer,
    file_name="Serentica_Task_Tracker.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.caption("Live • Multi-user • Auto-refresh")
