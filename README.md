# 🛡️ Civilex-Core | Master Contract Manager (Malaysia)

**Civilex** is a specialized AI-powered Contract Management System designed for the Malaysian construction industry. Built for Quantity Surveyors (QS), Contract Managers, and Project Directors, it serves as a digital defense system against contractual disputes, payment delays, and compliance risks.

It utilizes **Google Gemini 2.5 Flash** to perform forensic contract audits, draft legal correspondence, and generate standard forms based on Malaysian statutory laws (CIPAA 2012, Contracts Act 1950) and standard forms (PWD, PAM, IEM, CIDB).

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![AI](https://img.shields.io/badge/AI-Gemini%20Flash-green)

---

## 🚀 Key Features

### 1. 📂 Forensic Contract Scanner
* **Audit & Risk Analysis:** Upload any PDF (Letter of Award, PWD Form, etc.) to identify "Contract Killers."
* **Legacy Awareness:** Distinguishes between **PWD 75 Rev 2006** (Pre-CIPAA) and **Rev 2021** (Post-Covid).
* **Risk Detection:** Flags missing LAD caps, "Pay-When-Paid" clauses (illegal under CIPAA), and vague termination clauses.

### 2. ✍️ Defense & Correspondence Drafter
* **Role-Based Drafting:** Drafts letters from the perspective of a Main Contractor, Sub-Contractor, or NSC.
* **"Ali Baba" Protection:** Specialized logic for Sub-Contractors writing to Main Contractors to demand direct payment or written instructions for VOs.
* **Context-Aware:** Automatically addresses the correct administrator (e.g., "Superintending Officer" for JKR, "Architect" for PAM, "Project Director" for DB).

### 3. 📝 Legal Document Generator
* **Instant Drafting:** Generates Deeds of Assignment, Notices of Determination, and Sub-Contract LoAs in seconds.
* **Standard Compliance:** Ensuring drafts adhere to the specific "Base Contract" selected (e.g., drafting a letter based on FIDIC Yellow Book rules vs PWD 203A rules).

### 4. 🏗️ Digital Project Filing (M365 Integration)
* **Local/
