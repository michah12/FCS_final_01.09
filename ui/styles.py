"""
Styling Module - All CSS for Scentify App
Extracted from main file to keep code organized
"""
import streamlit as st


def apply_custom_styling():
    """Apply custom CSS styling"""
    st.markdown("""
        <style>
        /* Import Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap');
        
        /* Hover color fix */
        .logo-text,
        .logo-text:hover,
        .logo-tagline,
        .logo-tagline:hover,
        .section-title,
        .section-title:hover,
        .main-header,
        .main-header:hover {
            color: #6b5b95 !important;
        }
        
        .section-description,
        .section-description:hover {
            color: #666 !important;
        }
        
        .bipolar-label,
        .bipolar-label:hover {
            color: #6b5b95 !important;
        }
        
        .scale-numbers,
        .scale-numbers:hover,
        .scale-numbers *,
        .scale-numbers *:hover {
            color: #6b5b95 !important;
        }
        
        /* Main application background with subtle gradient */
        .stApp {
            background: linear-gradient(135deg, #faf9fc 0%, #f0eef5 100%);
            font-family: 'Poppins', sans-serif;
        }
        
        /* Add minimal floral background pattern */
        .stApp::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(200, 180, 220, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 90% 80%, rgba(200, 180, 220, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 50% 50%, rgba(200, 180, 220, 0.04) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }
        
        /* Main header styling */
        .main-header {
            font-size: 70px;
            font-weight: 600;
            color: #6b5b95 !important;
            text-align: center;
            margin-bottom: 10px;
            letter-spacing: 3px;
        }
        
        /* Section card styling for landing page */
        .section-card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin: 20px 0;
            border: 2px solid #e8e4f0;
            height: 250px;  /* Fixed height */
            min-height: 250px;
            max-height: 250px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;  /* Align all content to top */
            overflow: hidden;  /* Prevent content overflow */
        }
        
        /* Section title styling */
        .section-title {
            font-size: 28px;
            font-weight: 600;
            color: #6b5b95 !important;
            margin-bottom: 30px;  /* 30px spacing below title */
            text-align: center;
            height: 35px;  /* Fixed height for alignment */
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;  /* Prevent title from shrinking */
        }
        
        /* Section description styling */
        .section-description {
            font-size: 16px;
            color: #666 !important;
            margin-top: 0px;  /* No extra spacing (title handles the gap) */
            margin-bottom: 20px;
            line-height: 1.6;
            text-align: center;
            flex: 1;  /* Take remaining space */
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #6b5b95;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 30px;
            font-size: 16px;
            font-weight: 500;
            width: 100%;
            transition: transform 0.2s ease;
        }
        
        .stButton > button:hover {
            background-color: #6b5b95 !important;
            color: white !important;
            transform: scale(1.05) !important;
        }
        
        /* Prevent red outline/border on buttons and inputs */
        button:focus-visible,
        button:focus,
        input:focus-visible {
            outline: none !important;
        }
        
        /* Logo container styling - centered on page */
        .logo-container {
            cursor: pointer;
            display: block;
            text-align: center;
            margin: 0 auto 5px auto;
            width: 100%;
        }
        
        .logo-text {
            font-size: 70px;
            font-weight: 600;
            color: #6b5b95 !important;
            letter-spacing: 3px;
            text-align: center;
            user-select: none;
            display: block;
            width: 100%;
        }
        
        .logo-image {
            max-height: 80px;
            width: auto;
            display: block;
            margin: 0 auto;
        }
        
        /* Tagline styling below logo */
        .logo-tagline {
            font-family: 'Great Vibes', cursive;
            font-size: 24px;
            color: #6b5b95 !important;
            text-align: center;
            margin-top: 0px;
            margin-bottom: 10px;
            font-weight: 400;
            display: block;
            width: 100%;
        }
        
        /* Make sure equal column widths on landing page */
        .stColumn {
            min-width: 0;
            flex: 1 1 0px;
        }
        
        /* Responsive adjustments for smaller screens */
        @media (max-width: 768px) {
            .section-card {
                height: auto;
                min-height: 300px;
                max-height: none;
            }
            
            .main-header {
                font-size: 36px;
            }
        }
        
        /* Filter tag styling */
        .filter-tag {
            display: inline-block;
            background-color: #e8e4f0;
            color: #6b5b95;
            padding: 8px 16px;
            border-radius: 20px;
            margin: 5px;
            font-size: 14px;
            border: 1px solid #c8b8d8;
        }
        
        /* Perfume card styling */
        .perfume-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
            border: 2px solid #e8e4f0;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        
        /* Input field styling */
        .stTextInput > div > div > input {
            border-radius: 8px;
            border: 2px solid #e8e4f0;
            padding: 10px;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #6b5b95 !important;
            outline: none !important;
            box-shadow: none !important;
        }
        
        /* Remove red from ALL input and select elements */
        input:focus,
        input:active,
        textarea:focus,
        textarea:active,
        select:focus,
        select:active,
        .stSelectbox:focus,
        .stSelectbox:active,
        .stMultiSelect:focus,
        .stMultiSelect:active {
            border-color: #6b5b95 !important;
            outline: none !important;
            box-shadow: none !important;
            color: #6b5b95 !important;
        }
        
        /* Override Streamlit's default red focus colors */
        [data-baseweb="input"]:focus-within,
        [data-baseweb="select"]:focus-within {
            border-color: #6b5b95 !important;
            box-shadow: none !important;
        }
        
        /* Remove red from ALL interactive elements on hover/click/focus */
        button:focus,
        button:active,
        input:focus,
        input:active,
        textarea:focus,
        textarea:active,
        select:focus,
        select:active,
        summary:focus,
        summary:active,
        a:focus,
        a:active,
        [role="button"]:focus,
        [role="button"]:active {
            outline: none !important;
            box-shadow: none !important;
        }
        
        /* Keep borders purple instead of red */
        input:focus,
        textarea:focus,
        select:focus {
            border-color: #6b5b95 !important;
        }
        
        /* Target Streamlit's selectbox specifically */
        .stSelectbox > div > div,
        .stSelectbox > div > div:focus,
        .stSelectbox > div > div:focus-within,
        [data-baseweb="select"],
        [data-baseweb="select"]:focus,
        [data-baseweb="select"]:focus-within,
        [data-baseweb="select"] > div,
        [data-baseweb="select"] > div:focus {
            border-color: #6b5b95 !important;
            outline: none !important;
            box-shadow: none !important;
        }
        
        /* COMPLETELY DISABLE ALL TEXT COLOR CHANGES ON HOVER */
        p, span, div, label, h1, h2, h3, h4, h5, h6, summary, a, li, td, th, pre, code {
            transition: none !important;
        }
        
        /* Prevent expander header text from turning red */
        .streamlit-expanderHeader:hover,
        [data-testid="stExpander"] summary:hover {
            color: #6b5b95 !important;
        }
        
        /* Change dropdown arrow from red to purple - ULTRA AGGRESSIVE + HOVER */
        [data-baseweb="select"] svg,
        [data-baseweb="select"] svg *,
        [data-baseweb="select"] path,
        [data-baseweb="select"]:hover svg,
        [data-baseweb="select"]:hover svg *,
        [data-baseweb="select"]:hover path,
        .stSelectbox svg,
        .stSelectbox svg *,
        .stSelectbox path,
        .stSelectbox:hover svg,
        .stSelectbox:hover svg *,
        .stSelectbox:hover path,
        .stMultiSelect svg,
        .stMultiSelect svg *,
        .stMultiSelect path,
        .stMultiSelect:hover svg,
        .stMultiSelect:hover svg *,
        .stMultiSelect:hover path,
        [role="button"] svg,
        [role="button"] svg *,
        [role="button"] path,
        [role="button"]:hover svg,
        [role="button"]:hover svg *,
        [role="button"]:hover path,
        [aria-expanded] svg,
        [aria-expanded] svg *,
        [aria-expanded] path,
        [aria-expanded]:hover svg,
        [aria-expanded]:hover svg *,
        [aria-expanded]:hover path {
            color: #6b5b95 !important;
            fill: #6b5b95 !important;
            stroke: #6b5b95 !important;
        }
        
        /* Target the dropdown chevron specifically + HOVER */
        svg[viewBox="0 0 10 6"],
        svg[viewBox="0 0 10 6"] *,
        svg[viewBox="0 0 10 6"] path,
        *:hover svg[viewBox="0 0 10 6"],
        *:hover svg[viewBox="0 0 10 6"] *,
        *:hover svg[viewBox="0 0 10 6"] path {
            color: #6b5b95 !important;
            fill: #6b5b95 !important;
            stroke: #6b5b95 !important;
        }
        
        /* Change selected filter tags from red to purple */
        [data-baseweb="tag"],
        .stMultiSelect [data-baseweb="tag"] {
            background-color: #6b5b95 !important;
            color: white !important;
        }
        
        /* Make the X icon on filter tags white */
        [data-baseweb="tag"] svg,
        [data-baseweb="tag"] svg *,
        .stMultiSelect [data-baseweb="tag"] svg,
        .stMultiSelect [data-baseweb="tag"] svg * {
            color: white !important;
            fill: white !important;
            stroke: white !important;
        }
        
        
        
        /* Slider styling */
        .stSlider > div > div > div {
            background-color: #6b5b95;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Back button styling */
        .back-button {
            background-color: #9b8bb5 !important;
        }
        
        /* Perfume detail view styling */
        .perfume-detail-title {
            font-size: 36px;
            font-weight: 600;
            color: #6b5b95;
            margin-bottom: 10px;
        }
        
        .perfume-detail-brand {
            font-size: 20px;
            color: #888;
            font-style: italic;
            margin-bottom: 20px;
        }
        
        /* Note list styling */
        .note-list {
            background: #f8f7fa;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #6b5b95;
        }
        
        .note-category {
            font-weight: 600;
            color: #6b5b95;
            font-size: 16px;
            margin-bottom: 5px;
        }
        
        /* Questionnaire styling - clean, no white box */
        .bipolar-slider {
            padding: 20px 0;
            margin: 20px 0;
        }
        
        .bipolar-label {
            font-size: 16px;
            font-weight: 500;
            color: #6b5b95;
        }
        
        /* Questionnaire styling - clean, no white box */
        .bipolar-slider {
            padding: 20px 0;
            margin: 20px 0;
        }
        
        .bipolar-label {
            font-size: 16px;
            font-weight: 500;
            color: #6b5b95;
        }
        
        /* Chart container styling */
        .chart-container {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
            border: 2px solid #e8e4f0;
        }
        
        /* Hide Streamlit's default tick marks */
        [data-testid="stSlider"] [data-testid="stTickBar"] {
            display: none !important;
        }
        
        /* Custom number scale */
        .scale-numbers {
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
            font-size: 13px;
            color: #6b5b95;
            padding: 0 4px;
            font-weight: 400;
        }
        
        /* HIDE ONLY TICK MARKS - KEEP SLIDER HANDLE */
        
        /* Target only tick mark and dot elements, NOT the handle */
        .stSlider .rc-slider-mark,
        .stSlider .rc-slider-mark-text,
        .stSlider .rc-slider-dot,
        .stSlider .rc-slider-dot-active,
        div[data-baseweb="slider"] .rc-slider-mark,
        div[data-baseweb="slider"] .rc-slider-mark-text,
        div[data-baseweb="slider"] .rc-slider-dot,
        div[data-baseweb="slider"] .rc-slider-dot-active,
        [data-baseweb="slider"] .rc-slider-mark,
        [data-baseweb="slider"] .rc-slider-mark-text,
        [data-baseweb="slider"] .rc-slider-dot,
        [data-baseweb="slider"] .rc-slider-dot-active {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
        }
        
        /* Hide tick bars */
        .stSlider [data-testid="stTickBar"],
        [data-testid="stTickBar"] {
            display: none !important;
        }
        
        /* Make sure the handle/thumb is visible and functional */
        .stSlider .rc-slider-handle,
        div[data-baseweb="slider"] .rc-slider-handle,
        [data-baseweb="slider"] .rc-slider-handle,
        div[role="slider"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            cursor: pointer !important;
        }
        </style>
    """, unsafe_allow_html=True)

