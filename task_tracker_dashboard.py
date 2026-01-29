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

STATUS_OPTIONS = ["Pending", "In Progress", "Completed", "On Hold"]

# =====================================================
# DATA LOAD / SAVE
# =====================================================
def load_tasks():
    df = pd.read_csv(DATA_FILE)
    df["task_id"] = df["task_id"].astype(str)
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce")
    df["status"] = df["status"].fillna("Pending")
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
# STATUS COLORING
# =====================================================
def status_color(val):
    return {
        "Completed": "background-color:#d4edda",
        "In Progress": "background-color:#d1ecf1",
        "Pending": "background-color:#fff3cd",
        "On Hold": "background-color:#f8d7da",
    }.get(val, "")

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
        "<style>.stApp{background-color:#0E1117;color:white}</style>",
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

c1, c2, c3 = st.columns([5, 2, 1])
c1.markdown(f"## Hello, {st.session_state.user}")
c2.markdown(f"🕒 **{now_ist}**")

if c3.button("Dark / Light"):
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
# KPI
# =====================================================
today_ts = pd.Timestamp(date.today())

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Tasks", len(df))
k2.metric("Completed", (df["status"] == "Completed").sum())
k3.metric("Pending", (df["status"] == "Pending").sum())
k4.metric(
    "Overdue",
    (
        df["due_date"].notna()
        & (df["due_date"] < today_ts)
        & (df["status"] != "Completed")
    ).sum()
)

# =====================================================
# UPDATE TASK STATUS (FIXED)
# =====================================================
st.subheader("🔄 Update Task Status")

if not df.empty:
    df["label"] = df.apply(
        lambda x: f"{x['task']} | {x['assignee']} | {x['status']}",
        axis=1
    )
    label_to_id = dict(zip(df["label"], df["task_id"]))

    selected_label = st.selectbox("Select Task", list(label_to_id.keys()))
    selected_id = label_to_id[selected_label]

    current_status = df.loc[df["task_id"] == selected_id, "status"].iloc[0]

    # 🔑 FIX
    if current_status not in STATUS_OPTIONS:
        current_status = "Pending"

    new_status = st.selectbox(
        "New Status",
        STATUS_OPTIONS,
        index=STATUS_OPTIONS.index(current_status)
    )

    if st.button("Update Status"):
        df.loc[df["task_id"] == selected_id, "status"] = new_status
        save_tasks(df)
        st.success("Status updated")
        st.rerun()
else:
    st.info("No tasks available")

# =====================================================
# TASK TABLE (COLORED)
# =====================================================
st.subheader("📋 Task List")

if not df.empty:
    display_df = df.copy()
    display_df["Start Date"] = display_df["start_date"].dt.strftime("%d-%b-%Y")
    display_df["Expected Completion"] = display_df["due_date"].dt.strftime("%d-%b-%Y").fillna("TBD")

    styled = (
        display_df[
            ["task", "assignee", "department", "Start Date", "Expected Completion", "status", "priority"]
        ]
        .style
        .applymap(status_color, subset=["status"])
    )

    st.dataframe(styled, use_container_width=True)
else:
    st.info("No tasks available")
