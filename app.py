# Set up ngrok (for running Streamlit online)
from pyngrok import ngrok

# Kill previous tunnels if any
ngrok.kill()

# Set your Streamlit app port
port = 8501

# Create a public URL
public_url = ngrok.connect(port).public_url
print("Public URL:", public_url)

# --- STREAMLIT APP CODE ---

import streamlit as st
import pandas as pd
import random
import datetime

st.title("📅 Automated Shift Rota Generator")

st.sidebar.header("Rota Settings")
month = st.sidebar.selectbox("Select Month", [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
])
year = st.sidebar.number_input("Enter Year", 2025, 2100, 2025)
num_employees = st.sidebar.number_input("Number of Employees", 1, 50, 9)
shifts = ["M", "E", "N", "O"]

st.sidebar.write("Upload Employee List (Optional)")
uploaded_file = st.sidebar.file_uploader("Upload Excel/CSV file", type=["xlsx","csv"])

if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    employees = df.iloc[:,0].tolist()
else:
    employees = [f"Emp{i+1}" for i in range(num_employees)]

st.write(f"### Generating Rota for **{month} {year}**")
st.write(f"Employees: {', '.join(employees)}")

# Generate Rota
days_in_month = (datetime.date(year, list(datetime.date(1900, 1, 1).strftime('%B') for _ in range(12)).index(month)+2, 1) - datetime.timedelta(days=1)).day
rota = pd.DataFrame(index=employees, columns=[f"{i+1}" for i in range(days_in_month)])

for emp in employees:
    for day in rota.columns:
        rota.loc[emp, day] = random.choice(shifts)

st.dataframe(rota)

# Download Excel
if st.button("📥 Download Rota as Excel"):
    rota.to_excel("Generated_Rota.xlsx")
    with open("Generated_Rota.xlsx", "rb") as f:
        st.download_button("Download File", f, file_name="Rota.xlsx")
