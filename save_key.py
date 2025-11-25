import os

# 1. Ask for the key
key = input("Paste your Google API Key here: ")

# 2. Create the hidden .streamlit folder
folder_path = ".streamlit"
os.makedirs(folder_path, exist_ok=True)

# 3. Save the key into a secrets file
file_path = os.path.join(folder_path, "secrets.toml")
with open(file_path, "w") as f:
    f.write(f'GOOGLE_API_KEY = "{key}"')

print(f"\n✅ SUCCESS! Key saved in {file_path}")
print("You never have to paste it again.")
input("Press Enter to close...")