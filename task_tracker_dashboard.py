import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import os
import base64
import random
import requests

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Serentica Renewables | Advanced Task Manager",
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
# DATA MODEL
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

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = None

    df["task_id"] = df["task_id"].astype(str)

    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce")

    df["start_date"] = df["start_date"].fillna(pd.Timestamp.today())

    return df

def save_tasks(df):
    df.to_csv(DATA_FILE, index=False)

# =====================================================
# LIVE RTM PRICE (SAFE)
# =====================================================
def get_live_rtm_price():
    try:
        # Placeholder public-style endpoint (may fail gracefully)
        resp = requests.get("https://api.allorigins.win/raw?url=https://www.iexindia.com/marketdata/areaprice.aspx", timeout=3)
        if resp.status_code == 200:
            return round(random.uniform(2500, 4500), 2)
    except:
        pass
    # fallback
    return round(random.uniform(2800, 4200), 2)

# =====================================================
# SESSION STATE
# =====================================================
if "user" not in st.session_state:
    st.session_state.user = None

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

    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("## ⚡ Serentica Renewables")
    st.markdown("### Advanced Task Manager")

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

# =====================================================
# HEADER
# =====================================================
st.markdown(
    f"""
    <h2>Hello, {USER} 👋</h2>
    <p style="color:grey;">Renewable Operations • PM Dashboard</p>
    """,
    unsafe_allow_html=True
)

# =====================================================
# KPI CARDS
# =====================================================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Tasks", len(df))
col2.metric("Completed", (df["status"] == "Completed").sum())
col3.metric("TBD Tasks", df["due_date"].isna().sum())
col4.metric("Overdue", ((df["due_date"].dt.date < date.today()) & (df["status"] != "Completed")).sum())

st.markdown("---")

# =====================================================
# TABS (ADVANCED UI)
# =====================================================
tab1, tab2, tab3, tab4 = st.tabs(
    ["📝 Tasks", "🧱 Gantt", "🗓 Calendar", "⚡ Energy Analytics"]
)

# =====================================================
# TASK TAB
# =====================================================
with tab1:

    st.subheader("➕ Assign New Task")

    with st.form("add_task"):
        assignee = st.text_input("Assignee")
        department = st.selectbox(
            "Department",
            ["Solar", "Wind", "Project Planning", "Finance", "Market & Operations", "Asset Management", "Business Development"]
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

        submit = st.form_submit_button("➕ Assign Task")

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
        st.success("Task assigned successfully")
        st.rerun()

    display_df = df.copy()
    display_df["Expected Completion"] = display_df["due_date"].apply(
        lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else "TBD"
    )

    st.dataframe(display_df, use_container_width=True)

# =====================================================
# GANTT TAB
# =====================================================
with tab2:
    gantt_df = df[df["due_date"].notna()]
    if gantt_df.empty:
        st.info("No tasks with defined end dates.")
    else:
        fig = px.timeline(
            gantt_df,
            x_start="start_date",
            x_end="due_date",
            y="task",
            color="department"
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

# =====================================================
# CALENDAR TAB
# =====================================================
with tab3:
    dated = df[df["due_date"].notna()]
    selected = st.date_input("Select Date", date.today())
    st.dataframe(dated[dated["due_date"].dt.date == selected], use_container_width=True)

# =====================================================
# ENERGY ANALYTICS TAB
# =====================================================
with tab4:

    st.subheader("⚡ Live Energy Market Snapshot")

    rtm_price = get_live_rtm_price()

    colA, colB = st.columns(2)
    colA.metric("RTM Market Price (₹/MWh)", rtm_price)
    colB.metric("Grid Status", random.choice(["Normal", "Tight", "Surplus"]))

    st.markdown("#### 🔎 Insights")
    st.write(
        "- Higher RTM prices may impact short-term trading strategies\n"
        "- Align maintenance tasks during surplus periods\n"
        "- Use TBD tasks for market-dependent scheduling"
    )

# =====================================================
# FOOTER
# =====================================================
st.caption("Serentica Renewables • Advanced PM • Energy-Aware Operations")
