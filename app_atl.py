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
import numpy as np

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
        "Storage file 2026.xlsx",
        sheet_name=0
    )

    # =====================================================
    # TEST HISTORY DATABASE
    # =====================================================
    test_df = pd.read_excel(
        "Storage file 2026.xlsx",
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
        'Date of birth': 'Date of birth',
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
    if 'Date of birth' in df.columns:
        df['Date of birth'] = pd.to_datetime(
            df['Date of birth'],
            errors='coerce',
            dayfirst=True
        ).dt.strftime('%Y-%m-%d')
        

    if 'Monitoring_Start' in df.columns:
        df['Monitoring_Start'] = pd.to_datetime(
            df['Monitoring_Start'],
            errors='coerce',
            dayfirst=True
        ).dt.strftime('%Y-%m-%d')

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
    "VALD - ForceFrame"
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
    st.subheader("🏋️ VALD Test History (Strength)")

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

    # =====================================================
    # CHECK DATA
    # =====================================================
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
        # ATHLETE SUMMARY
        # =====================================================
        n_tests = athlete_tests[exercise_col].nunique()

        first_test = athlete_tests[date_col].min()

        last_test = athlete_tests[date_col].max()

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "Unique Tests",
                n_tests
            )

        with c2:
            st.metric(
                "First Test",
                first_test.strftime('%Y-%m-%d')
                if pd.notnull(first_test)
                else "-"
            )

        with c3:
            st.metric(
                "Last Test",
                last_test.strftime('%Y-%m-%d')
                if pd.notnull(last_test)
                else "-"
            )

        # =====================================================
        # BASE TABLE
        # =====================================================
        display_df = athlete_tests[(athlete_tests[exercise_col].notna())
        &(athlete_tests[left_col].notna()|athlete_tests[right_col].notna())
        ][
        [
            date_col,exercise_col,left_col,right_col]].copy()

        display_df = display_df.rename(columns={
            date_col: 'Date',
            exercise_col: 'Exercise',
            left_col: 'Left Strength',
            right_col: 'Right Strength'
        })

        # Clean exercise names
        display_df['Exercise'] = (
            display_df['Exercise']
            .astype(str)
            .str.strip()
        )

        # =====================================================
        # DISPLAY TEST TABLE
        # =====================================================
        table_df = display_df.copy()

        table_df['Date'] = (
            table_df['Date']
            .dt.strftime('%d/%m/%Y')
        )

        st.markdown("### 📋 Test Results")

        st.dataframe(
            table_df.sort_values(
                by='Date',
                ascending=False
            ),
            use_container_width=True
        )

        # =====================================================
        # PREPARE RATIO DATA
        # =====================================================
        plot_df = display_df.copy()

        # =====================================================
        # FUNCTION
        # =====================================================
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

        # =====================================================
        # EXERCISE TABLES
        # =====================================================
        er_df = get_strength(
            plot_df,
            'HIP ER ISO'
        )

        ir_df = get_strength(
            plot_df,
            'HIP IR ISO'
        )

        add_sup_df = get_strength(
            plot_df,
            'HIP ADD SUPINE (ANKLE) ISO'
        )

        abd_sup_df = get_strength(
            plot_df,
            'HIP ABD SUPINE (ANKLE) ISO'
        )

        add60_df = get_strength(
            plot_df,
            'HIP ADD 60° ISO'
        )

        abd60_df = get_strength(
            plot_df,
            'HIP ABD 60° ISO'
        )

        # =====================================================
        # MERGE TABLES
        # =====================================================
        ratio_table = er_df.copy()

        for df_merge in [
            ir_df,
            add_sup_df,
            abd_sup_df,
            add60_df,
            abd60_df
        ]:

            ratio_table = ratio_table.merge(
                df_merge,
                on='Date',
                how='outer'
            )

        # =====================================================
        # CALCULATE RATIOS
        # =====================================================
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

        # =====================================================
        # FINAL RATIO TABLE
        # =====================================================
        final_ratio_table = pd.DataFrame({

            'Date': (
                list(ratio_table['Date']) * 3
            ),

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
            .sort_values(by='Date')
        )

        final_ratio_table[['Left', 'Right']] = (
            final_ratio_table[['Left', 'Right']]
            .round(3)
        )

        # =====================================================
        # DISPLAY RATIO TABLE
        # =====================================================
        ratio_display = final_ratio_table.copy()

        ratio_display['Date'] = (
            ratio_display['Date']
            .dt.strftime('%d/%m/%Y')
        )

        st.markdown("### 📊 Strength Ratios")

        st.dataframe(
            ratio_display,
            use_container_width=True
        )

        # =====================================================
        # KPI BAR PLOTS
        # =====================================================
        st.markdown("### 📈 Ratio Progression")

        kpis = final_ratio_table[
            'KPI'
        ].dropna().unique()

        n_cols = 2

        for i in range(0, len(kpis), n_cols):

            cols = st.columns(n_cols)

            for j in range(n_cols):

                if i + j >= len(kpis):
                    continue

                kpi = kpis[i + j]

                kpi_df = final_ratio_table[
                    final_ratio_table['KPI'] == kpi
                ].sort_values('Date')

                if kpi_df.empty:
                    continue

                fig, ax = plt.subplots(
                    figsize=(4, 3)
                )

                x = np.arange(len(kpi_df))

                width = 0.35

                # LEFT
                ax.bar(
                    x - width / 2,
                    kpi_df['Left'],
                    width,
                    label='Left'
                )

                # RIGHT
                ax.bar(
                    x + width / 2,
                    kpi_df['Right'],
                    width,
                    label='Right'
                )

                # TITLE
                ax.set_title(
                    kpi,
                    fontsize=10
                )

                ax.set_ylabel("Ratio")

                # X AXIS
                ax.set_xticks(x)

                ax.set_xticklabels(
                    kpi_df['Date']
                    .dt.strftime('%d/%m/%Y'),
                    rotation=45,
                    ha='right',
                    fontsize=8
                )

                ax.tick_params(
                    axis='y',
                    labelsize=8
                )

                ax.legend(fontsize=8)

                ax.grid(axis='y')

                # VALUE LABELS
                for idx, val in enumerate(kpi_df['Left']):

                    ax.text(
                        idx - width / 2,
                        val,
                        f'{val:.2f}',
                        ha='center',
                        va='bottom',
                        fontsize=7
                    )

                for idx, val in enumerate(kpi_df['Right']):

                    ax.text(
                        idx + width / 2,
                        val,
                        f'{val:.2f}',
                        ha='center',
                        va='bottom',
                        fontsize=7
                    )

                with cols[j]:
                    st.pyplot(fig)

        # =====================================================
        # KPI DELTA SUMMARY
        # =====================================================
        st.markdown("### 📌 Delta % KPI Progress Summary (First date vs Last date)")

        summary_rows = []

        for kpi in final_ratio_table['KPI'].dropna().unique():

            kpi_df = final_ratio_table[
                final_ratio_table['KPI'] == kpi
            ].sort_values('Date')

            if len(kpi_df) < 2:
                continue

            # FIRST VALUES
            first_left = kpi_df.iloc[0]['Left']
            first_right = kpi_df.iloc[0]['Right']

            # LAST VALUES
            last_left = kpi_df.iloc[-1]['Left']
            last_right = kpi_df.iloc[-1]['Right']

            # DELTA %
            delta_left = (
                (last_left - first_left)
                / first_left * 100
                if first_left != 0
                else np.nan
            )

            delta_right = (
                (last_right - first_right)
                / first_right * 100
                if first_right != 0
                else np.nan
            )

            summary_rows.append({

                'KPI': kpi,

                'Delta % Left': round(
                    delta_left,
                    1
                ),

                'Delta % Right': round(
                    delta_right,
                    1
                )
            })

        summary_df = pd.DataFrame(
            summary_rows
        )

        st.dataframe(
            summary_df,
            use_container_width=True
        )

    else:
        st.info(
            "No test data available for this athlete."
        )
        
# =========================================================
# TAB 4 - KEISER TESTS
# =========================================================
with tab4:
    st.subheader("⚡ Keiser Test History (Power)")

    # =====================================================
    # COLUMN DETECTION
    # =====================================================
    name_col = [c for c in keiser_df.columns if 'Name' in c][0]

    date_col = [
        c for c in keiser_df.columns
        if c.endswith('Date')
    ][0]

    # SJ
    sj_load_col = [
        c for c in keiser_df.columns
        if 'SJ' in c and 'Load' in c
    ][0]

    sj_left_col = [
        c for c in keiser_df.columns
        if 'SJ' in c and 'Power L' in c
    ][0]

    sj_right_col = [
        c for c in keiser_df.columns
        if 'SJ' in c and 'Power R' in c
    ][0]

    # CMJ
    cmj_load_col = [
        c for c in keiser_df.columns
        if 'CMJ' in c and 'Load' in c
    ][0]

    cmj_left_col = [
        c for c in keiser_df.columns
        if 'CMJ' in c and 'Power L' in c
    ][0]

    cmj_right_col = [
        c for c in keiser_df.columns
        if 'CMJ' in c and 'Power R' in c
    ][0]

    # =====================================================
    # ATHLETE SELECTOR
    # =====================================================
    selected_keiser = st.selectbox(
        "Select Athlete",
        sorted(keiser_df[name_col].dropna().unique()),
        key="tab4_athlete"
    )

    # =====================================================
    # FILTER ATHLETE
    # =====================================================
    athlete_keiser = keiser_df[
        keiser_df[name_col] == selected_keiser
    ].copy()

    # =====================================================
    # CHECK DATA
    # =====================================================
    if not athlete_keiser.empty:

        # =====================================================
        # CLEAN DATA
        # =====================================================
        athlete_keiser[date_col] = pd.to_datetime(
            athlete_keiser[date_col],
            errors='coerce',
            dayfirst=True
        )

        numeric_cols = [
            sj_load_col,
            sj_left_col,
            sj_right_col,
            cmj_load_col,
            cmj_left_col,
            cmj_right_col
        ]

        for col in numeric_cols:

            athlete_keiser[col] = pd.to_numeric(
                athlete_keiser[col]
                .astype(str)
                .str.replace(',', '.'),
                errors='coerce'
            )

        # =====================================================
        # SUMMARY
        # =====================================================
        n_tests = athlete_keiser[date_col].nunique()

        first_test = athlete_keiser[date_col].min()

        last_test = athlete_keiser[date_col].max()

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "Number of Tests",
                n_tests
            )

        with c2:
            st.metric(
                "First Test",
                first_test.strftime('%Y-%m-%d')
                if pd.notnull(first_test)
                else "-"
            )

        with c3:
            st.metric(
                "Last Test",
                last_test.strftime('%Y-%m-%d')
                if pd.notnull(last_test)
                else "-"
            )

        # =====================================================
        # BASE TABLE
        # =====================================================
        keiser_display = athlete_keiser[
            [
                date_col,

                sj_load_col,
                sj_left_col,
                sj_right_col,

                cmj_load_col,
                cmj_left_col,
                cmj_right_col
            ]
        ].copy()

        keiser_display = keiser_display.rename(columns={

            date_col: 'Date',

            sj_load_col: 'SJ Load',
            sj_left_col: 'SJ Power Left',
            sj_right_col: 'SJ Power Right',

            cmj_load_col: 'CMJ Load',
            cmj_left_col: 'CMJ Power Left',
            cmj_right_col: 'CMJ Power Right'
        })

        # =====================================================
        # CALCULATE DELTAS
        # =====================================================
        keiser_display['SJ Delta %'] = (
            (
                keiser_display['SJ Power Left']
                - keiser_display['SJ Power Right']
            )
            /
            keiser_display[
                ['SJ Power Left', 'SJ Power Right']
            ].mean(axis=1)
        ) * 100

        keiser_display['CMJ Delta %'] = (
            (
                keiser_display['CMJ Power Left']
                - keiser_display['CMJ Power Right']
            )
            /
            keiser_display[
                ['CMJ Power Left', 'CMJ Power Right']
            ].mean(axis=1)
        ) * 100

        # =====================================================
        # DISPLAY TABLE
        # =====================================================
        display_table = keiser_display.copy()

        display_table['Date'] = (
            display_table['Date']
            .dt.strftime('%d/%m/%Y')
        )

        st.markdown("### 📋 Keiser Results")

        st.dataframe(
            display_table.sort_values(
                by='Date',
                ascending=False
            ),
            use_container_width=True
        )

        # =====================================================
        # KPI TABLE
        # =====================================================
        final_kpi_table = pd.DataFrame({

            'Date': (
                list(keiser_display['Date']) * 2
            ),

            'KPI': (
                ['SJ Power'] * len(keiser_display) +
                ['CMJ Power'] * len(keiser_display)
            ),

            'Left': (
                list(keiser_display['SJ Power Left']) +
                list(keiser_display['CMJ Power Left'])
            ),

            'Right': (
                list(keiser_display['SJ Power Right']) +
                list(keiser_display['CMJ Power Right'])
            )
        })

        final_kpi_table = (
            final_kpi_table
            .dropna(subset=['Left', 'Right'])
            .sort_values(by='Date')
        )

        # =====================================================
        # DISPLAY KPI TABLE
        # =====================================================
        kpi_display = final_kpi_table.copy()

        kpi_display['Date'] = (
            kpi_display['Date']
            .dt.strftime('%d/%m/%Y')
        )

        st.markdown("### 📊 Keiser KPI Table")

        st.dataframe(
            kpi_display,
            use_container_width=True
        )

        # =====================================================
        # BAR PLOTS
        # =====================================================
        st.markdown("### 📈 Keiser Progression")

        kpis = final_kpi_table[
            'KPI'
        ].dropna().unique()

        n_cols = 2

        for i in range(0, len(kpis), n_cols):

            cols = st.columns(n_cols)

            for j in range(n_cols):

                if i + j >= len(kpis):
                    continue

                kpi = kpis[i + j]

                kpi_df = final_kpi_table[
                    final_kpi_table['KPI'] == kpi
                ].sort_values('Date')

                if kpi_df.empty:
                    continue

                fig, ax = plt.subplots(
                    figsize=(4, 3)
                )

                x = np.arange(len(kpi_df))

                width = 0.35

                # LEFT
                ax.bar(
                    x - width / 2,
                    kpi_df['Left'],
                    width,
                    label='Left'
                )

                # RIGHT
                ax.bar(
                    x + width / 2,
                    kpi_df['Right'],
                    width,
                    label='Right'
                )

                ax.set_title(
                    kpi,
                    fontsize=10
                )

                ax.set_ylabel("Power")

                ax.set_xticks(x)

                ax.set_xticklabels(
                    kpi_df['Date']
                    .dt.strftime('%d/%m/%Y'),
                    rotation=45,
                    ha='right',
                    fontsize=8
                )

                ax.tick_params(
                    axis='y',
                    labelsize=8
                )

                ax.legend(fontsize=8)

                ax.grid(axis='y')

                # VALUES
                for idx, val in enumerate(kpi_df['Left']):

                    ax.text(
                        idx - width / 2,
                        val,
                        f'{val:.0f}',
                        ha='center',
                        va='bottom',
                        fontsize=7
                    )

                for idx, val in enumerate(kpi_df['Right']):

                    ax.text(
                        idx + width / 2,
                        val,
                        f'{val:.0f}',
                        ha='center',
                        va='bottom',
                        fontsize=7
                    )

                with cols[j]:
                    st.pyplot(fig)

        # =====================================================
        # DELTA SUMMARY
        # =====================================================
        st.markdown(
            "### 📌 Delta % Progress Summary"
        )

        summary_rows = []

        for kpi in final_kpi_table[
            'KPI'
        ].dropna().unique():

            kpi_df = final_kpi_table[
                final_kpi_table['KPI'] == kpi
            ].sort_values('Date')

            if len(kpi_df) < 2:
                continue

            first_left = kpi_df.iloc[0]['Left']
            first_right = kpi_df.iloc[0]['Right']

            last_left = kpi_df.iloc[-1]['Left']
            last_right = kpi_df.iloc[-1]['Right']

            delta_left = (
                (
                    last_left - first_left
                )
                / first_left * 100
                if first_left != 0
                else np.nan
            )

            delta_right = (
                (
                    last_right - first_right
                )
                / first_right * 100
                if first_right != 0
                else np.nan
            )

            summary_rows.append({

                'KPI': kpi,

                'Delta % Left': round(
                    delta_left,
                    1
                ),

                'Delta % Right': round(
                    delta_right,
                    1
                )
            })

        summary_df = pd.DataFrame(
            summary_rows
        )

        st.dataframe(
            summary_df,
            use_container_width=True
        )

    else:

        st.info(
            "No Keiser test data available for this athlete."
        )



# =========================================================
# FOOTER
# =========================================================
st.markdown('---')
st.caption('Developed with Streamlit • Athlete Monitoring System')



