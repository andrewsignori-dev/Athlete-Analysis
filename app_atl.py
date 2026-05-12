# app_atl.py

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import altair as alt
from io import BytesIO
from fpdf import FPDF
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Athletes Monitoring Dashboard",
    layout="wide",
    page_icon="🏥"
)

st.title("Athletes Monitoring Dashboard")
#st.markdown("Track athlete health, rehabilitation, and monitoring status.")

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data
def load_data():

    # =====================================================
    # MAIN ATHLETE DATABASE
    # =====================================================
    df = pd.read_excel(
        "Storage file.xlsx",
        sheet_name=0
    )

    # =====================================================
    # TEST HISTORY DATABASE
    # =====================================================
    test_df = pd.read_excel(
        "Storage file.xlsx",
        sheet_name="Test history",
        header=[0,1,2]
    )
    
    test_df.columns = [
    '_'.join([str(i).strip() for i in col if 'Unnamed' not in str(i)])
    for col in test_df.columns]

    # =====================================================
    # CLEAN COLUMN NAMES
    # =====================================================
    df.columns = df.columns.str.strip()
    test_df.columns = test_df.columns.str.strip()

    # =====================================================
    # RENAME COLUMNS
    # =====================================================
    rename_dict = {
        'Date of birth': 'DOB',
        'Height (cm)': 'Height_cm',
        'Weight (kg)': 'Weight_kg',
        'Date start monitoring': 'Monitoring_Start'
    }

    df = df.rename(columns=rename_dict)

    # =====================================================
    # NUMERIC CLEANING
    # =====================================================
    numeric_cols = [
        'Height_cm',
        'Weight_kg',
        'BMI'
    ]

    for col in numeric_cols:

        if col in df.columns:

            df[col] = (
                df[col]
                .astype(str)
                .str.replace(',', '.', regex=False)
            )

            df[col] = pd.to_numeric(
                df[col],
                errors='coerce'
            )

    # =====================================================
    # DATE CLEANING
    # =====================================================
    if 'DOB' in df.columns:
        df['DOB'] = pd.to_datetime(
            df['DOB'],
            errors='coerce'
        )

    if 'Monitoring_Start' in df.columns:
        df['Monitoring_Start'] = pd.to_datetime(
            df['Monitoring_Start'],
            errors='coerce',
            dayfirst=True
        )

    # =====================================================
    # YES / NO CLEANING
    # =====================================================
    binary_cols = [
        'S&C',
        'Rehab'
    ]

    for col in binary_cols:

        if col in df.columns:
            df[col] = df[col].fillna('No')

    # =====================================================
    # TEST HISTORY CLEANING
    # =====================================================
    test_numeric_cols = [
        'Left Strength',
        'Right Strength'
    ]

    for col in test_numeric_cols:

        if col in test_df.columns:

            test_df[col] = (
                test_df[col]
                .astype(str)
                .str.replace(',', '.', regex=False)
            )

            test_df[col] = pd.to_numeric(
                test_df[col],
                errors='coerce'
            )

    # Clean test dates
    if 'Date' in test_df.columns:

        test_df['Date'] = pd.to_datetime(
            test_df['Date'],
            errors='coerce',
            dayfirst=True
        )

    return df, test_df


# =========================================================
# LOAD DATAFRAMES
# =========================================================
try:
    df, test_df = load_data()

except Exception as e:

    st.error(
        f"Error loading Excel file: {e}"
    )

    st.stop()
# =========================================================
# SIDEBAR FILTERS
# =========================================================
st.sidebar.header("🔎 Filters")

# Team filter
teams = sorted(df['Team'].dropna().unique())
selected_teams = st.sidebar.multiselect(
    "Select Team(s)",
    teams
)

# Gender filter
if 'Gender' in df.columns:
    genders = sorted(df['Gender'].dropna().unique())
    selected_gender = st.sidebar.multiselect(
        "Select Gender",
        genders
    )
else:
    selected_gender = []

# Status filter
statuses = sorted(df['Status'].dropna().unique())
selected_status = st.sidebar.multiselect(
    "Select Status",
    statuses
)

# Name filter
names = sorted(df['Name'].dropna().unique())
selected_names = st.sidebar.multiselect(
    "Select Athlete(s)",
    names
)

def bmi_category(bmi):
    if pd.isna(bmi):
        return "Unknown"
    elif bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"

# Create BMI category column
df['BMI_Category'] = df['BMI'].apply(bmi_category)

# Sidebar category selector
bmi_categories = [
    "Underweight",
    "Normal",
    "Overweight",
    "Obese"
]

selected_bmi_categories = st.sidebar.multiselect(
    "Select BMI Category",
    bmi_categories
)

# =========================================================
# APPLY FILTERS
# =========================================================
filtered_df = df.copy()

if selected_teams:
    filtered_df = filtered_df[
        filtered_df['Team'].isin(selected_teams)
    ]

if selected_gender:
    filtered_df = filtered_df[
        filtered_df['Gender'].isin(selected_gender)
    ]

if selected_status:
    filtered_df = filtered_df[
        filtered_df['Status'].isin(selected_status)
    ]

if selected_names:
    filtered_df = filtered_df[
        filtered_df['Name'].isin(selected_names)
    ]

# =========================================================
# KPI SECTION
# =========================================================
st.subheader("📊 Overview")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Athletes", len(filtered_df))

with col2:
    injured_count = len(filtered_df[filtered_df['Status'] == 'Injured'])
    st.metric("Injured", injured_count)

with col3:
    healthy_count = len(filtered_df[filtered_df['Status'] == 'Healthy'])
    st.metric("Healthy", healthy_count)

with col4:
    rehab_count = len(filtered_df[filtered_df['Rehab'] == 'Yes'])
    st.metric("In Rehab", rehab_count)

with col5:
    avg_bmi = round(filtered_df['BMI'].mean(), 2)
    st.metric("Average BMI", avg_bmi)

st.markdown('---')

# =========================================================
# DASHBOARD TABS
# =========================================================
tab1, tab2, tab3 = st.tabs([
    "📊 Main Dashboard",
    "👤 Individual Profile Section",
    "KPI"
])

# =========================================================
# TAB 1
# =========================================================
with tab1:

    # =========================================================
    # TABLE SECTION
    # =========================================================
    st.subheader("📋 Athletes Database")

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=500
    )

    # =========================================================
    # CHARTS
    # =========================================================
    colA, colB = st.columns(2)

    # ---------------------------------------------------------
    # STATUS DISTRIBUTION
    # ---------------------------------------------------------
    with colA:
        st.subheader("🏥 Status Distribution")

        status_counts = (
            filtered_df['Status']
            .value_counts()
            .reset_index()
        )

        status_counts.columns = ['Status', 'Count']

        fig_status = px.pie(
            status_counts,
            names='Status',
            values='Count',
            hole=0.4
        )

        st.plotly_chart(fig_status, use_container_width=True)

    # ---------------------------------------------------------
    # TEAM DISTRIBUTION
    # ---------------------------------------------------------
    with colB:
        st.subheader("🏅 Team Distribution")

        team_counts = (
            filtered_df['Team']
            .value_counts()
            .reset_index()
        )

        team_counts.columns = ['Team', 'Count']

        fig_team = px.bar(
            team_counts,
            x='Team',
            y='Count',
            text='Count'
        )

        st.plotly_chart(fig_team, use_container_width=True)

    # =========================================================
    # BMI ANALYSIS
    # =========================================================
    st.subheader("📈 BMI Analysis")

    fig_bmi = px.scatter(
        filtered_df,
        x='Height_cm',
        y='Weight_kg',
        size='BMI',
        color='Status',
        hover_data=['Name', 'Team'],
    )

    st.plotly_chart(fig_bmi, use_container_width=True)

    # =========================================================
    # ALTAIR CHART
    # =========================================================
    st.subheader("📊 BMI by Team")

    alt_chart = (
        alt.Chart(filtered_df)
        .mark_bar()
        .encode(
            x='Team:N',
            y='mean(BMI):Q',
            tooltip=['Team', 'mean(BMI)']
        )
        .properties(height=400)
    )

    st.altair_chart(alt_chart, use_container_width=True)

# =========================================================
# TAB 2
# =========================================================
with tab2:

    # =========================================================
    # ATHLETE PROFILE SECTION
    # =========================================================
    st.subheader("👤 Individual Athlete Profile")

    selected_profile = st.selectbox(
        "Select Athlete",
        filtered_df['Name'].unique()
    )

    profile_df = filtered_df[
        filtered_df['Name'] == selected_profile
    ]

    if not profile_df.empty:

        athlete = profile_df.iloc[0]

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Height (cm)", athlete['Height_cm'])
            st.metric("Weight (kg)", athlete['Weight_kg'])

        with c2:
            st.metric("BMI", round(athlete['BMI'], 0))
            st.metric("Gender", athlete['Gender'])

        with c3:
            st.metric("Status", athlete['Status'])
            st.metric("Rehab", athlete['Rehab'])

        st.markdown("### Notes")
        st.info(athlete['Notes'])
        
# =========================================================
# TAB 3
# =========================================================
with tab3:

    st.subheader("🏋️ Athlete Test History")

    # =====================================================
    # COLUMN DETECTION
    # =====================================================
    name_col = [c for c in test_df.columns if 'Name' in c][0]

    date_col = [
        c for c in test_df.columns
        if c.endswith('Date')
    ][0]

    exercise_col = [
        c for c in test_df.columns
        if 'Exercise name' in c
    ][0]

    left_col = [
        c for c in test_df.columns
        if 'Left Strength' in c
    ][0]

    right_col = [
        c for c in test_df.columns
        if 'Right Strength' in c
    ][0]

    # =====================================================
    # ATHLETE SELECTOR
    # =====================================================
    selected_profile = st.selectbox(
        "Select Athlete",
        sorted(test_df[name_col].dropna().unique()),
        key="tab3_athlete"
    )

    # =====================================================
    # FILTER ATHLETE
    # =====================================================
    athlete_tests = test_df[
        test_df[name_col] == selected_profile
    ].copy()

    if not athlete_tests.empty:

        # =====================================================
        # CLEAN DATA
        # =====================================================
        athlete_tests[date_col] = pd.to_datetime(
            athlete_tests[date_col],
            errors='coerce',
            dayfirst=True
        )

        athlete_tests[left_col] = pd.to_numeric(
            athlete_tests[left_col]
            .astype(str)
            .str.replace(',', '.'),
            errors='coerce'
        )

        athlete_tests[right_col] = pd.to_numeric(
            athlete_tests[right_col]
            .astype(str)
            .str.replace(',', '.'),
            errors='coerce'
        )

        # =====================================================
        # BASE TABLE
        # =====================================================
        display_df = athlete_tests[
            athlete_tests[exercise_col].notna()
        ][
            [
                date_col,
                exercise_col,
                left_col,
                right_col
            ]
        ].copy()

        display_df = display_df.rename(columns={
            date_col: 'Date',
            exercise_col: 'Exercise',
            left_col: 'Left Strength',
            right_col: 'Right Strength'
        })

        # Format date
        display_df['Date'] = display_df['Date'].dt.strftime('%d/%m/%Y')

        # =====================================================
        # DISPLAY TABLE
        # =====================================================
        st.markdown("### 📋 Test Results")

        st.dataframe(
            display_df.sort_values(
                by='Date',
                ascending=False
            ),
            use_container_width=True
        )

        # =====================================================
        # RATIO TABLE
        # =====================================================
        st.markdown("### 📊 Strength Ratios")

        plot_df = display_df.copy()

        plot_df['Date'] = pd.to_datetime(
            plot_df['Date'],
            dayfirst=True,
            errors='coerce'
        )

        # -----------------------------------------------------
        # FUNCTION
        # -----------------------------------------------------
        def get_strength(df, exercise_name):

            temp = df[
                df['Exercise'] == exercise_name
            ][
                ['Date', 'Left Strength', 'Right Strength']
            ].copy()

            temp = temp.rename(columns={
                'Left Strength': f'{exercise_name}_L',
                'Right Strength': f'{exercise_name}_R'
            })

            return temp

        # -----------------------------------------------------
        # EXERCISES
        # -----------------------------------------------------
        er_df = get_strength(plot_df, 'HIP ER ISO')
        ir_df = get_strength(plot_df, 'HIP IR ISO')

        add_sup_df = get_strength(
            plot_df,
            'HIP ADD SUPINE (ANKLE) ISO'
        )

        abb_sup_df = get_strength(
            plot_df,
            'HIP ABD SUPINE (ANKLE) ISO'
        )

        add60_df = get_strength(
            plot_df,
            'HIP ADD 60° ISO'
        )

        abb60_df = get_strength(
            plot_df,
            'HIP ABD 60° ISO'
        )

        # -----------------------------------------------------
        # MERGE
        # -----------------------------------------------------
        ratio_table = er_df.copy()

        for df_merge in [
            ir_df,
            add_sup_df,
            abb_sup_df,
            add60_df,
            abb60_df
        ]:
            ratio_table = ratio_table.merge(
                df_merge,
                on='Date',
                how='outer'
            )

        # -----------------------------------------------------
        # RATIOS
        # -----------------------------------------------------
        ratio_table['ER/IR Left'] = (
            ratio_table['HIP ER ISO_L'] /
            ratio_table['HIP IR ISO_L']
        )

        ratio_table['ER/IR Right'] = (
            ratio_table['HIP ER ISO_R'] /
            ratio_table['HIP IR ISO_R']
        )

        ratio_table['ADD/ABB SUPINE Left'] = (
            ratio_table['HIP ADD SUPINE (ANKLE) ISO_L'] /
            ratio_table['HIP ABD SUPINE (ANKLE) ISO_L']
        )

        ratio_table['ADD/ABB SUPINE Right'] = (
            ratio_table['HIP ADD SUPINE (ANKLE) ISO_R'] /
            ratio_table['HIP ABD SUPINE (ANKLE) ISO_R']
        )

        ratio_table['ADD/ABB 60 Left'] = (
            ratio_table['HIP ADD 60° ISO_L'] /
            ratio_table['HIP ABD 60° ISO_L']
        )

        ratio_table['ADD/ABB 60 Right'] = (
            ratio_table['HIP ADD 60° ISO_R'] /
            ratio_table['HIP ABD 60° ISO_R']
        )

        # -----------------------------------------------------
        # FINAL RATIO TABLE
        # -----------------------------------------------------
        final_ratio_table = pd.DataFrame({

            'Date': list(ratio_table['Date']) * 3,

            'KPI': (
                ['ER/IR'] * len(ratio_table) +
                ['ADD/ABB SUPINE'] * len(ratio_table) +
                ['ADD/ABB 60'] * len(ratio_table)
            ),

            'Left': (
                list(ratio_table['ER/IR Left']) +
                list(ratio_table['ADD/ABB SUPINE Left']) +
                list(ratio_table['ADD/ABB 60 Left'])
            ),

            'Right': (
                list(ratio_table['ER/IR Right']) +
                list(ratio_table['ADD/ABB SUPINE Right']) +
                list(ratio_table['ADD/ABB 60 Right'])
            )
        })

        final_ratio_table = (
            final_ratio_table
            .dropna(subset=['Left', 'Right'])
            .sort_values(by='Date', ascending=False)
        )

        final_ratio_table[['Left', 'Right']] = (
            final_ratio_table[['Left', 'Right']]
            .round(3)
        )

        final_ratio_table['Date'] = (
            final_ratio_table['Date']
            .dt.strftime('%d/%m/%Y')
        )

        # -----------------------------------------------------
        # DISPLAY RATIO TABLE
        # -----------------------------------------------------
        st.dataframe(
            final_ratio_table,
            use_container_width=True
        )

        # =====================================================
        # PLOTS
        # =====================================================
        st.markdown("### 📈 Strength Progression")

        plot_df['Date'] = pd.to_datetime(
            plot_df['Date'],
            dayfirst=True,
            errors='coerce'
        )

        for exercise in plot_df['Exercise'].unique():

            ex_df = plot_df[
                plot_df['Exercise'] == exercise
            ].sort_values('Date')

            if ex_df.empty:
                continue

            fig, ax = plt.subplots(figsize=(7,4))

            ax.plot(
                ex_df['Date'],
                ex_df['Left Strength'],
                marker='o',
                linewidth=2,
                label='Left Strength'
            )

            ax.plot(
                ex_df['Date'],
                ex_df['Right Strength'],
                marker='o',
                linewidth=2,
                label='Right Strength'
            )

            ax.set_title(exercise)
            ax.set_xlabel("Date")
            ax.set_ylabel("Strength")

            ax.legend()
            ax.grid(True)

            st.pyplot(fig)

    else:
        st.info("No test data available for this athlete.")
 
# =========================================================
# FOOTER
# =========================================================
st.markdown('---')
st.caption('Developed with Streamlit • Athlete Monitoring System')



