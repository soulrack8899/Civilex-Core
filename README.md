🛡️ Civilex-Core | Master Contract Manager (Malaysia)

Civilex is a specialized Legal-Tech solution designed for the Malaysian construction industry. It functions as an intelligent "Contract Department in a Box" for Quantity Surveyors, Project Directors, and Contract Managers.

Powered by Google Gemini 2.5 Flash, Civilex provides forensic contract auditing, automated correspondence drafting, and legal document generation, strictly adhering to Malaysian Statutory Law and Standard Forms of Contract.

🏗️ Core Modules

1. 📂 Forensic Contract Scanner

Audit: Upload any PDF (Letter of Award, PWD Form, PAM Contract).

Verification: The AI identifies the specific Form of Contract (e.g., PWD 203A Rev 2010 vs Rev 2007) and cross-references clauses.

Risk Detection: Flags "Contract Killers" such as:

Missing LAD Caps (Section 75 Contracts Act 1950).

"Pay-When-Paid" clauses (Void under CIPAA 2012).

Unlimited Design Liability (in Design & Build forms).

2. ✍️ Correspondence & Defense Drafter

Context-Aware: Drafts letters from the perspective of Main Contractor, Sub-Contractor, or NSC.

Intelligent Routing: Automatically addresses the correct administrator based on the contract type:

"S.O." for JKR/PWD.

"Architect" for PAM/HDA.

"Engineer" for IEM/FIDIC.

"Project Director" for Design & Build.

3. 📝 Legal Document Generator

Instant Drafting: Generates standard legal templates in seconds:

Sub-Contract Letters of Award (Back-to-Back).

Deeds of Assignment (Direct Payment).

Notices of Determination / Default.

Compliance: Ensures all drafts align with the specific Governing Standard Form selected (e.g., drafting a PAM NSC Letter vs a PWD Domestic Sub-Con Letter).

📚 Knowledge Base (Malaysian Context)

Civilex is hard-coded with a Master Knowledge Base relevant to Sarawak and Federal projects:

Category

Supported Standards

Statutory

Contracts Act 1950, CIPAA 2012, Housing Development Act (HDA)

Government

PWD 75 (Sarawak Rev 2006/2021), PWD 203A (Federal Rev 2007/2010), PWD Design & Build

Private

PAM Contract (2006/2018), PAM NSC 2018, CIDB (2000/2022)

Engineering

IEM.CE 2011 (Civil), IEM.ME 2012 (Mech/Elec)

International

FIDIC Red Book, FIDIC Yellow Book

🛠️ Installation & Usage

Prerequisites

Install Python 3.10+

Obtain a Google Gemini API Key

Setup

Clone the repository:

git clone [https://github.com/soulrack8899/Civilex-Core.git](https://github.com/soulrack8899/Civilex-Core.git)


Install dependencies:

pip install -r requirements.txt


Run the application:

streamlit run app.py


🔒 Data Privacy

Local Execution: Civilex can run entirely on localhost. No data is stored on external servers unless explicitly configured.

M365 Integration: Compatible with OneDrive/SharePoint for secure, encrypted file storage and team synchronization.

Developed for the Advancement of the Malaysian Construction Industry.