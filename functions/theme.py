import streamlit as st

THEME_ORANGE = "#F05A28"
THEME_BLACK = "#17191C"
THEME_GREY = "#454B52"
THEME_LIGHT_GREY = "#EEF0F2"
THEME_WHITE = "#FFFFFF"

def apply_custom_theme():
    """Injects custom CSS adhering to the Automotive Orange & Charcoal theme."""
    st.markdown(
        f"""
        <style>
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
        }}
        
        h1, h2, h3 {{
            color: {THEME_BLACK} !important;
            font-weight: 700 !important;
        }}

        .stButton > button {{
            background-color: {THEME_ORANGE} !important;
            color: {THEME_WHITE} !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.25s ease-in-out !important;
        }}
        .stButton > button:hover {{
            background-color: {THEME_BLACK} !important;
            color: {THEME_WHITE} !important;
            box-shadow: 0 4px 12px rgba(240, 90, 40, 0.35) !important;
        }}

        .stDownloadButton > button {{
            background-color: {THEME_BLACK} !important;
            color: {THEME_WHITE} !important;
            border: 1px solid {THEME_ORANGE} !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }}
        .stDownloadButton > button:hover {{
            background-color: {THEME_ORANGE} !important;
            color: {THEME_WHITE} !important;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 6px;
            background-color: {THEME_LIGHT_GREY};
            padding: 6px;
            border-radius: 10px;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 6px;
            color: {THEME_GREY};
            font-weight: 600;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {THEME_ORANGE} !important;
            color: {THEME_WHITE} !important;
        }}

        [data-testid="stMetric"] {{
            background-color: {THEME_LIGHT_GREY};
            border-left: 4px solid {THEME_ORANGE};
            padding: 12px 16px;
            border-radius: 8px;
        }}
        [data-testid="stMetricValue"] {{
            color: {THEME_ORANGE} !important;
            font-weight: 800 !important;
        }}
        [data-testid="stMetricLabel"] {{
            color: {THEME_GREY} !important;
            font-weight: 600 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )