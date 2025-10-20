import streamlit as st
import pandas as pd
from io import BytesIO

# Page setup
st.set_page_config(page_title="Shift Rota Generator", layout="wide")
st.title("Shift Rota Generator")

st.markdown("""
This app allows you to upload an Excel file with your employee list, generate a shift rota, 
and download it as an Excel file.  
""")

# Upload Excel
uploaded_file = st.file_uploader("Upload Employee List Excel", type=["xlsx"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("File uploaded successfully!")
        st.write("Preview of your data:")
        st.dataframe(df.head())

        # Generate Rota button
        if st.button("Generate Rota"):
            # Create a copy for rota
            rota = df.copy()

            # Assign shifts automatically
            shifts = ["Morning", "Evening", "Night"]
            rota['Shift'] = [shifts[i % len(shifts)] for i in range(len(df))]

            st.write("Generated Rota:")
            st.dataframe(rota)

            # Prepare for download
            output = BytesIO()
            rota.to_excel(output, index=False)
            output.seek(0)

            st.download_button(
                label="Download Rota Excel",
                data=output,
                file_name="generated_rota.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"Error reading the Excel file: {e}")
else:
    st.info("Please upload an Excel file to get started.")
