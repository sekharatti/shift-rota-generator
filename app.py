import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Shift Rota Generator", layout="wide")
st.title("Shift Rota Generator")

# Upload Excel
uploaded_file = st.file_uploader("Upload Employee List Excel", type=["xlsx"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("File uploaded successfully!")
        st.write("Preview of your data:")
        st.dataframe(df.head())

        # Button to generate rota
        if st.button("Generate Rota"):
            # Example: Just copying the data and adding dummy shifts
            rota = df.copy()
            rota['Shift'] = ["Morning", "Evening", "Night"] * (len(df)//3 + 1)
            rota = rota.head(len(df))  # match original length
            st.write("Generated Rota:")
            st.dataframe(rota)

            # Download rota as Excel
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

