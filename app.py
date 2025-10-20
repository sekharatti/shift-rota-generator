import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta

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
                date_cols = [d.strftime("%Y-%m-%d") for d in dates]

                # Initialize rota dictionary
                rota_dict = {emp: [] for emp in employees}

                # Pre-assign weekly offs randomly, 1 per employee per 7 days
                weekly_off_schedule = {emp: [] for emp in employees}
                for i, emp in enumerate(employees):
                    for week_start in range(0, num_days, 7):
                        off_day = week_start + i % min(7, len(employees))  # stagger offs
                        if off_day < num_days:
                            weekly_off_schedule[emp].append(off_day)

                # Assign shifts
                for day_index in range(num_days):
                    for i, emp in enumerate(employees):
                        if day_index in weekly_off_schedule[emp]:
                            rota_dict[emp].append("Weekly Off")
                        else:
                            # Rotate shifts evenly
                            shift = shifts[(day_index + i) % len(shifts)]
                            rota_dict[emp].append(shift)

                # Convert to DataFrame: rows=employees, columns=dates
                rota_df = pd.DataFrame(rota_dict, index=date_cols).T
                rota_df.index.name = "Employee"

                st.write("Generated Multi-Day Rota:")
                st.dataframe(rota_df)

                # Prepare download
                output = BytesIO()
                rota_df.to_excel(output)
                output.seek(0)
                st.download_button(
                    label="Download Rota Excel",
                    data=output,
                    file_name="multi_day_rota.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"Error reading the Excel file: {e}")
else:
    st.info("Please upload an Excel file to get started.")
