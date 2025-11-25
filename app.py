import streamlit as st
import google.generativeai as genai
import time
from fpdf import FPDF
import base64
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="Civilex | Master Contract Manager", page_icon="🛡️", layout="wide")

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

# --- MASTER CONTRACT LIST (FULL & CONSISTENT) ---
# This list is used in ALL modules to ensure consistency.
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
    st.markdown("**Region:** Malaysia")
    
    with st.expander("📚 Library Scope", expanded=True):
        st.caption("Includes all PWD, PAM, IEM, CIDB, FIDIC & HDA variations.")
    
    st.markdown("---")
    menu = st.radio("Select Module:", ["📂 Document Scanner", "✍️ Draft Reply/Defense", "📝 Create Contract/Deed"])
    st.markdown("---")

# --- MAIN APP LOGIC ---

if not api_key:
    st.warning("🔒 Key not found.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")

# --- INTELLIGENT CONTEXT (LOCKED KNOWLEDGE BASE) ---
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
    st.markdown("### Upload Document")
    
    uploaded_file = st.file_uploader("Drop PDF here", type=["pdf"])
    
    # Session state to store report so it doesn't disappear
    if "scan_report" not in st.session_state:
        st.session_state.scan_report = ""

    if uploaded_file:
        if st.button("🚀 Run Forensic Audit"):
            with st.spinner("🕵️ Detecting Contract Version (Legacy vs Current)..."):
                with open("temp.pdf", "wb") as f: f.write(uploaded_file.getbuffer())
                sample_file = genai.upload_file(path="temp.pdf", display_name="Scan")
                while sample_file.state.name == "PROCESSING": time.sleep(1); sample_file = genai.get_file(sample_file.name)

                prompt = f"""
                {MY_CONTEXT}
                TASK: Forensic Audit of Uploaded Document.
                
                STEP 1: IDENTIFY FORM & YEAR
                - Matches PWD 75 2006 or 2021?
                - Matches CIDB 2000 or 2022?
                - Matches IEM 1989 or 2011?
                
                STEP 2: RISK CHECK
                - **Statutory Compliance:** If Pre-2014 form, warn about CIPAA.
                - **LAD:** Check for penalty issues.
                - **Termination:** Check clauses.
                
                OUTPUT:
                Professional Report. Quote specific clauses.
                """
                response = model.generate_content([sample_file, prompt])
                st.session_state.scan_report = response.text # Store it
    
    # DISPLAY REPORT & PDF BUTTON (RESTORED)
    if st.session_state.scan_report:
        st.markdown("---")
        st.markdown(st.session_state.scan_report)
        
        # PDF Generator for Scanner
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
    col1, col2 = st.columns([1,1])
    with col1:
        uploaded_file = st.file_uploader("Reference PDF (Incoming Letter)", type=["pdf"])
    with col2:
        sender_role = st.selectbox("From:", ["Main Contractor", "Domestic Sub-Con", "NSC", "Supplier"])
        
        # USING MASTER LIST
        contract_type = st.selectbox("Contract Version:", MASTER_CONTRACT_LIST)
        
        # INTELLIGENT RECIPIENT LOGIC
        if "Design & Build" in contract_type: def_to = "The Project Director (P.D.)"
        elif "PWD" in contract_type: def_to = "The Superintending Officer (S.O.)"
        elif "PAM" in contract_type or "HDA" in contract_type: def_to = "The Architect"
        elif "IEM" in contract_type or "FIDIC" in contract_type: def_to = "The Engineer"
        else: def_to = "The Contract Administrator"
            
        recipient = st.text_input("To:", value=def_to)
        goal = st.text_area("Goal:", placeholder="e.g., Claim for EOT under Clause 43 (PWD 75 2006).")

    if st.button("Generate Letter"):
        with st.spinner("Drafting..."):
            prompt_text = f"""
            {MY_CONTEXT}
            TASK: Draft a formal contractual letter.
            CONTEXT: The project is governed by {contract_type}.
            
            FROM: {sender_role} TO: {recipient}
            GOAL: {goal}
            
            GUIDANCE:
            - Use correct administrator title.
            - Reference relevant clauses for {contract_type} (Note specific version differences).
            """
            inputs = [prompt_text]
            if uploaded_file:
                with open("temp.pdf", "wb") as f: f.write(uploaded_file.getbuffer())
                sample_file = genai.upload_file(path="temp.pdf", display_name="Context")
                while sample_file.state.name == "PROCESSING": time.sleep(1); sample_file = genai.get_file(sample_file.name)
                inputs.insert(0, sample_file)

            response = model.generate_content(inputs)
            st.markdown("---")
            st.subheader("✉️ Draft")
            st.text_area("Copy:", value=response.text, height=400)
            
            # PDF Download for Letter
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
    with col1:
        # USING MASTER LIST
        base_contract = st.selectbox("1. Governing Standard Form:", MASTER_CONTRACT_LIST)
             
    with col2:
        doc_type = st.selectbox("2. Document to Create:", 
            ["Sub-Contract Letter of Award (Domestic)", 
             "Nominated Sub-Contract (NSC) Agreement",
             "Deed of Assignment (Direct Payment)", 
             "Notice of Assignment", 
             "Notice of Claim (EOT / L&E)",
             "Notice of Determination (Termination)",
             "Letter of Demand (Payment)"])
    
    st.markdown("---")
    
    # FORM FOR INPUTS
    with st.form("contract_form"):
        c1, c2 = st.columns(2)
        with c1:
            project = st.text_input("Project Name")
            my_company = st.text_input("My Company")
        with c2:
            other_party = st.text_input("Counterparty")
            amount = st.text_input("Value (RM)")
            
        extra_details = st.text_area("Specific Terms / Scope:", 
                                     value="Back-to-back basis. Retention 5%.")
        
        # THE MISSING BUTTON IS HERE
        submitted = st.form_submit_button("🚀 Generate Document")
    
    # OUTPUT LOGIC (OUTSIDE THE FORM)
    if submitted:
        with st.spinner(f"Drafting {doc_type} based on {base_contract}..."):
            prompt = f"""
            {MY_CONTEXT}
            TASK: Draft a {doc_type}.
            
            GOVERNING LAW: {base_contract}.
            
            DETAILS:
            - Project: {project}
            - Parties: {my_company} vs {other_party}
            - Value: {amount}
            - Scope: {extra_details}
            
            LEGAL CHECKS:
            - Ensure Contracts Act 1950 compliance.
            - If PWD 75 2006, modernization of payment terms required?
            - If CIDB 2022, use 'Compensation Event' terminology.
            - If IEM 1989, ensure updated arbitration references.
            """
            
            response = model.generate_content(prompt)
            st.markdown("---")
            st.subheader(f"📄 Draft: {doc_type}")
            st.text_area("Copy / Edit:", value=response.text, height=500)
            
            # PDF Download
            pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=10)
            clean_text = response.text.replace("**", "").encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, clean_text)
            b64 = base64.b64encode(pdf.output(dest='S').encode('latin-1')).decode()
            st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="{doc_type}.pdf"><b>📥 Download PDF</b></a>', unsafe_allow_html=True)