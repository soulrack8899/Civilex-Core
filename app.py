import streamlit as st
import google.generativeai as genai
import time
from fpdf import FPDF
import base64
import os
import pandas as pd 

# --- PAGE SETUP ---
st.set_page_config(page_title="Civilex | Master Contract & Tender Manager", page_icon="🛡️", layout="wide")

# --- PDF CLASS ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Civilex AI - Professional Document', 0, 1, 'C')
        self.line(10, 20, 200, 20)
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

# --- AUTHENTICATION ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Google API Key", type="password")

# ==========================================
# 📂 FILE MANAGER LOGIC
# ==========================================
onedrive_path = os.environ.get("OneDrive") 
if onedrive_path:
    PROJECTS_ROOT = os.path.join(onedrive_path, "Civilex_Projects")
    STORAGE_MODE = "☁️ OneDrive (Synced)"
else:
    PROJECTS_ROOT = "Civil_Projects"
    STORAGE_MODE = "💻 Local Storage"

def get_projects():
    if not os.path.exists(PROJECTS_ROOT):
        os.makedirs(PROJECTS_ROOT)
    return [f.name for f in os.scandir(PROJECTS_ROOT) if f.is_dir()]

def create_project_folder(name):
    clean_name = "".join([c for c in name if c.isalnum() or c in " -_"]).strip()
    path = os.path.join(PROJECTS_ROOT, clean_name)
    
    if not os.path.exists(path):
        os.makedirs(f"{path}/Incoming_Letters")
        os.makedirs(f"{path}/Outgoing_Drafts")
        os.makedirs(f"{path}/Contracts")
        os.makedirs(f"{path}/Tenders/01_BQ_Documents")
        os.makedirs(f"{path}/Tenders/02_Supplier_Quotes")
        os.makedirs(f"{path}/Tenders/03_Cost_Analysis")
        return True
    return False

def save_to_project(project_name, file_bytes, file_name, subfolder):
    full_folder_path = os.path.join(PROJECTS_ROOT, project_name, subfolder)
    if not os.path.exists(full_folder_path):
        os.makedirs(full_folder_path)
    save_path = os.path.join(full_folder_path, file_name)
    with open(save_path, "wb") as f:
        f.write(file_bytes)
    return save_path

def save_text_to_project(project_name, text_content, file_name, subfolder):
    full_folder_path = os.path.join(PROJECTS_ROOT, project_name, subfolder)
    if not os.path.exists(full_folder_path):
        os.makedirs(full_folder_path)
    save_path = os.path.join(full_folder_path, file_name)
    with open(save_path, "w") as f:
        f.write(text_content)
    return save_path

# --- MASTER CONTRACT LIST ---
MASTER_CONTRACT_LIST = [
    "--- GOVERNMENT (SARAWAK) ---",
    "PWD 75 (Sarawak) - Rev 2021 (Current)",
    "PWD 75 (Sarawak) - Rev 2006 (Legacy)", 
    "--- GOVERNMENT (FEDERAL) ---",
    "PWD 203A (Federal) - Rev 1/2010 (Current)", 
    "PWD 203A (Federal) - Rev 2007 (Legacy)",
    "PWD 203 (Federal) - Lump Sum Rev 2010",
    "PWD Design & Build (DB) - Rev 2007",
    "PWD Form 203N (Nominated Sub-Con)",
    "PWD Form 203P (Nominated Supplier)",
    "--- PRIVATE SECTOR ---",
    "PAM Contract 2018 (With Quantities)",
    "PAM Contract 2018 (Without Quantities)",
    "PAM Contract 2006 (Legacy)",
    "PAM NSC 2018 (Nominated Sub-Con)",
    "CIDB Standard Form 2022 (Collaborative)",
    "CIDB Standard Form 2000 (Legacy)",
    "AIAC Standard Form 2019",
    "--- ENGINEERING ---",
    "IEM.CE 2011 (Civil Engineering)",
    "IEM.ME 2012 (Mech & Elec)",
    "IEM Form 1989 (Legacy Civil)",
    "--- INTERNATIONAL / SPECIAL ---",
    "FIDIC Red Book (Construction)",
    "FIDIC Yellow Book (Design-Build)",
    "HDA Schedule G (Landed Residential)",
    "HDA Schedule H (High-Rise Residential)"
]

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=50)
    st.title("Civilex Manager")
    st.caption(f"Storage: {STORAGE_MODE}")
    
    st.markdown("### 🏗️ Active Project")
    project_list = get_projects()
    proj_mode = st.radio("Mode:", ["Select Existing", "Create New"], horizontal=True, label_visibility="collapsed")
    
    current_project = None
    if proj_mode == "Create New":
        new_proj = st.text_input("New Project Name:")
        if st.button("Create Folder"):
            if new_proj:
                create_project_folder(new_proj)
                st.success(f"Created {new_proj}!")
                time.sleep(0.5)
                st.rerun()
    else:
        if project_list:
            current_project = st.selectbox("Select Project:", project_list)
            st.success(f"📂 Open: {current_project}")
        else:
            st.warning("No projects found. Create one!")

    st.markdown("---")
    with st.expander("📚 Master Library", expanded=False):
        st.caption("Includes all PWD, PAM, IEM, CIDB, FIDIC & HDA variations.")
    
    menu = st.radio("Select Module:", 
        ["📂 Document Scanner", 
         "✍️ Draft Reply/Defense", 
         "📝 Create Contract/Deed",
         "💰 Smart Estimator (Pre-Contract)"])
    
    st.markdown("---")

# --- MAIN APP LOGIC ---
if not api_key:
    st.warning("🔒 Key not found. Enter in sidebar.")
    st.stop()

genai.configure(api_key=api_key)

# USE STABLE 2.0 FLASH
model = genai.GenerativeModel(model_name="models/gemini-2.0-flash")

# --- INTELLIGENT CONTEXT ---
MY_CONTEXT = """
STRICT LANGUAGE RULE: UK/Malaysian English spelling only (Programme, Labour, Defence, Cheque).
ROLE: Senior Consultant Quantity Surveyor (CQS) & Contract Manager in Malaysia.
MASTER KNOWLEDGE BASE (VERSIONS & AMENDMENTS) - DO NOT HALLUCINATE:
1. **PWD 75 (SARAWAK STATE):** Rev 2006 (Legacy), Rev 2021 (Current/Covid Clauses).
2. **PWD 203A (FEDERAL):** Rev 2007 (Legacy), Rev 1/2010 (Current).
3. **PAM CONTRACT:** 2006 (Legacy), 2018 (Current).
4. **CIDB FORMS:** 2000 (Adversarial), 2022 (Collaborative/Compensation Events).
5. **IEM FORMS:** 1989 (Old), 2011 (Civil), 2012 (ME).
6. **STATUTORY:** HDA (Residential), CIPAA 2012 (Payment), Contracts Act 1950.
INSTRUCTION: Identify the EXACT Version. Use correct Administrator.
"""

# ==========================================
# MODULE 1: DOCUMENT SCANNER
# ==========================================
if menu == "📂 Document Scanner":
    st.title("📂 Forensic Contract Scanner")
    if current_project: st.caption(f"Saving scans to: {current_project}/Incoming_Letters/")
    
    uploaded_file = st.file_uploader("Drop PDF here", type=["pdf"])
    if "scan_report" not in st.session_state: st.session_state.scan_report = ""

    if uploaded_file:
        if st.button("🚀 Run Forensic Audit"):
            with st.spinner("🕵️ Detecting Contract Version..."):
                if current_project: save_to_project(current_project, uploaded_file.getbuffer(), uploaded_file.name, "Incoming_Letters")
                with open("temp.pdf", "wb") as f: f.write(uploaded_file.getbuffer())
                
                # Force MIME type for stability
                sample_file = genai.upload_file(path="temp.pdf", display_name="Scan", mime_type="application/pdf")
                
                while sample_file.state.name == "PROCESSING": time.sleep(1); sample_file = genai.get_file(sample_file.name)

                prompt = f"{MY_CONTEXT}\n Forensic Audit. Identify Form & Year. Check LAD, Payment, Design Liability."
                
                # API FIX: Correct List Structure
                response = model.generate_content([prompt, sample_file])
                st.session_state.scan_report = response.text 
    
    if st.session_state.scan_report:
        st.markdown("---")
        st.markdown(st.session_state.scan_report)
        pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=10)
        clean_text = st.session_state.scan_report.replace("**", "").encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, clean_text)
        b64 = base64.b64encode(pdf.output(dest='S').encode('latin-1')).decode()
        st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Forensic_Report.pdf"><b>📥 Download Report as PDF</b></a>', unsafe_allow_html=True)

# ==========================================
# MODULE 2: DRAFT REPLY
# ==========================================
elif menu == "✍️ Draft Reply/Defense":
    st.title("✍️ Correspondence Drafter")
    if not current_project: st.info("💡 Tip: Create a Project in the sidebar to auto-save your letters.")
    col1, col2 = st.columns([1,1])
    with col1: uploaded_file = st.file_uploader("Incoming Letter (PDF)", type=["pdf"])
    with col2:
        sender_role = st.selectbox("From:", ["Sub-Contractor (to Main Con)", "Main Contractor (to Client)", "NSC", "Supplier"])
        contract_type = st.selectbox("Contract Version:", MASTER_CONTRACT_LIST)
        
        if "Design & Build" in contract_type: def_to = "The Project Director (P.D.)"
        elif "PWD" in contract_type: def_to = "The Superintending Officer (S.O.)"
        elif "PAM" in contract_type or "HDA" in contract_type: def_to = "The Architect"
        elif "IEM" in contract_type or "FIDIC" in contract_type: def_to = "The Engineer"
        else: def_to = "The Contract Administrator"
            
        recipient = st.text_input("To:", value=def_to)
        goal = st.text_area("Goal:", placeholder="e.g., Claim for EOT due to rain.")

    if st.button("Generate Letter"):
        with st.spinner("Drafting..."):
            prompt_text = f"{MY_CONTEXT}\n Draft Letter. Context: {contract_type}. From: {sender_role}. To: {recipient}. Goal: {goal}."
            
            api_payload = [prompt_text]
            
            if uploaded_file:
                if current_project: save_to_project(current_project, uploaded_file.getbuffer(), uploaded_file.name, "Incoming_Letters")
                with open("temp.pdf", "wb") as f: f.write(uploaded_file.getbuffer())
                sample_file = genai.upload_file(path="temp.pdf", display_name="Context", mime_type="application/pdf")
                while sample_file.state.name == "PROCESSING": time.sleep(1); sample_file = genai.get_file(sample_file.name)
                api_payload.append(sample_file)

            # API FIX: Correct List Structure
            response = model.generate_content(api_payload)
            
            if current_project: save_text_to_project(current_project, response.text, f"Draft_{int(time.time())}.txt", "Outgoing_Drafts")
            st.markdown("---")
            st.text_area("Result:", value=response.text, height=400)
            
            pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=10)
            clean_text = response.text.replace("**", "").encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, clean_text)
            b64 = base64.b64encode(pdf.output(dest='S').encode('latin-1')).decode()
            st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Draft_Letter.pdf"><b>📥 Download Letter as PDF</b></a>', unsafe_allow_html=True)

# ==========================================
# MODULE 3: CONTRACT CREATOR
# ==========================================
elif menu == "📝 Create Contract/Deed":
    st.title("📝 Legal Document Generator")
    col1, col2 = st.columns(2)
    with col1: base_contract = st.selectbox("1. Governing Standard:", MASTER_CONTRACT_LIST)     
    with col2: doc_type = st.selectbox("2. Document:", ["Sub-Contract LoA", "Deed of Assignment", "Notice of Assignment", "Notice of Determination"])
    
    with st.form("c_form"):
        c1, c2 = st.columns(2)
        with c1: project = st.text_input("Project"); my_comp = st.text_input("My Company")
        with c2: other = st.text_input("Counterparty"); val = st.text_input("Value")
        extra = st.text_area("Details:", value="Back-to-back basis.")
        sub = st.form_submit_button("🚀 Generate Document")
    
    if sub:
        with st.spinner("Drafting..."):
            prompt = f"{MY_CONTEXT}\n Draft {doc_type}. Base: {base_contract}. Project: {project}. Parties: {my_comp} vs {other}. Val: {val}. Terms: {extra}."
            response = model.generate_content(prompt)
            if current_project: save_text_to_project(current_project, response.text, f"{doc_type}.txt", "Contracts")
            st.markdown("---")
            st.text_area("Result:", value=response.text, height=500)
            
            pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=10)
            clean_text = response.text.replace("**", "").encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, clean_text)
            b64 = base64.b64encode(pdf.output(dest='S').encode('latin-1')).decode()
            st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="{doc_type}.pdf"><b>📥 Download PDF</b></a>', unsafe_allow_html=True)

# ==========================================
# MODULE 4: COMMERCIAL MANAGER (CASH FLOW)
# ==========================================
elif menu == "💰 Smart Estimator (Pre-Contract)": # You can rename this to "💰 Commercial Manager"
    st.title("💰 Commercial Manager & Cash Flow")
    st.caption("Combine Contract Clauses with Project Schedule to predict Cash Flow.")

    if not current_project:
        st.error("⚠️ Please Select a Project first.")
        st.stop()

    # --- TAB SETUP ---
    tab1, tab2, tab3 = st.tabs(["1. Extract Contract Terms", "2. Project Schedule", "3. Cash Flow Dashboard"])

    # --- GLOBAL VARIABLES FOR THIS SESSION ---
    if "comm_terms" not in st.session_state:
        st.session_state.comm_terms = {
            "payment_period": 30, # Default days
            "honor_cert_period": 14, # Default days
            "retention_percent": 10.0, # Default %
            "retention_limit": 5.0 # Default %
        }
    
    # --- TAB 1: AI CONTRACT SCANNER ---
    with tab1:
        st.subheader("Step 1: Define the 'Money Rules'")
        st.info("Upload the Contract/Tender Document to auto-extract payment terms.")
        
        contract_file = st.file_uploader("Upload Contract (PDF)", type=["pdf"], key="comm_pdf")
        
        col_a, col_b = st.columns(2)
        
        # Manual Override Inputs (Pre-filled by AI later)
        with col_a:
            p_period = st.number_input("Payment Period (Days)", value=st.session_state.comm_terms['payment_period'])
            h_period = st.number_input("Honouring Cert. Period (Days)", value=st.session_state.comm_terms['honor_cert_period'])
        with col_b:
            r_percent = st.number_input("Retention (%)", value=st.session_state.comm_terms['retention_percent'])
            r_limit = st.number_input("Limit of Retention (%)", value=st.session_state.comm_terms['retention_limit'])

        # AI TRIGGER
        if contract_file and st.button("🔍 AI: Extract Terms"):
            with st.spinner("Reading Contract Clauses..."):
                # Save and Upload
                with open("temp_contract.pdf", "wb") as f: f.write(contract_file.getbuffer())
                sample_file = genai.upload_file(path="temp_contract.pdf", display_name="Contract", mime_type="application/pdf")
                while sample_file.state.name == "PROCESSING": time.sleep(1); sample_file = genai.get_file(sample_file.name)

                # STRICT JSON PROMPT
                prompt = """
                Analyze the attached construction contract. Extract these 4 numerical values.
                Return ONLY a JSON string like this: {"payment_period": 30, "honor_cert_period": 14, "retention_percent": 10, "retention_limit": 5}
                Rules:
                1. 'Period of Honouring Certificates' (Architect to certify).
                2. 'Period of Payment' (Client to pay after cert).
                3. 'Retention Percentage'.
                4. 'Limit of Retention' (Percentage of Contract Sum).
                If not found, use standard PAM 2018 values.
                """
                response = model.generate_content([prompt, sample_file])
                
                try:
                    # Clean the response to get pure JSON
                    import json
                    json_str = response.text.replace("```json", "").replace("```", "").strip()
                    extracted = json.loads(json_str)
                    
                    # Update Session State
                    st.session_state.comm_terms.update(extracted)
                    st.success("✅ Terms Extracted! Go to 'Project Schedule' tab.")
                    st.rerun() # Refresh to update the number inputs
                except:
                    st.error("AI read the file but couldn't format the JSON perfectly. Please update the numbers manually above.")
                    st.write(response.text)

    # --- TAB 2: SCHEDULE (THE TIME DIMENSION) ---
    with tab2:
        st.subheader("Step 2: The Programme of Works")
        
        # Default Data
        if "schedule_df" not in st.session_state:
            data = {
                "Activity": ["Preliminaries", "Piling Works", "Substructure", "Superstructure (Frame)", "Architecture", "M&E First Fix"],
                "Start Date": [pd.to_datetime("2025-01-01"), pd.to_datetime("2025-02-01"), pd.to_datetime("2025-03-01"), pd.to_datetime("2025-04-01"), pd.to_datetime("2025-06-01"), pd.to_datetime("2025-05-01")],
                "End Date": [pd.to_datetime("2025-12-31"), pd.to_datetime("2025-02-28"), pd.to_datetime("2025-03-31"), pd.to_datetime("2025-06-30"), pd.to_datetime("2025-09-30"), pd.to_datetime("2025-08-30")],
                "Value (RM)": [150000, 300000, 250000, 800000, 600000, 400000]
            }
            st.session_state.schedule_df = pd.DataFrame(data)

        # Editable Table
        edited_df = st.data_editor(st.session_state.schedule_df, num_rows="dynamic", use_container_width=True)
        st.session_state.schedule_df = edited_df
        
        total_val = edited_df["Value (RM)"].sum()
        st.metric("Total Contract Value", f"RM {total_val:,.2f}")

    # --- TAB 3: CASH FLOW ENGINE ---
    with tab3:
        st.subheader("Step 3: Cash Flow Forecast")
        
        if st.button("🚀 Calculate Cash Flow"):
            # 1. GET VARIABLES
            df = st.session_state.schedule_df.copy()
            pay_lag = st.session_state.comm_terms['payment_period'] + st.session_state.comm_terms['honor_cert_period']
            ret_rate = st.session_state.comm_terms['retention_percent'] / 100
            
            # 2. LOGIC: Shift Dates based on Contract Terms
            # Convert dates to datetime objects just in case
            df['End Date'] = pd.to_datetime(df['End Date'])
            
            # Calculate The "Money Date" (When it actually hits bank)
            df['Cash In Date'] = df['End Date'] + pd.Timedelta(days=pay_lag)
            
            # Calculate Retention Deduction
            df['Gross Claim'] = df['Value (RM)']
            df['Retention'] = df['Gross Claim'] * ret_rate
            df['Net Cash In'] = df['Gross Claim'] - df['Retention']
            
            # 3. AGGREGATE BY MONTH
            df['Month'] = df['Cash In Date'].dt.to_period('M')
            cash_flow = df.groupby('Month')[['Net Cash In']].sum().reset_index()
            cash_flow['Month'] = cash_flow['Month'].astype(str)
            cash_flow['Cumulative Cash'] = cash_flow['Net Cash In'].cumsum()
            
            # 4. VISUALIZE
            st.bar_chart(cash_flow, x='Month', y='Net Cash In', color="#00FF00")
            
            st.write("### 📉 Cash Flow Table")
            st.dataframe(cash_flow)
            
            # 5. AI ADVISOR
            st.markdown("---")
            st.subheader("🤖 AI Commercial Advisor")
            st.write(f"**Analysis:** Based on your contract, you have a **{pay_lag}-day cash lag** on every claim.")
            if cash_flow['Net Cash In'].iloc[0] == 0:
                st.warning("⚠️ Warning: No cash inflow in the first month. Ensure you have bridge financing.")