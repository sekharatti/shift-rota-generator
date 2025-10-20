import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import random

# Page setup
st.set_page_config(page_title="Shift Rota Generator", layout="wide")
st.title("Shift Rota Generator")

st.markdown("""
Upload an Excel file with your employee list and generate a multi-day shift rota automatically.  
**Layout:** Employee names in rows, dates in columns.  
- 3 shifts per day: Morning, Afternoon, Night  
- Weekly offs automatically assigned and staggered  
- Downloadable Excel file  
""")

# Upload Excel
uploaded_file = st.file_uploader("Upload Employee List Excel", type=["xlsx"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        if df.empty:
            st.error("Uploaded file is empty!")
        else:
            st.success("File uploaded successfully!")
            st.write("Preview of your data:")
            st.dataframe(df.head())

            # User input: Number of days
            num_days = st.number_input("Number of days to generate rota", min_value=1, value=30, step=1)

            if st.button("Generate Rota"):
                employees = df.iloc[:, 0].tolist()  # assume first column has employee names
                shifts = ["Morning", "Afternoon", "Night"]

                # Generate dates
                dates = [datetime.today().date() + timedelta(days=i) for i in range(num_days)]
                date
