# app_atl.py

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
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
        sheet_name="Test history"
    )

    # =====================================================
    # CLEAN COLUMN NAMES
    # =====================================================
    df.columns = df.columns.str.strip()
    test_df.columns = test_df.columns.str.strip()

    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================
    df = df.drop_duplicates()
    test_df = test_df.drop_duplicates()

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
tab1, tab2 = st.tabs([
    "📊 Main Dashboard",
    "👤 Individual Profile Section"
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
# FOOTER
# =========================================================
st.markdown('---')
st.caption('Developed with Streamlit • Athlete Monitoring System')



