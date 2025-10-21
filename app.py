import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import math
import random

st.set_page_config(page_title="Shift Rota Generator (Production)", layout="wide")
st.title("Shift Rota Generator — Production Ready")

st.markdown("""
**Features**
- Employees in rows, dates in columns  
- Shifts: Morning, Afternoon, Night  
- Prevents Night → Morning consecutive assignment  
- Staggered or Same-weekday weekly offs (configurable)  
- Max employees per shift (configurable)  
- Balances shift distribution across employees  
""")

# Upload
uploaded_file = st.file_uploader("Upload Employee List Excel (names in first column)", type=["xlsx"])
if not uploaded_file:
    st.info("Please upload an Excel file with employee names in the first column.")
    st.stop()

try:
    df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Error reading Excel: {e}")
    st.stop()

if df.empty:
    st.error("Uploaded file is empty.")
    st.stop()

employees = df.iloc[:, 0].astype(str).tolist()
num_employees = len(employees)
st.write(f"Detected **{num_employees}** employees. Preview:")
st.dataframe(pd.DataFrame({"Employee": employees}).head(20))

# Config UI
col1, col2, col3 = st.columns(3)
with col1:
    num_days = st.number_input("Number of days to generate rota", min_value=1, value=30, step=1)
    start_date = st.date_input("Start date", value=datetime.today().date())
with col2:
    max_per_shift = st.number_input("Max employees per shift (per day)", min_value=1, value=max(1, math.ceil(num_employees/3)), step=1)
with col3:
    seed = st.number_input("Random seed (for reproducible stagger)", value=42, step=1)

st.markdown("**Weekly Off Options**")
wo_col1, wo_col2 = st.columns([2,3])
with wo_col1:
    wo_mode = st.radio("Weekly off mode", options=["Staggered (recommended)", "Same weekday(s) for all"])
with wo_col2:
    if wo_mode == "Same weekday(s) for all":
        weekdays = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        selected_weekdays = st.multiselect("Choose weekday(s) that are weekly off for everyone", options=weekdays, default=["Saturday","Sunday"])
    else:
        selected_weekdays = []

st.markdown("**Advanced options**")
adv_col1, adv_col2 = st.columns(2)
with adv_col1:
    avoid_night_to_morning = st.checkbox("Avoid Night → Morning next day", value=True)
with adv_col2:
    show_stats = st.checkbox("Show per-employee shift counts after generation", value=True)

if st.button("Generate Rota"):
    random.seed(int(seed))
    shifts = ["Morning", "Afternoon", "Night"]
    dates = [start_date + timedelta(days=i) for i in range(num_days)]
    date_cols = [d.strftime("%Y-%m-%d") for d in dates]

    # 1) Compute weekly off schedule: dict emp -> set(day_index)
    weekly_off_schedule = {emp: set() for emp in employees}
    if wo_mode == "Same weekday(s) for all" and selected_weekdays:
        # Map weekday name to index: Monday=0 ... Sunday=6
        name_to_idx = {n:i for i,n in enumerate(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])}
        selected_idxs = {name_to_idx[n] for n in selected_weekdays}
        for di, d in enumerate(dates):
            if d.weekday() in selected_idxs:
                for emp in employees:
                    weekly_off_schedule[emp].add(di)
    else:
        # Staggered: distribute weekly off slots across employees for each week block
        # For each week starting at week_start, assign each employee an off_day within that week in round-robin style
        for week_start in range(0, num_days, 7):
            week_len = min(7, num_days - week_start)
            # random offset to vary pattern between months/weeks
            offset = random.randint(0, week_len - 1)
            for idx, emp in enumerate(employees):
                # position within week: (offset + idx) % week_len
                off_day = week_start + ((offset + idx) % week_len)
                if off_day < num_days:
                    weekly_off_schedule[emp].add(off_day)

    # 2) Prepare tracking for balancing and continuity
    last_shift = {emp: None for emp in employees}
    shift_counts = {emp: {s: 0 for s in shifts} for emp in employees}
    total_assignments = {emp: 0 for emp in employees}

    # 3) For each day, assign up to max_per_shift employees per shift
    # result: mapping emp -> list of len=num_days with assigned shift or "Weekly Off" or "Unassigned"
    rota_assignments = {emp: [""] * num_days for emp in employees}

    # Precompute desired slots per day total
    total_slots_per_day = max_per_shift * len(shifts)

    warnings = []

    for day_index in range(num_days):
        # 3a) Build list of available employees this day (not weekly off)
        available = [emp for emp in employees if day_index not in weekly_off_schedule[emp]]
        random.shuffle(available)  # random tie-breaker but deterministic by seed

        if len(available) == 0:
            # everyone off this day (possible if same-weekdays chosen); fill with Weekly Off
            for emp in employees:
                rota_assignments[emp][day_index] = "Weekly Off"
            continue

        # 3b) For security, if available < total_slots_per_day, we will leave some slots unfilled.
        if len(available) < total_slots_per_day:
            warnings.append(f"Day {date_cols[day_index]}: only {len(available)} available for {total_slots_per_day} slots")

        # 3c) For assignment, we will fill shift by shift, selecting employees with minimal current count for that shift,
        # that are not already assigned this day, and respecting continuity rule.
        assigned_today = set()

        for shift in shifts:
            slots = max_per_shift
            candidates = [emp for emp in available if emp not in assigned_today]
            # Filter out those violating Night->Morning if applicable
            if avoid_night_to_morning and shift == "Morning":
                candidates = [emp for emp in candidates if last_shift[emp] != "Night"]

            # Sort candidates by (shift_counts[emp][shift], total_assignments[emp]) ascending to favor underworked employees
            candidates.sort(key=lambda e: (shift_counts[e][shift], total_assignments[e], random.random()))

            # Select up to slots
            selected = candidates[:slots]
            for emp in selected:
                rota_assignments[emp][day_index] = shift
                shift_counts[emp][shift] += 1
                total_assignments[emp] += 1
                assigned_today.add(emp)

        # 3d) Mark weekly off employees explicitly
        for emp in employees:
            if day_index in weekly_off_schedule[emp]:
                rota_assignments[emp][day_index] = "Weekly Off"

        # 3e) Any available employee not assigned and not weekly off
        for emp in employees:
            if rota_assignments[emp][day_index] == "":
                # they were available but not selected for any slot -> mark Unassigned
                if day_index not in weekly_off_schedule[emp]:
                    rota_assignments[emp][day_index] = "Unassigned"

        # 3f) Update last_shift for all employees (Weekly Off and Unassigned count as such)
        for emp in employees:
            rota_val = rota_assignments[emp][day_index]
            last_shift[emp] = rota_val if rota_val != "Unassigned" else last_shift[emp]

    # 4) Build DataFrame with employees as rows, dates as columns
    rota_df = pd.DataFrame({emp: rota_assignments[emp] for emp in employees}, index=date_cols).T
    rota_df.index.name = "Employee"

    # 5) Display and warnings
    st.write("### Generated Rota")
    st.dataframe(rota_df.style.set_properties(**{"white-space":"pre"}), height=600)

    if warnings:
        for w in warnings:
            st.warning(w)

    # 6) Show shift distribution stats optionally
    if show_stats:
        stats = []
        for emp in employees:
            stats.append({
                "Employee": emp,
                "Morning": shift_counts[emp]["Morning"],
                "Afternoon": shift_counts[emp]["Afternoon"],
                "Night": shift_counts[emp]["Night"],
                "TotalAssigned": total_assignments[emp],
                "WeeklyOffs": len(weekly_off_schedule[emp])
            })
        stats_df = pd.DataFrame(stats).sort_values("Employee")
        st.write("### Per-employee shift counts (summary)")
        st.dataframe(stats_df)

    # 7) Prepare Excel for download
    output = BytesIO()
    rota_df.to_excel(output)
    output.seek(0)
    st.download_button(
        label="Download Rota Excel",
        data=output,
        file_name="production_multi_day_rota.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

