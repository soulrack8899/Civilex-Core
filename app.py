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
# 📂 FILE MANAGER LOGIC (SMART SORTING)
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
    """Creates a new project folder with AUTOMATIC TENDER SORTING."""
    clean_name = "".join([c for c in name if c.isalnum() or c in " -_"]).strip()
    path = os.path.join(PROJECTS_ROOT, clean_name)
    
    if not os.path.exists(path):
        # 1. Contract Administration Folders
        os.makedirs(f"{path}/Incoming_Letters")
        os.makedirs(f"{path}/Outgoing_Drafts")
        os.makedirs(f"{path}/Contracts")
        
        # 2. Tender & Estimating Folders (New)
        os.makedirs(f"{path}/Tenders/01_BQ_Documents")
        os.makedirs(f"{path}/Tenders/02_Supplier_Quotes")
        os.makedirs(f"{path}/Tenders/03_Cost_Analysis")
        os.makedirs(f"{path}/Tenders/04_Final_Submission")
        return True
    return False

def save_to_project(project_name, file_bytes, file_name, subfolder):
    """Saves binary files (PDFs) to the correct subfolder."""
    # Ensure subfolder exists even if created manually
    full_folder_path = os.path.join(PROJECTS_ROOT, project_name, subfolder)
    if not os.path.exists(full_folder_path):
        os.makedirs(full_folder_path)
        
    save_path = os.path.join(full_folder_path, file_name)
    with open(save_path, "wb") as f:
        f.write(file_bytes)
    return save_path

def save_text_to_project(project_name, text_content, file_name, subfolder):
    """Saves text/markdown files."""
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
    
    # --- PROJECT SELECTOR ---
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
        st.caption("Includes PWD, PAM, IEM, CIDB, FIDIC & JKR SOR Logic.")
    
    # MENU
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
model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")

# --- INTELLIGENT CONTEXT ---
MY_CONTEXT = """
STRICT LANGUAGE RULE: UK/Malaysian English spelling only (Programme, Labour, Defence, Cheque).
ROLE: Senior Consultant Quantity Surveyor (CQS) & Contract Manager in Malaysia.

MASTER KNOWLEDGE BASE (VERSIONS & AMENDMENTS) - DO NOT HALLUCINATE:

1. **PWD 75 (SARAWAK STATE):**
   - **Rev. 2006:** Legacy form (45 Clauses). Pre-CIPAA. Critical Risk: Clause 33 (Payment) may differ from statutory timelines.
   - **Rev. 2021:** Current form (53 Clauses). Post-CIPAA. Includes "Epidemic" in Clause 40 (EOT) and new Waiver clause (Cl. 52).

2. **PWD 203A (FEDERAL):**
   - **Rev. 2007:** Legacy (78 Clauses). 
   - **Rev. 1/2010:** Current (81 Clauses). Added clauses for Safety (Cl. 68) and Default.

3. **PAM CONTRACT:**
   - **2006:** Widespread in stalled/legacy projects.
   - **2018:** Current. Updates to Clause 30 (Certificates) and Clause 11 (Variations).

4. **CIDB FORMS:**
   - **2000 Edition:** Traditional adversarial approach.
   - **2022 Edition:** Collaborative approach. Introduces "Compensation Events" instead of just VOs.

5. **IEM FORMS:**
   - **1989:** Old Civil form (Modeled on old PWD).
   - **2011 (Civil) / 2012 (ME):** Modern engineering forms. Administered by "The Engineer".

6. **STATUTORY OVERRIDES (TOP PRIORITY):**
   - **HDA:** Residential projects must use Schedule G/H.
   - **CIPAA 2012:** Voids "Pay-When-Paid" in ALL construction contracts (Sec 35).
   - **Contracts Act 1950:** Sec 75 requires proof of actual loss for LAD.

INSTRUCTION: 
1. Identify the EXACT Version based on the text. 
2. Use the correct Administrator: "S.O." (JKR), "Architect" (PAM), "Engineer" (IEM/FIDIC), "P.D." (Design & Build).
"""

# ==========================================
# MODULE 1: DOCUMENT SCANNER
# ==========================================
if menu == "📂 Document Scanner":
    st.title("📂 Forensic Contract Scanner")
    
    if current_project:
        st.caption(f"Saving scans to: {current_project}/Incoming_Letters/")
    
    uploaded_file = st.file_uploader("Drop PDF here", type=["pdf"])
    
    if "scan_report" not in st.session_state:
        st.session_state.scan_report = ""

    if uploaded_file:
        if st.button("🚀 Run Forensic Audit"):
            with st.spinner("🕵️ Detecting Contract Version (Legacy vs Current)..."):
                
                if current_project:
                    save_to_project(current_project, uploaded_file.getbuffer(), uploaded_file.name, "Incoming_Letters")
                
                with open("temp.pdf", "wb") as f: f.write(uploaded_file.getbuffer())
                sample_file = genai.upload_file(path="temp.pdf", display_name="Scan")
                while sample_file.state.name == "PROCESSING": time.sleep(1); sample_file = genai.get_file(sample_file.name)

                prompt = f"""
                {MY_CONTEXT}
                TASK: Forensic Audit of Uploaded Document.
                
                STEP 1: IDENTIFY FORM & YEAR
                - Matches PWD 75 2006 or 2021?
                - Matches CIDB 2000 or 2022?
                
                STEP 2: RISK CHECK
                - **Statutory Compliance:** If Pre-2014 form, warn about CIPAA.
                - **LAD:** Check for penalty issues.
                - **Termination:** Check clauses.
                
                OUTPUT:
                Professional Report. Quote specific clauses.
                """
                response = model.generate_content([sample_file, prompt])
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
    
    if not current_project:
        st.info("💡 Tip: Create a Project in the sidebar to auto-save your letters.")

    col1, col2 = st.columns([1,1])
    with col1:
        uploaded_file = st.file_uploader("Incoming Letter (PDF)", type=["pdf"])
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
            
            if uploaded_file and current_project:
                save_to_project(current_project, uploaded_file.getbuffer(), uploaded_file.name, "Incoming_Letters")
            
            prompt_text = f"""
            {MY_CONTEXT}
            TASK: Draft a formal contractual letter.
            CONTEXT: The project is governed by {contract_type}.
            FROM: {sender_role} TO: {recipient}
            GOAL: {goal}
            GUIDANCE: Use correct administrator title. Reference relevant clauses.
            """
            inputs = [prompt_text]
            if uploaded_file:
                with open("temp.pdf", "wb") as f: f.write(uploaded_file.getbuffer())
                sample_file = genai.upload_file(path="temp.pdf", display_name="Context")
                while sample_file.state.name == "PROCESSING": time.sleep(1); sample_file = genai.get_file(sample_file.name)
                inputs.insert(0, sample_file)

            response = model.generate_content(inputs)
            
            if current_project:
                filename = f"Draft_{int(time.time())}.txt"
                save_text_to_project(current_project, response.text, filename, "Outgoing_Drafts")
                st.success(f"✅ Saved to {current_project}/Outgoing_Drafts/")

            st.markdown("---")
            st.subheader("✉️ Draft")
            st.text_area("Copy:", value=response.text, height=400)
            
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
            
            # PDF
            pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=10)
            clean_text = response.text.replace("**", "").encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, clean_text)
            b64 = base64.b64encode(pdf.output(dest='S').encode('latin-1')).decode()
            st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="{doc_type}.pdf"><b>📥 Download PDF</b></a>', unsafe_allow_html=True)

# ==========================================
# MODULE 4: SMART ESTIMATOR (TENDER INTELLIGENCE)
# ==========================================
elif menu == "💰 Smart Estimator (Pre-Contract)":
    st.title("💰 Smart Tender Estimator")
    st.markdown("### JKR Rate Comparison & Profit Prediction")
    
    if not current_project:
        st.error("⚠️ Please Select a Project first.")
        st.info("Estimates will be saved to 'Tenders/03_Cost_Analysis'.")
        st.stop()
    
    # FOLDER MANAGEMENT
    st.success(f"📂 Project: {current_project}")

    col1, col2 = st.columns(2)
    with col1:
        bq_file = st.file_uploader("1. Upload Scanned BQ Page (PDF)", type=["pdf"])
    with col2:
        # THE LEARNING INPUT
        sor_file = st.file_uploader("2. Upload JKR SOR 2024 (Reference)", type=["pdf"])
        
    st.info("💡 **How it works:** The AI reads your BQ, cross-references items with the uploaded **JKR SOR 2024**, and calculates the variance.")
    
    if bq_file and st.button("🚀 Analyze & Estimate"):
        with st.spinner("Reading BQ & Comparing against JKR SOR 2024..."):
            
            # 1. SAVE FILES TO TENDER FOLDER
            bq_path = save_to_project(current_project, bq_file.getbuffer(), "BQ_Scan.pdf", "Tenders/01_BQ_Documents")
            
            files_to_process = []
            
            # Upload BQ
            sample_bq = genai.upload_file(path=bq_path, display_name="BQ")
            files_to_process.append(sample_bq)
            
            # Upload SOR if provided
            if sor_file:
                sor_path = save_to_project(current_project, sor_file.getbuffer(), "JKR_SOR_2024.pdf", "Tenders/02_Supplier_Quotes")
                sample_sor = genai.upload_file(path=sor_path, display_name="SOR")
                files_to_process.append(sample_sor)
                sor_instruction = "REFERENCE: Use the rates found in the uploaded 'JKR SOR 2024' PDF as the exact benchmark."
            else:
                sor_instruction = "REFERENCE: Use your internal knowledge of JKR Sarawak 2024 rates (approximate)."

            # Wait for processing
            for f in files_to_process:
                while f.state.name == "PROCESSING": time.sleep(1); f = genai.get_file(f.name)

            # 2. PROMPT FOR ESTIMATION
            prompt = f"""
            You are a Senior Estimator in Sarawak. 
            
            INPUTS:
            1. A BQ Page (Bill of Quantities).
            2. JKR Sarawak Schedule of Rates 2024 (SOR) - if provided.
            
            {sor_instruction}
            
            TASK:
            1. EXTRACT items from the BQ.
            2. MATCH each item to the JKR SOR Rate (from the reference PDF).
            3. ESTIMATE 'Actual Market Cost' (Concrete, Steel, Labour in Kuching/Sarawak).
            4. CALCULATE VARIANCE: (JKR Rate - Market Cost).
            
            OUTPUT FORMAT (Markdown Table):
            | Item Description | Unit | Qty | JKR Rate (RM) | Market Cost (RM) | Margin/Loss |
            
            ANALYSIS:
            - Highlight any items where JKR Rate < Market Cost (Loss Makers).
            - Suggest a 'Tender Strategy' (e.g., Front-load items, or negotiate supplier rates).
            """
            
            response = model.generate_content(files_to_process + [prompt])
            
            st.markdown("---")
            st.subheader("📊 Cost & Profit Analysis")
            st.markdown(response.text)
            
            # 3. SAVE ESTIMATE
            save_text_to_project(current_project, response.text, "Cost_Analysis.md", "Tenders/03_Cost_Analysis")
            st.success(f"✅ Analysis saved to {current_project}/Tenders/03_Cost_Analysis/")