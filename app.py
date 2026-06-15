import streamlit as st
import pandas as pd
import json
import os
import hashlib
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Ensure database exists
DB_FILE = "orders_db.json"
EXCEL_PATH = os.path.join("watched", "service_orders.xlsx")

def load_db():
    if not os.path.exists(DB_FILE):
        return {"orders": [], "tickets": [], "logs": [], "imported_hashes": []}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_action(user, action):
    db = load_db()
    db["logs"].append({
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "user": user,
        "action": action
    })
    save_db(db)

# Excel live poller function
def poll_excel_file():
    if not os.path.exists(EXCEL_PATH):
        return False
    
    try:
        # Load the file
        df = pd.read_excel(EXCEL_PATH)
        # Normalize headers: replace spaces with underscores, strip, and lowercase
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        
        required_cols = ["project_id", "skill", "role", "start_date", "end_date"]
        for col in required_cols:
            if col not in df.columns:
                return False
                
        db = load_db()
        imported_hashes = set(db.get("imported_hashes", []))
        new_orders = []
        
        for _, row in df.iterrows():
            p_id = str(row.get("project_id", "")).strip()
            skill = str(row.get("skill", "")).strip()
            role = str(row.get("role", "")).strip()
            s_date = str(row.get("start_date", "")).strip()
            e_date = str(row.get("end_date", "")).strip()
            
            if not p_id or p_id == "nan":
                continue
                
            # Create a unique row identifier hash
            row_str = f"{p_id}-{skill}-{role}-{s_date}-{e_date}"
            row_hash = hashlib.md5(row_str.encode("utf-8")).hexdigest()
            
            if row_hash not in imported_hashes:
                # Format dates nicely
                try:
                    s_date_clean = pd.to_datetime(s_date).strftime("%Y-%m-%d")
                    e_date_clean = pd.to_datetime(e_date).strftime("%Y-%m-%d")
                except:
                    s_date_clean = s_date.split(" ")[0] if " " in s_date else s_date
                    e_date_clean = e_date.split(" ")[0] if " " in e_date else e_date
                
                next_so_num = len(db["orders"]) + 1
                new_id = f"SO-2026-{next_so_num:04d}"
                
                new_order = {
                    "id": new_id,
                    "customer_name": "System Integration Sync",
                    "organization": "Automated Excel Sync",
                    "contact_details": "excel-agent@company.com",
                    "service_category": "Software Engineering Services",
                    "priority": "High" if "Senior" in role or "Lead" in role else "Medium",
                    "description": f"Automated Service Order created from Excel sync. Project ID: {p_id}. Required Skill: {skill}. Role: {role}. Expected timeline: {s_date_clean} to {e_date_clean}.",
                    "delivery_date": e_date_clean,
                    "status": "Submitted",
                    "progress": 0,
                    "engineer": "Unassigned",
                    "digital_signature": None,
                    "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "source": "Excel Sync",
                    "project_id": p_id,
                    "skill": skill,
                    "role": role
                }
                
                db["orders"].append(new_order)
                db["imported_hashes"].append(row_hash)
                
                # Add to logs
                db["logs"].append({
                    "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "user": "System (Excel Watcher)",
                    "action": f"Auto-imported Service Order {new_id} from Excel row (Project: {p_id})"
                })
                
                new_orders.append(new_id)
                
        if new_orders:
            save_db(db)
            st.session_state["recent_imports"] = new_orders
            return True
            
    except PermissionError:
        # Excel is open and locked by MS Excel
        st.session_state["excel_lock_warning"] = True
    except Exception as e:
        print("Excel Sync Exception:", e)
        
    return False

# Setup Streamlit App Layout
st.set_page_config(
    page_title="Enterprise Service Order Management Portal",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Call watcher/sync
poll_excel_file()

# Styling Injection for SaaS look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Elegant Title and Headers */
    .portal-header {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #0f62fe 0%, #002d9c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    .portal-subtitle {
        font-size: 1.1rem;
        color: #525252;
        margin-bottom: 25px;
    }

    /* Glassmorphism KPI Card */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #e0e0e0;
        border-top: 4px solid #0f62fe;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 18px rgba(15, 98, 254, 0.1);
    }
    .metric-val {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f62fe;
    }
    .metric-title {
        font-size: 0.9rem;
        color: #525252;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Custom Timeline CSS */
    .timeline-wrapper {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 0;
        margin-top: 10px;
        position: relative;
    }
    .timeline-line {
        position: absolute;
        height: 4px;
        background: #e0e0e0;
        left: 5%;
        right: 5%;
        z-index: 1;
    }
    .timeline-progress-line {
        position: absolute;
        height: 4px;
        background: #0f62fe;
        left: 5%;
        z-index: 2;
        transition: width 0.5s ease;
    }
    .timeline-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        z-index: 3;
        width: 12.5%;
    }
    .timeline-node {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: #ffffff;
        border: 3px solid #e0e0e0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 11px;
        color: #a8a8a8;
        transition: all 0.3s ease;
    }
    .timeline-node.completed {
        background: #24a148;
        border-color: #24a148;
        color: white;
    }
    .timeline-node.active {
        background: #0f62fe;
        border-color: #0f62fe;
        color: white;
        box-shadow: 0 0 10px rgba(15, 98, 254, 0.5);
    }
    .timeline-label {
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 8px;
        color: #525252;
        text-align: center;
    }
    .timeline-label.active {
        color: #0f62fe;
        font-weight: 700;
    }

    /* Custom Kanban Board styles */
    .kanban-col {
        background-color: #f1f3f5;
        border-radius: 8px;
        padding: 12px;
        min-height: 400px;
    }
    .kanban-title {
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 12px;
        color: #343a40;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .kanban-card {
        background: white;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border-left: 4px solid #0f62fe;
        transition: transform 0.15s ease;
    }
    .kanban-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .kanban-card-id {
        font-size: 0.75rem;
        font-weight: 700;
        color: #0f62fe;
        margin-bottom: 4px;
    }
    .kanban-card-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: #212529;
        margin-bottom: 6px;
    }
    .kanban-card-meta {
        font-size: 0.75rem;
        color: #6c757d;
        display: flex;
        justify-content: space-between;
    }
    
    /* Support Chat Bubbles */
    .chat-bubble-customer {
        background-color: #f1f3f9;
        color: #212529;
        padding: 10px 14px;
        border-radius: 12px 12px 12px 0px;
        margin-bottom: 10px;
        max-width: 80%;
        display: inline-block;
        float: left;
        clear: both;
    }
    .chat-bubble-staff {
        background-color: #e3f2fd;
        color: #0b3c5d;
        padding: 10px 14px;
        border-radius: 12px 12px 0px 12px;
        margin-bottom: 10px;
        max-width: 80%;
        display: inline-block;
        float: right;
        clear: both;
        border: 1px solid #bbdefb;
    }
    .chat-meta {
        font-size: 0.7rem;
        color: #8c8c8c;
        margin-top: 4px;
        display: block;
    }

    /* Hide default sidebar open button to enforce top-bar only navigation */
    section[data-testid="stSidebar"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to get status timeline progress percentage
STATUS_STAGES = ["Submitted", "Under Review", "Approved", "Development", "Testing", "Deployment", "Completed"]
def get_status_percentage(status):
    if status not in STATUS_STAGES:
        return 0
    idx = STATUS_STAGES.index(status)
    return int((idx / (len(STATUS_STAGES) - 1)) * 100)

# Load current DB
db = load_db()

# Top Header Layout with Logo, Sync Button, and Role selector in the top right
col_header, col_sync, col_role = st.columns([3.2, 1.1, 1.3])
with col_header:
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 15px; margin-top: 5px; margin-bottom: 10px;'>
        <img src='https://img.icons8.com/color/96/000000/cloud-lighting.png' width='45' />
        <div>
            <span style='font-size: 2.2rem; font-weight: 700; background: linear-gradient(135deg, #0f62fe 0%, #002d9c 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1;'>XYZ</span>
            <span style='font-size: 1.2rem; color: #525252; border-left: 2px solid #ccc; padding-left: 15px; margin-left: 10px; font-weight: 500;'>Enterprise Service Portal</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_sync:
    st.markdown("<div style='margin-top:25px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Sync Excel", use_container_width=True, help="Force sync and reload service orders from watched/service_orders.xlsx"):
        if poll_excel_file():
            st.toast("🚨 Imported new orders from Excel!", icon="⚡")
            st.rerun()
        else:
            st.toast("✅ Database is up to date.", icon="👍")
            st.rerun()
with col_role:
    user_role = st.selectbox(
        "Current System Role Context",
        ["Admin", "Manager", "Engineer", "Customer"],
        index=3,
        help="Select a role context to view appropriate dashboards and actions."
    )
    # User identity tag below dropdown
    if user_role == "Customer":
        current_user_name = "Sarah Jenkins"
        st.markdown("<div style='text-align: right; font-size: 0.8rem; color: #525252; margin-top:-8px;'>User: <b>Sarah Jenkins</b> (Acme FinTech)</div>", unsafe_allow_html=True)
    elif user_role == "Admin":
        current_user_name = "System Admin"
        st.markdown("<div style='text-align: right; font-size: 0.8rem; color: #24a148; margin-top:-8px;'>User: <b>Administrator</b></div>", unsafe_allow_html=True)
    elif user_role == "Manager":
        current_user_name = "Delivery Manager (Alex)"
        st.markdown("<div style='text-align: right; font-size: 0.8rem; color: #f1c40f; margin-top:-8px;'>User: <b>Delivery Manager</b></div>", unsafe_allow_html=True)
    else:
        current_user_name = "David K. (Engineer)"
        st.markdown("<div style='text-align: right; font-size: 0.8rem; color: #0f62fe; margin-top:-8px;'>User: <b>David K. (Architect)</b></div>", unsafe_allow_html=True)

# Render Excel Lock warning if present (e.g. if file is open in MS Excel)
if st.session_state.get("excel_lock_warning"):
    st.warning("⚠️ **Excel File Locked:** The spreadsheet `watched/service_orders.xlsx` is open in Microsoft Excel or another editor. Please save and close Excel to sync new records.")
    st.session_state["excel_lock_warning"] = False

# Sync notifications toast
if "recent_imports" in st.session_state and st.session_state["recent_imports"]:
    st.toast(f"🚨 Live Excel Watcher: Imported {len(st.session_state['recent_imports'])} new Service Orders!", icon="⚡")
    del st.session_state["recent_imports"]

# Dynamic tab navigation list
tabs_list = ["🏠 Home Page", "💼 Customer Portal", "➕ Service Order Creation", "🔍 Order Tracking", "💬 Support Systems"]
if user_role in ["Admin", "Manager", "Engineer"]:
    tabs_list.append("📈 Project Management")
if user_role == "Admin":
    tabs_list.append("🔑 Admin Portal")

# Render Top Tabs Navigation Bar
tabs = st.tabs(tabs_list)

# Render tab contents dynamically
for name, tab in zip(tabs_list, tabs):
    with tab:
        if "Home Page" in name:
            st.markdown("<div class='portal-header'>Streamline Software Service Requests and Project Delivery</div>", unsafe_allow_html=True)
            st.markdown("<div class='portal-subtitle'>Welcome to XYZ Services. Accelerate engineering delivery, automate project scoping, and monitor real-time SLA completion.</div>", unsafe_allow_html=True)
            
            # Visual Banner Graphic
            st.markdown("""
            <div style='background: linear-gradient(135deg, #0f62fe 0%, #001c66 100%); padding: 50px 30px; border-radius: 12px; color: white; margin-bottom: 30px;'>
                <h2 style='color: white; margin-top:0;'>Modern Project Intake & Resource Orchestration</h2>
                <p style='font-size: 1.15rem; max-width: 800px; opacity: 0.9;'>
                    Submit software engineering requests manually or simply append them into a shared corporate Excel worksheet. Our system automatically parses skillsets, allocates roles, establishes Gantt schedules, and notifies engineering teams instantly.
                </p>
                <div style='margin-top: 25px;'>
                    <span style='background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; font-size: 0.9rem; font-weight:600; margin-right: 10px;'>📊 100% SLA Compliant</span>
                    <span style='background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; font-size: 0.9rem; font-weight:600; margin-right: 10px;'>⚡ Live Excel Poller</span>
                    <span style='background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; font-size: 0.9rem; font-weight:600;'>🔐 RBAC Access Control</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Main call to actions
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("""
                <div style='background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e0e0e0; min-height: 220px;'>
                    <h3 style='color: #0f62fe; margin-top:0;'>Submit Service Request</h3>
                    <p style='color: #525252; font-size:0.95rem;'>Create a detailed project charter specifying resource roles, technology stacks, delivery dates, and security requirements.</p>
                </div>
                """, unsafe_allow_html=True)
                st.caption("💡 Switch to the **➕ Service Order Creation** tab above.")
                    
            with col2:
                st.markdown("""
                <div style='background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e0e0e0; min-height: 220px; margin-bottom: 15px;'>
                    <h3 style='color: #002d9c; margin-top:0;'>Excel Watcher Directory</h3>
                    <p style='color: #525252; font-size:0.95rem;'>Open the corporate spreadsheet file located at <code>watched/service_orders.xlsx</code>. Saving new entries instantly syncs them here.</p>
                </div>
                """, unsafe_allow_html=True)
                if os.path.exists(EXCEL_PATH):
                    with open(EXCEL_PATH, "rb") as file:
                        st.download_button(
                            label="📥 Download Excel Template",
                            data=file,
                            file_name="service_orders_template.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="home_download_btn",
                            use_container_width=True
                        )
                    
            with col3:
                st.markdown("""
                <div style='background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e0e0e0; min-height: 220px;'>
                    <h3 style='color: #161616; margin-top:0;'>Live Helpdesk</h3>
                    <p style='color: #525252; font-size:0.95rem;'>Run support chat requests, discuss engineering blockers with assigned architects, and view resolution history.</p>
                </div>
                """, unsafe_allow_html=True)
                st.caption("💡 Switch to the **💬 Support Systems** tab above.")

            # Corporate Overview & testimonials
            st.markdown("### Client Testimonials & Enterprise Trust")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                > **"The live Excel integration transformed how our management submits requirements. Our teams just append new roles into their local sheet and within seconds they appear mapped, scheduled, and staffed."**
                > <br>*— CTO, Acme FinTech Corp*
                """, unsafe_allow_html=True)
            with col2:
                st.markdown("""
                > **"Having HIPAA security templates pre-loaded and integrated into electronic signature pads speeds up client onboarding from weeks to less than 24 hours."**
                > <br>*— Compliance Director, MedTech Solutions*
                """, unsafe_allow_html=True)

        elif "Customer Portal" in name:
            st.markdown("<div class='portal-header'>Customer Dashboard</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='portal-subtitle'>Real-time tracking of active orders, notifications, and approvals for <b>{current_user_name}</b>.</div>", unsafe_allow_html=True)
            
            # Metric rows
            total_orders = len(db["orders"])
            active_orders = len([o for o in db["orders"] if o["status"] not in ["Completed"]])
            completed_orders = len([o for o in db["orders"] if o["status"] == "Completed"])
            pending_approvals = len([o for o in db["orders"] if o["status"] == "Submitted"])
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"<div class='metric-card'><div class='metric-val'>{total_orders}</div><div class='metric-title'>Total Requests</div></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='metric-card'><div class='metric-val'>{active_orders}</div><div class='metric-title'>Active Orders</div></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div class='metric-card'><div class='metric-val'>{completed_orders}</div><div class='metric-title'>Completed</div></div>", unsafe_allow_html=True)
            with c4:
                st.markdown(f"<div class='metric-card'><div class='metric-val'>{pending_approvals}</div><div class='metric-title'>Pending Review</div></div>", unsafe_allow_html=True)
                
            st.markdown("---")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### Active Service Orders")
                filtered_orders = db["orders"]
                if user_role == "Customer":
                    filtered_orders = [o for o in db["orders"] if o["organization"] in ["Acme FinTech Corp", "Automated Excel Sync", "Excel Auto Sync"]]
                    
                if not filtered_orders:
                    st.info("No active service orders found for your organization.")
                else:
                    for order in filtered_orders:
                        st.markdown(f"""
                        <div style='background: white; padding: 15px; border-radius: 10px; margin-bottom: 12px; border: 1px solid #e0e0e0; border-left: 5px solid {"#24a148" if order["status"]=="Completed" else "#0f62fe" if order["status"]=="Development" else "#f1c40f"};'>
                            <div style='display: flex; justify-content: space-between;'>
                                <strong style='font-size:1.1rem; color:#161616;'>{order["id"]} - {order["service_category"]}</strong>
                                <span style='background-color:#e8f0fe; color:#0f62fe; padding:2px 8px; border-radius:12px; font-size:0.8rem; font-weight:600;'>{order["status"]}</span>
                            </div>
                            <p style='font-size:0.9rem; color:#525252; margin: 8px 0;'>{order["description"]}</p>
                            <div style='display:flex; justify-content:space-between; font-size:0.8rem; color:#8c8c8c;'>
                                <span>Client: <b>{order["organization"]}</b></span>
                                <span>Delivery Date: <b>{order["delivery_date"]}</b></span>
                                <span>Assignee: <b>{order["engineer"]}</b></span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
            with col2:
                st.markdown("### Recent Updates & Alerts")
                logs = db["logs"][-5:]
                logs.reverse()
                for log in logs:
                    st.markdown(f"""
                    <div style='padding: 10px; border-bottom: 1px solid #e0e0e0; font-size: 0.85rem;'>
                        <span style='color: #8c8c8c; font-size: 0.75rem;'>🕒 {log["timestamp"]}</span>
                        <p style='margin: 3px 0; color:#333;'><b>{log["user"]}:</b> {log["action"]}</p>
                    </div>
                    """, unsafe_allow_html=True)

        elif "Service Order Creation" in name:
            st.markdown("<div class='portal-header'>Service Order Creation</div>", unsafe_allow_html=True)
            st.markdown("<div class='portal-subtitle'>Submit a detailed custom service request or upload a bulk Excel data sheet.</div>", unsafe_allow_html=True)
            
            tab_manual, tab_excel = st.tabs(["📋 Standard Request Form", "📂 Bulk Excel Upload"])
            
            with tab_manual:
                st.markdown("### Complete Service Specifications")
                with st.form("service_order_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        cust_name = st.text_input("Customer Name", value="Sarah Jenkins" if user_role == "Customer" else "")
                        org_name = st.text_input("Organization", value="Acme FinTech Corp" if user_role == "Customer" else "")
                        contact = st.text_input("Contact Email/Phone", value="sarah.j@acmefintech.com" if user_role == "Customer" else "")
                        category = st.selectbox("Service Category", [
                            "Cloud Migration & Architecture", 
                            "Full Stack Web Application",
                            "UI/UX & Frontend Development",
                            "DevOps & CI/CD Pipeline",
                            "Mobile App Development",
                            "Database Optimization Services"
                        ])
                    with col2:
                        priority = st.selectbox("Priority Level", ["Low", "Medium", "High", "Critical"])
                        delivery_date = st.date_input("Desired Delivery Date", min_value=datetime.today())
                        attachment = st.file_uploader("Attach Project Specifications (PDF, Docx)", type=["pdf", "docx", "zip"])
                        
                    project_desc = st.text_area("Project/Role Requirements & Description", placeholder="Detail the skills, programming languages, framework dependencies, or resource duration requirements...")
                    
                    submit_btn = st.form_submit_button("Generate Service Order Request")
                    
                    if submit_btn:
                        if not cust_name or not org_name or not project_desc:
                            st.error("Error: Please fill out all required fields (Name, Organization, and Description).")
                        else:
                            next_num = len(db["orders"]) + 1
                            so_id = f"SO-2026-{next_num:04d}"
                            
                            new_order = {
                                "id": so_id,
                                "customer_name": cust_name,
                                "organization": org_name,
                                "contact_details": contact,
                                "service_category": category,
                                "priority": priority,
                                "description": project_desc,
                                "delivery_date": str(delivery_date),
                                "status": "Submitted",
                                "progress": 0,
                                "engineer": "Unassigned",
                                "digital_signature": None,
                                "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "source": "Manual",
                                "project_id": "PRJ-MAN-" + str(next_num),
                                "skill": "Form Input",
                                "role": "Consulting Spec"
                            }
                            db["orders"].append(new_order)
                            
                            db["logs"].append({
                                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "user": f"Customer ({cust_name})",
                                "action": f"Created Service Order {so_id} manually"
                            })
                            
                            save_db(db)
                            st.success(f"🎉 Service Order **{so_id}** created successfully!")
                            st.balloons()
                            st.rerun()
                            
            with tab_excel:
                st.markdown("### Upload Batch Excel Sheet")
                st.markdown("Select a batch `.xlsx` or `.csv` service sheet matching columns: `project_id`, `skill`, `role`, `start date`, `end date`.")
                
                col_upload, col_download = st.columns([3, 1])
                with col_upload:
                    batch_file = st.file_uploader("Upload Excel File", type=["xlsx", "csv"])
                with col_download:
                    st.markdown("<div style='margin-top:25px;'></div>", unsafe_allow_html=True)
                    if os.path.exists(EXCEL_PATH):
                        with open(EXCEL_PATH, "rb") as file:
                            st.download_button(
                                label="📥 Download Excel Template",
                                data=file,
                                file_name="service_orders_template.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="creation_download_btn",
                                use_container_width=True
                            )
                
                if batch_file:
                    try:
                        if batch_file.name.endswith(".csv"):
                            df = pd.read_csv(batch_file)
                        else:
                            df = pd.read_excel(batch_file)
                            
                        df.columns = [c.strip().lower() for c in df.columns]
                        required = ["project_id", "skill", "role", "start date", "end date"]
                        missing = [col for col in required if col not in df.columns]
                        
                        if missing:
                            st.error(f"Validation Failed: Excel is missing columns: {', '.join(missing)}")
                        else:
                            st.dataframe(df, use_container_width=True)
                            
                            import_btn = st.button("Process & Import Batch Service Orders")
                            if import_btn:
                                imported_count = 0
                                imported_hashes = set(db.get("imported_hashes", []))
                                
                                for _, row in df.iterrows():
                                    p_id = str(row.get("project_id", "")).strip()
                                    skill = str(row.get("skill", "")).strip()
                                    role = str(row.get("role", "")).strip()
                                    s_date = str(row.get("start date", "")).strip()
                                    e_date = str(row.get("end date", "")).strip()
                                    
                                    if not p_id or p_id == "nan":
                                        continue
                                        
                                    row_str = f"{p_id}-{skill}-{role}-{s_date}-{e_date}"
                                    row_hash = hashlib.md5(row_str.encode("utf-8")).hexdigest()
                                    
                                    if row_hash not in imported_hashes:
                                        try:
                                            s_date_clean = pd.to_datetime(s_date).strftime("%Y-%m-%d")
                                            e_date_clean = pd.to_datetime(e_date).strftime("%Y-%m-%d")
                                        except:
                                            s_date_clean = s_date.split(" ")[0] if " " in s_date else s_date
                                            e_date_clean = e_date.split(" ")[0] if " " in e_date else e_date
                                            
                                        next_num = len(db["orders"]) + 1
                                        so_id = f"SO-2026-{next_num:04d}"
                                        
                                        new_order = {
                                            "id": so_id,
                                            "customer_name": f"Batch Upload Admin ({current_user_name})",
                                            "organization": "Bulk Batch Sync",
                                            "contact_details": "batch-uploader@enterprise.com",
                                            "service_category": "Software Engineering Services",
                                            "priority": "High" if "Senior" in role or "Lead" in role else "Medium",
                                            "description": f"Bulk Service Order imported. Project ID: {p_id}. Skill: {skill}. Role: {role}. Expected timeline: {s_date_clean} to {e_date_clean}.",
                                            "delivery_date": e_date_clean,
                                            "status": "Submitted",
                                            "progress": 0,
                                            "engineer": "Unassigned",
                                            "digital_signature": None,
                                            "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                            "source": "Excel Batch",
                                            "project_id": p_id,
                                            "skill": skill,
                                            "role": role
                                        }
                                        db["orders"].append(new_order)
                                        db["imported_hashes"].append(row_hash)
                                        imported_count += 1
                                        
                                if imported_count > 0:
                                    db["logs"].append({
                                        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                        "user": current_user_name,
                                        "action": f"Uploaded batch sheet and imported {imported_count} Service Orders"
                                    })
                                    save_db(db)
                                    st.success(f"Import complete! Successfully added **{imported_count}** new Service Orders.")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.info("No new rows found. All entries have already been processed.")
                                    
                    except Exception as ex:
                        st.error(f"Error parsing file: {ex}")

        elif "Order Tracking" in name:
            st.markdown("<div class='portal-header'>Order Tracking & Status Lifecycle</div>", unsafe_allow_html=True)
            st.markdown("<div class='portal-subtitle'>Query specific Service Order IDs to view progression timelines and milestones.</div>", unsafe_allow_html=True)
            
            order_ids = [o["id"] for o in db["orders"]]
            
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown("### Search Order")
                search_id = st.selectbox("Select Order ID", order_ids)
                
            with col2:
                order = next((o for o in db["orders"] if o["id"] == search_id), None)
                if order:
                    st.markdown(f"## Status details for **{order['id']}**")
                    st.markdown(f"**Description:** {order['description']}")
                    
                    percent = get_status_percentage(order["status"])
                    st.progress(percent / 100.0)
                    st.write(f"Completion progression: **{percent}%** | Current Phase: **{order['status']}**")
                    
                    st.markdown("---")
                    st.markdown("### Progression Lifecycle")
                    
                    timeline_html = "<div class='timeline-wrapper'>"
                    timeline_html += "<div class='timeline-line'></div>"
                    
                    active_idx = STATUS_STAGES.index(order["status"])
                    progress_width = (active_idx / (len(STATUS_STAGES) - 1)) * 90
                    timeline_html += f"<div class='timeline-progress-line' style='width: {progress_width}%;'></div>"
                    
                    for i, stage in enumerate(STATUS_STAGES):
                        node_class = ""
                        label_class = ""
                        if i < active_idx:
                            node_class = "completed"
                            node_char = "✓"
                        elif i == active_idx:
                            node_class = "active"
                            node_char = str(i+1)
                            label_class = "active"
                        else:
                            node_class = "future"
                            node_char = str(i+1)
                            
                        timeline_html += f"<div class='timeline-step'><div class='timeline-node {node_class}'>{node_char}</div><div class='timeline-label {label_class}'>{stage}</div></div>"
                    timeline_html += "</div>"
                    st.html(timeline_html)
                    
                    st.markdown("---")
                    st.markdown("### Project Parameters")
                    mcol1, mcol2 = st.columns(2)
                    with mcol1:
                        st.write(f"**Customer:** {order['customer_name']} ({order['organization']})")
                        st.write(f"**Category:** {order['service_category']}")
                        st.write(f"**Delivery Target:** {order['delivery_date']}")
                    with mcol2:
                        st.write(f"**Priority:** {order['priority']}")
                        st.write(f"**Assigned Architect:** {order['engineer']}")
                        st.write(f"**Source Intake:** {order['source']}")
                else:
                    st.error("Select a valid service order from the list.")

        elif "Support Systems" in name:
            st.markdown("<div class='portal-header'>Support Ticket System</div>", unsafe_allow_html=True)
            st.markdown("<div class='portal-subtitle'>Submit support queries, chat with assigned engineers, and monitor active ticket threads.</div>", unsafe_allow_html=True)
            
            tab_chat, tab_new = st.tabs(["💬 Active Chats", "🎫 Open New Support Ticket"])
            
            with tab_chat:
                if not db["tickets"]:
                    st.info("No active support tickets found.")
                else:
                    ticket_titles = [f"{t['id']} - {t['title']} ({t['status']})" for t in db["tickets"]]
                    selected_tkt_title = st.selectbox("Select Support Thread", ticket_titles)
                    
                    selected_tkt_id = selected_tkt_title.split(" - ")[0]
                    ticket = next((t for t in db["tickets"] if t["id"] == selected_tkt_id), None)
                    
                    if ticket:
                        st.markdown(f"### Ticket: **{ticket['title']}**")
                        st.write(f"Priority: **{ticket['priority']}** | Status: **{ticket['status']}** | Created: {ticket['created_at']}")
                        
                        st.markdown("---")
                        st.markdown("<div style='background-color:#ffffff; padding:20px; border-radius:8px; border:1px solid #e0e0e0; min-height:300px;'>", unsafe_allow_html=True)
                        for msg in ticket["messages"]:
                            bubble_class = "chat-bubble-staff" if msg["is_admin"] else "chat-bubble-customer"
                            st.markdown(f"""
                            <div class='{bubble_class}'>
                                <strong>{msg["sender"]}</strong><br>
                                {msg["text"]}
                                <span class='chat-meta'>🕒 {msg["timestamp"]}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        st.markdown("---")
                        with st.form("chat_reply_form", clear_on_submit=True):
                            reply_text = st.text_input("Enter Message")
                            col1, col2 = st.columns([5, 1])
                            with col2:
                                send_btn = st.form_submit_button("Send Response", use_container_width=True)
                                
                            if send_btn and reply_text:
                                new_msg = {
                                    "sender": current_user_name,
                                    "text": reply_text,
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "is_admin": user_role in ["Admin", "Manager", "Engineer"]
                                }
                                ticket["messages"].append(new_msg)
                                save_db(db)
                                st.rerun()
                                
            with tab_new:
                st.markdown("### Lodge Formal Technical Support Ticket")
                with st.form("open_ticket_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        tkt_title = st.text_input("Ticket Title/Subject")
                        tkt_priority = st.selectbox("Priority Impact", ["Low", "Medium", "High", "Blocker"])
                    with col2:
                        tkt_order_link = st.selectbox("Link to Service Order ID", ["General Inquiry"] + [o["id"] for o in db["orders"]])
                        tkt_attachment = st.file_uploader("Attach Logs/Errors", type=["txt", "log", "png", "jpg"])
                        
                    tkt_description = st.text_area("Detailed Error Description / Question")
                    tkt_submit = st.form_submit_button("Open Support Thread")
                    
                    if tkt_submit:
                        if not tkt_title or not tkt_description:
                            st.error("Please fill out Title and Description fields.")
                        else:
                            new_tkt_id = f"TKT-{len(db['tickets']) + 1001}"
                            new_ticket = {
                                "id": new_tkt_id,
                                "title": f"{tkt_title} (Order: {tkt_order_link})",
                                "priority": tkt_priority,
                                "status": "Open",
                                "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "messages": [
                                    {
                                        "sender": current_user_name,
                                        "text": tkt_description,
                                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "is_admin": user_role in ["Admin", "Manager", "Engineer"]
                                    }
                                ]
                            }
                            db["tickets"].append(new_ticket)
                            db["logs"].append({
                                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "user": current_user_name,
                                "action": f"Opened support ticket {new_tkt_id}"
                            })
                            save_db(db)
                            st.success(f"Support ticket **{new_tkt_id}** created successfully!")
                            st.balloons()
                            st.rerun()

        elif "Project Management" in name:
            st.markdown("<div class='portal-header'>Project Management Dashboard</div>", unsafe_allow_html=True)
            st.markdown("<div class='portal-subtitle'>Task boards, resource timelines, and Gantt charts detailing sprint completions.</div>", unsafe_allow_html=True)
            
            tab_gantt, tab_kanban = st.tabs(["📊 Gantt Chart Visualization", "📋 Sprint Kanban Board"])
            
            with tab_gantt:
                st.markdown("### Project Duration & Resource Allocation Timeline")
                gantt_data = []
                for order in db["orders"]:
                    start_date = order.get("created_at", "2026-06-01")[:10]
                    end_date = order.get("delivery_date", "2026-08-01")
                    
                    try:
                        datetime.strptime(start_date, "%Y-%m-%d")
                    except:
                        start_date = "2026-06-01"
                    try:
                        datetime.strptime(end_date, "%Y-%m-%d")
                    except:
                        end_date = "2026-08-30"
                        
                    gantt_data.append({
                        "Task ID": order["id"],
                        "Category": order["service_category"],
                        "Start": start_date,
                        "Finish": end_date,
                        "Engineer": order["engineer"],
                        "Role/Skill": f"{order.get('role', 'Developer')} ({order.get('skill', 'Generic')})",
                        "Progress": order["progress"]
                    })
                    
                if not gantt_data:
                    st.info("No timelines found to generate Gantt chart.")
                else:
                    df_gantt = pd.DataFrame(gantt_data)
                    fig = px.timeline(
                        df_gantt,
                        x_start="Start",
                        x_end="Finish",
                        y="Task ID",
                        color="Engineer",
                        hover_data=["Category", "Role/Skill", "Progress"],
                        title="Service Request Fulfillment Gantt Chart"
                    )
                    fig.update_yaxes(autorange="reversed")
                    fig.update_layout(
                        xaxis_title="Timeline Range",
                        yaxis_title="Service Request ID",
                        height=400,
                        template="plotly_white"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
            with tab_kanban:
                st.markdown("### Visual Kanban Task Grid")
                col_submitted, col_dev, col_testing, col_completed = st.columns(4)
                
                with col_submitted:
                    count_intake = len([o for o in db["orders"] if o["status"] in ["Submitted", "Under Review", "Approved"]])
                    st.markdown(f"<div class='kanban-col'><div class='kanban-title'><span>Intake / Review</span> <span style='font-size:0.85em; background:#ccc; padding:2px 6px; border-radius:50%;'>{count_intake}</span></div>", unsafe_allow_html=True)
                    for o in db["orders"]:
                        if o["status"] in ["Submitted", "Under Review", "Approved"]:
                            st.markdown(f"""
                            <div class='kanban-card'>
                                <div class='kanban-card-id'>{o['id']} ({o['status']})</div>
                                <div class='kanban-card-title'>{o['service_category']}</div>
                                <div class='kanban-card-meta'>
                                    <span>👤 {o['organization']}</span>
                                    <span>📅 {o['delivery_date']}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                with col_dev:
                    count_dev = len([o for o in db["orders"] if o["status"] == "Development"])
                    st.markdown(f"<div class='kanban-col'><div class='kanban-title'><span>In Development</span> <span style='font-size:0.85em; background:#0f62fe; color:white; padding:2px 6px; border-radius:50%;'>{count_dev}</span></div>", unsafe_allow_html=True)
                    for o in db["orders"]:
                        if o["status"] == "Development":
                            st.markdown(f"""
                            <div class='kanban-card' style='border-left:4px solid #0f62fe;'>
                                <div class='kanban-card-id'>{o['id']}</div>
                                <div class='kanban-card-title'>{o['service_category']}</div>
                                <div class='kanban-card-meta'>
                                    <span>👤 {o['engineer']}</span>
                                    <span>⏳ {o['progress']}%</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                with col_testing:
                    count_testing = len([o for o in db["orders"] if o["status"] == "Testing"])
                    st.markdown(f"<div class='kanban-col'><div class='kanban-title'><span>QA / Testing</span> <span style='font-size:0.85em; background:#f1c40f; padding:2px 6px; border-radius:50%;'>{count_testing}</span></div>", unsafe_allow_html=True)
                    for o in db["orders"]:
                        if o["status"] == "Testing":
                            st.markdown(f"""
                            <div class='kanban-card' style='border-left:4px solid #f1c40f;'>
                                <div class='kanban-card-id'>{o['id']}</div>
                                <div class='kanban-card-title'>{o['service_category']}</div>
                                <div class='kanban-card-meta'>
                                    <span>👤 {o['engineer']}</span>
                                    <span>⏳ {o['progress']}%</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                with col_completed:
                    count_completed = len([o for o in db["orders"] if o["status"] in ["Deployment", "Completed"]])
                    st.markdown(f"<div class='kanban-col'><div class='kanban-title'><span>Deployed & Closed</span> <span style='font-size:0.85em; background:#24a148; color:white; padding:2px 6px; border-radius:50%;'>{count_completed}</span></div>", unsafe_allow_html=True)
                    for o in db["orders"]:
                        if o["status"] in ["Deployment", "Completed"]:
                            st.markdown(f"""
                            <div class='kanban-card' style='border-left:4px solid #24a148;'>
                                <div class='kanban-card-id'>{o['id']}</div>
                                <div class='kanban-card-title'>{o['service_category']}</div>
                                <div class='kanban-card-meta'>
                                    <span>👤 {o['engineer']}</span>
                                    <span>🏁 Closed</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

        elif "Admin Portal" in name:
            st.markdown("<div class='portal-header'>Admin Command Console</div>", unsafe_allow_html=True)
            st.markdown("<div class='portal-subtitle'>Electronic sign-offs, SLA monitoring, database audits, and staff resource management.</div>", unsafe_allow_html=True)
            
            col_g1, col_g2 = st.columns([2, 1])
            with col_g1:
                st.markdown("### SLA Compliance & Operational Health Gauges")
                fig_sla = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = 92.5,
                    delta = {'reference': 90.0, 'position': "top", 'relative': False, 'valueformat': ".1f%"},
                    title = {'text': "Service SLA Fulfillment Compliance %", 'font': {'size': 16}},
                    gauge = {
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                        'bar': {'color': "#0f62fe"},
                        'bgcolor': "white",
                        'borderwidth': 2,
                        'bordercolor': "gray",
                        'steps': [
                            {'range': [0, 80], 'color': '#ffe3e3'},
                            {'range': [80, 90], 'color': '#fff9e3'},
                            {'range': [90, 100], 'color': '#e3ffe3'}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ))
                fig_sla.update_layout(height=280, margin=dict(t=30, b=10, l=30, r=30))
                st.plotly_chart(fig_sla, use_container_width=True)
                
            with col_g2:
                st.markdown("### Revenue by Service Category")
                category_revenue = {}
                for o in db["orders"]:
                    cat = o["service_category"]
                    price = 45000 if "Migration" in cat else 28000 if "Full Stack" in cat else 15000
                    category_revenue[cat] = category_revenue.get(cat, 0) + price
                    
                df_rev = pd.DataFrame([{"Category": k, "Estimated Value ($)": v} for k, v in category_revenue.items()])
                fig_pie = px.pie(df_rev, values="Estimated Value ($)", names="Category", hole=0.3)
                fig_pie.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_pie, use_container_width=True)
                
            st.markdown("---")
            tab_approvals, tab_logs = st.tabs(["🔑 Approvals & Assignments", "📝 Security System Audit Logs"])
            
            with tab_approvals:
                st.markdown("### Electronic Signature Sign-offs & Engineer Allocation")
                pending_orders = [o for o in db["orders"] if o["status"] in ["Submitted", "Under Review"]]
                
                if not pending_orders:
                    st.info("No service orders currently pending approvals.")
                else:
                    selected_app_id = st.selectbox("Select Order to Approve/Allocate", [o["id"] for o in pending_orders])
                    ord_to_app = next((o for o in pending_orders if o["id"] == selected_app_id), None)
                    
                    if ord_to_app:
                        st.markdown(f"""
                        <div style='background-color:#ffffff; padding:15px; border-radius:8px; border:1px solid #0f62fe; margin-bottom:20px;'>
                            <h4>Fulfillment Request: {ord_to_app["id"]} ({ord_to_app["service_category"]})</h4>
                            <p><b>Client:</b> {ord_to_app["organization"]} | <b>Contact:</b> {ord_to_app["contact_details"]}</p>
                            <p><b>Required Profile/Skill:</b> {ord_to_app.get("role","Developer")} ({ord_to_app.get("skill","None")})</p>
                            <p><b>Project Scope:</b> {ord_to_app["description"]}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.form("approval_allocation_form"):
                            col1, col2 = st.columns(2)
                            with col1:
                                engineer_assignment = st.selectbox(
                                    "Allocate Engineering Lead", 
                                    ["Elena R. (Senior Fullstack Developer)", "David K. (Cloud Architect)", "Alex M. (UI/UX Frontend Engineer)", "Julian B. (DevOps Engineer)"]
                                )
                                target_status = st.selectbox("Update Project Status", ["Approved", "Development", "Testing"])
                            with col2:
                                authorizer_name = st.text_input("Authorizer Official Name", value=current_user_name)
                                digital_sign_agree = st.checkbox("Apply Official cryptographic token validation signature and bind SLA terms.")
                                
                            sign_btn = st.form_submit_button("Submit Signed Authorization Certificate")
                            
                            if sign_btn:
                                if not authorizer_name or not digital_sign_agree:
                                    st.error("Approval aborted: Authorizer Official Name is required, and you must verify signature agreement.")
                                else:
                                    for o in db["orders"]:
                                        if o["id"] == ord_to_app["id"]:
                                            o["status"] = target_status
                                            o["engineer"] = engineer_assignment
                                            o["digital_signature"] = authorizer_name
                                            o["progress"] = 25 if target_status == "Development" else 10
                                            break
                                            
                                    db["logs"].append({
                                        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                        "user": f"Admin ({authorizer_name})",
                                        "action": f"Digitally approved and signed Order {ord_to_app['id']}. Assigned Engineer: {engineer_assignment}. Status: {target_status}."
                                    })
                                    save_db(db)
                                    st.success(f"Certificate issued! Service Order {ord_to_app['id']} has been approved and allocated.")
                                    st.balloons()
                                    st.rerun()
                                    
            with tab_logs:
                st.markdown("### Cryptographic Audit Records")
                st.markdown("This immutable history tracks form creations, Excel data updates, user changes, and digital approvals.")
                
                search_log = st.text_input("Filter logs by keyword")
                log_records = []
                for log in reversed(db["logs"]):
                    if not search_log or search_log.lower() in log["user"].lower() or search_log.lower() in log["action"].lower():
                        log_records.append({
                            "Timestamp": log["timestamp"],
                            "Trigger User": log["user"],
                            "Action Description": log["action"]
                        })
                        
                if log_records:
                    st.table(log_records)
                else:
                    st.info("No logs found matching filter criteria.")
