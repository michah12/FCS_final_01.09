import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from collections import Counter

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
import pickle
import random

from ui.styles import apply_custom_styling
from api.fragella import (
    call_fragella_api, 
    search_fragella_perfumes, 
    transform_api_perfume, 
    get_initial_perfumes
)
from ml.recommender import (
    extract_perfume_features,
    build_training_dataset,
    train_ml_model,
    load_ml_model,
    get_ml_recommendations,
    apply_diversity_filter,
    generate_ml_explanation,
    get_model_insights
)
from data_handlers.persistence import (
    load_user_interactions as _load_interactions,
    save_user_interactions as _save_interactions,
    load_user_inventory as _load_inventory,
    save_user_inventory as _save_inventory,
    load_perfume_rankings as _load_rankings,
    save_perfume_rankings as _save_rankings
)
from ui.detail_components import (
    scroll_to_top,
    render_detail_back_button,
    render_perfume_image,
    render_add_button,
    render_perfume_title,
    render_section_header,
    render_description,
    render_performance_metrics,
    render_main_accords_chart,
    render_notes_pyramid,
    render_seasonality,
    render_gender_boxes,
    render_occasion_bar,
    get_accord_colors
)

# Load API Key from .env file
load_dotenv()
FRAGELLA_API_KEY = os.getenv("FRAGELLA_API_KEY")

# Check if API key is configured
if not FRAGELLA_API_KEY:
    st.error("FRAGELLA_API_KEY not found.")
    st.stop()

st.set_page_config(
    page_title="Scentify Perfume Finder",
    layout="wide",
    initial_sidebar_state="collapsed"
)
USER_INTERACTIONS_FILE = "data/user_interactions.json"
USER_INVENTORY_FILE = "data/user_perfume_inventory.json"
PERFUME_RANKINGS_FILE = "data/perfume_rankings.json"
ML_MODEL_FILE = "data/ml_model.pkl"
ML_SCALER_FILE = "data/ml_scaler.pkl"

ML_CONFIG = {
    'negative_samples_ratio': 2,
    'min_inventory_size': 2,
    'model_type': 'logistic_regression',
    'random_state': 42,
    'min_recommendation_probability': 0.5,
    'diversity_threshold': 0.3
}

LOGO_TYPE = "text"
LOGO_IMAGE_PATH = "logo.png"
LOGO_TEXT = "SCENTIFY"
LOGO_HEIGHT = 80
LOGO_TAGLINE = "Find Your Signature Scent"

def get_image_base64(image_path: str) -> str:
    """Convert image to base64 for HTML embedding"""
    import base64
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def load_user_interactions() -> List[Dict]:
    """Load user interaction history from JSON file"""
    return _load_interactions(USER_INTERACTIONS_FILE)

def save_user_interactions(interactions: List[Dict]):
    """Save user interaction history to JSON file"""
    _save_interactions(interactions, USER_INTERACTIONS_FILE)

def load_user_inventory() -> List[Dict]:
    """Load user parfume collection from JSON file"""
    return _load_inventory(USER_INVENTORY_FILE)

def save_user_inventory(inventory: List[Dict]):
    """Save user perfume collection to JSON file"""
    _save_inventory(inventory, USER_INVENTORY_FILE)

def load_perfume_rankings() -> Dict:
    """Load perfume popularity rankings from JSON file"""
    return _load_rankings(PERFUME_RANKINGS_FILE)

def save_perfume_rankings(rankings: Dict):
    """Save perfume popularity rankings to JSON file"""
    _save_rankings(rankings, PERFUME_RANKINGS_FILE)




def record_interaction(perfume_id: str, interaction_type: str):
    """Record a user interaction and update rankings"""
    interactions = load_user_interactions()
    
    interaction = {
        "perfume_id": perfume_id,
        "interaction_type": interaction_type,
        "timestamp": datetime.now().isoformat()
    }
    
    interactions.append(interaction)
    save_user_interactions(interactions)
    update_perfume_rankings()

def update_perfume_rankings():
    """Count clicks per perfume and save rankings"""
    interactions = load_user_interactions()
    
    rankings = {}
    for interaction in interactions:
        if interaction.get('interaction_type') == 'click':
            perfume_id = interaction['perfume_id']
            rankings[perfume_id] = rankings.get(perfume_id, 0) + 1
    
    save_perfume_rankings(rankings)
    return rankings

def get_ml_sorted_perfumes(perfumes: List[Dict]) -> List[Dict]:
    """Sort perfumes by their popularity based on number of clicks"""
    rankings = load_perfume_rankings()
    
    sorted_perfumes = sorted(
        perfumes,
        key=lambda p: rankings.get(p.get('id', p['name']), 0),
        reverse=True
    )
    
    return sorted_perfumes

def initialize_session_state():
    """Initialize all session state variables on first load"""
    
    if 'active_section' not in st.session_state:
        st.session_state.active_section = "home"
    
    if 'selected_filters' not in st.session_state:
        st.session_state.selected_filters = {}
    
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    
    if 'price_range' not in st.session_state:
        st.session_state.price_range = (0, 200)
    
    if 'questionnaire_answers' not in st.session_state:
        st.session_state.questionnaire_answers = {}
    
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    
    if 'show_questionnaire_results' not in st.session_state:
        st.session_state.show_questionnaire_results = False
    
    if 'perfume_database' not in st.session_state:
        with st.spinner("Loading perfumes from Fragella API..."):
            st.session_state.perfume_database = get_initial_perfumes(FRAGELLA_API_KEY)
            if not st.session_state.perfume_database:
                st.warning("Could not load perfumes from API.")
    
    if 'user_inventory' not in st.session_state:
        st.session_state.user_inventory = load_user_inventory()
    
    if 'current_perfume' not in st.session_state:
        st.session_state.current_perfume = None
    
    if 'show_perfume_details' not in st.session_state:
        st.session_state.show_perfume_details = False
    
    # Track where detail view was opened from (search, questionnaire, inventory)
    if 'detail_view_source' not in st.session_state:
        st.session_state.detail_view_source = 'search'
    
    # Search context for similar recommendations
    if 'search_context' not in st.session_state:
        st.session_state.search_context = {}
    
    # ML recommendations cache
    if 'ml_recommendations' not in st.session_state:
        st.session_state.ml_recommendations = []
    
    # Flag for adding perfumes to inventory
    if 'adding_perfume' not in st.session_state:
        st.session_state.adding_perfume = False


# CSS styling is handled in ui/styles.py
def render_header():
    """Render the Scentify logo header"""
    if LOGO_TYPE == "image":
        if os.path.exists(LOGO_IMAGE_PATH):
            # Use image logo
            logo_html = f"""
            <div style="position: relative; margin-top: -45px;">
                <div class="logo-container" id="logo-home-link">
                    <img src="data:image/png;base64,{get_image_base64(LOGO_IMAGE_PATH)}" class="logo-image" style="max-height: {LOGO_HEIGHT}px;">
                </div>
                <div class="logo-tagline">{LOGO_TAGLINE}</div>
            </div>
            """
        else:
            # Fallback to Text if image not found
            st.warning(f"Logo image not found at '{LOGO_IMAGE_PATH}'. Using text logo instead.")
            logo_html = f"""
            <div style="position: relative; margin-top: -45px;">
                <div class="logo-container" id="logo-home-link">
                    <div class="logo-text">{LOGO_TEXT}</div>
                </div>
                <div class="logo-tagline">{LOGO_TAGLINE}</div>
            </div>
            """
    else:
        # Use text logo
        logo_html = f"""
        <div style="position: relative; margin-top: -45px;">
            <div class="logo-container" id="logo-home-link">
                <div class="logo-text">{LOGO_TEXT}</div>
            </div>
            <div class="logo-tagline">{LOGO_TAGLINE}</div>
        </div>
        """
    
    st.markdown(logo_html, unsafe_allow_html=True)
    
    st.markdown("---")

def render_back_button(target_section: str, label: str = "Back"):
    """Render a back button that navigates to the specified section"""
    if st.button(f"← {label}", key=f"back_to_{target_section}", use_container_width=True):
        st.session_state.active_section = target_section
        st.session_state.show_perfume_details = False
        st.session_state.current_perfume = None
        if target_section == "search":
            st.session_state.search_query = ""
        st.rerun()

def display_perfume_card(perfume: Dict, show_ml_badge: bool = False, source: str = 'search', card_index: int = None):
    """Display a perfume card with image, details, and action buttons"""
    
    if card_index is not None:
        key_suffix = f"{source}_{card_index}_{perfume['id']}"
    else:
        if 'card_counter' not in st.session_state:
            st.session_state.card_counter = 0
        st.session_state.card_counter += 1
        key_suffix = f"{source}_{st.session_state.card_counter}_{perfume['id']}"
    
    rankings = load_perfume_rankings()
    rank_score = rankings.get(perfume['id'], 0)
    
    image_url = perfume.get('image_url', '')
    if not image_url:
        image_url = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjI1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjI1MCIgZmlsbD0iI2U4ZTRmMCIvPjxwYXRoIGQ9Ik04MCA2MGgyMHY0MEg4MHoiIGZpbGw9IiM2YjViOTUiLz48cmVjdCB4PSI2MCIgeT0iMTAwIiB3aWR0aD0iNjAiIGhlaWdodD0iMTIwIiByeD0iMTAiIGZpbGw9IiM2YjViOTUiIG9wYWNpdHk9IjAuOCIvPjxyZWN0IHg9IjcwIiB5PSIxMTAiIHdpZHRoPSI0MCIgaGVpZ2h0PSI5MCIgZmlsbD0iI2M4YjhkOCIgb3BhY2l0eT0iMC42Ii8+PC9zdmc+'
    
    gender = perfume.get("gender", "UNISEX").upper()
    perfume_name = perfume.get('name', 'Unknown')
    perfume_brand = perfume.get('brand', 'Unknown')
    accords = perfume.get('main_accords', ['Fresh', 'Floral'])[:3]
    accords_str = ', '.join(accords)
    perfume_type = perfume.get('perfume_type', 'Eau de Parfum')
    
    with st.container():
        card_html = f"""<div style="background: linear-gradient(135deg, #ffffff 0%, #fafafa 100%); border-radius: 16px; padding: 0; overflow: visible; box-shadow: 0 2px 12px rgba(107, 91, 149, 0.08); border: 1px solid #e8e4f0; height: 420px; display: flex; flex-direction: column; width: 100%; box-sizing: border-box; margin-bottom: 8px;">
    <div style="padding: 15px; background: linear-gradient(180deg, #f8f7fa 0%, transparent 100%);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px; min-height: 26px;">
            <div style="background: linear-gradient(135deg, #ab9bb9 0%, #8b7aa8 100%); padding: 6px 14px; border-radius: 20px; box-shadow: 0 2px 8px rgba(107, 91, 149, 0.2);">
                <span style="color: white; font-size: 10px; font-weight: 700; letter-spacing: 0.6px; text-transform: uppercase; white-space: nowrap;">{perfume_type}</span>
                </div>
            <span style="background: linear-gradient(135deg, #6b5b95 0%, #8b7aa8 100%); color: white; padding: 6px 14px; border-radius: 20px; font-size: 10px; font-weight: 700; letter-spacing: 0.6px; text-transform: uppercase; box-shadow: 0 2px 8px rgba(107, 91, 149, 0.2); white-space: nowrap;">{gender}</span>
                </div>
        <div style="height: 140px; width: 100%; display: flex; align-items: center; justify-content: center; overflow: hidden;">
            <img src="{image_url}" style="max-width: 130px; max-height: 130px; width: auto; height: auto; object-fit: contain; filter: drop-shadow(0 4px 12px rgba(107, 91, 149, 0.12));">
                </div>
                </div>
    <div style="flex: 1; padding: 14px 16px 16px 16px; display: flex; flex-direction: column; align-items: center; justify-content: space-between;">
        <div style="width: 100%; text-align: center; min-height: 60px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 12px;">
            <h3 style="color: #2c2c2c; margin: 0 0 5px 0; font-size: 16px; font-weight: 600; line-height: 1.3; letter-spacing: -0.2px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{perfume_name}</h3>
            <p style="color: #6b5b95; font-style: italic; font-size: 13px; margin: 0; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">by {perfume_brand}</p>
                </div>
        <div style="width: 100%; background: linear-gradient(135deg, #f8f7fa 0%, #ffffff 100%); padding: 10px; border-radius: 12px; border: 1px solid #e8e4f0; min-height: 65px; display: flex; flex-direction: column; justify-content: center;">
            <p style="font-size: 9px; color: #8b7aa8; margin: 0 0 5px 0; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; text-align: center;">Accords</p>
            <p style="text-align: center; color: #6b5b95; font-size: 12px; font-weight: 600; margin: 0; line-height: 1.3; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{accords_str}</p>
            </div>
    </div>
</div>"""
        
        st.markdown(card_html, unsafe_allow_html=True)
        
        if show_ml_badge and rank_score > 0:
            st.markdown(f"""
<div style="text-align: center; margin: 6px 0 8px 0;">
    <span style="background: linear-gradient(135deg, #6b5b95 0%, #8b7aa8 100%);
                 color: white;
                 padding: 5px 14px;
                 border-radius: 16px;
                 font-size: 10px;
                 font-weight: 700;
                 letter-spacing: 0.5px;
                 box-shadow: 0 2px 8px rgba(107, 91, 149, 0.2);
                 display: inline-block;">
        Popular (Score: {rank_score})
    </span>
</div>
            """, unsafe_allow_html=True)
        elif show_ml_badge:
            st.markdown('<div style="height: 35px;"></div>', unsafe_allow_html=True)
        
        # Reduce spacing before buttons
        st.markdown('<div style="height: 5px;"></div>', unsafe_allow_html=True)
        
        # Only show buttons if not in ML recommendations
        if source != 'ml_recommendations':
            # Two buttons side by side: View Details and Add to Inventory
            col1, col2 = st.columns(2, gap="small")
            
            with col1:
                if st.button("View", key=f"view_btn_{key_suffix}", use_container_width=True):
                    # Record interaction
                    record_interaction(perfume['id'], 'click')
                    
                    # Clear any previous states
                    if 'adding_perfume' in st.session_state:
                        st.session_state.adding_perfume = False
                    
                    st.session_state.current_perfume = perfume.copy()
                    st.session_state.show_perfume_details = True
                    
                    if source != 'current':
                        st.session_state.detail_view_source = source
                    
                    st.rerun()
            
            with col2:
                add_clicked = st.button("Add", key=f"add_btn_{key_suffix}", use_container_width=True, type="primary")
            
            if add_clicked:
                was_added = add_to_user_inventory(perfume)
                if was_added:
                    record_interaction(perfume['id'], 'add_to_inventory')
                    st.success(f"Added **{perfume.get('name', 'Perfume')}** to your inventory!")
                    # If not added, error message shows without rerun

def display_inventory_perfume_card(perfume: Dict, index: int):
    """Display perfume card in inventory view"""
    
    image_url = perfume.get('image_url', '')
    if not image_url:
        image_url = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjI1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjI1MCIgZmlsbD0iI2U4ZTRmMCIvPjxwYXRoIGQ9Ik04MCA2MGgyMHY0MEg4MHoiIGZpbGw9IiM2YjViOTUiLz48cmVjdCB4PSI2MCIgeT0iMTAwIiB3aWR0aD0iNjAiIGhlaWdodD0iMTIwIiByeD0iMTAiIGZpbGw9IiM2YjViOTUiIG9wYWNpdHk9IjAuOCIvPjxyZWN0IHg9IjcwIiB5PSIxMTAiIHdpZHRoPSI0MCIgaGVpZ2h0PSI5MCIgZmlsbD0iI2M4YjhkOCIgb3BhY2l0eT0iMC42Ii8+PC9zdmc+'
    
    gender = perfume.get('gender', 'UNISEX').upper()
    perfume_name = perfume.get('name', 'Unknown')
    perfume_brand = perfume.get('brand', 'Unknown')
    accords = perfume.get('main_accords', ['Fresh', 'Floral'])[:3]
    accords_str = ', '.join(accords)
    perfume_type = perfume.get('perfume_type', 'Eau de Parfum')
    
    with st.container():
        card_html = f"""<div style="background: linear-gradient(135deg, #ffffff 0%, #fafafa 100%); border-radius: 16px; padding: 0; overflow: visible; box-shadow: 0 2px 12px rgba(107, 91, 149, 0.08); border: 1px solid #e8e4f0; height: 420px; display: flex; flex-direction: column; width: 100%; box-sizing: border-box; margin-bottom: 8px;">
    <div style="padding: 15px; background: linear-gradient(180deg, #f8f7fa 0%, transparent 100%);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px; min-height: 26px;">
            <div style="background: linear-gradient(135deg, #ab9bb9 0%, #8b7aa8 100%); padding: 6px 14px; border-radius: 20px; box-shadow: 0 2px 8px rgba(107, 91, 149, 0.2);">
                <span style="color: white; font-size: 10px; font-weight: 700; letter-spacing: 0.6px; text-transform: uppercase; white-space: nowrap;">{perfume_type}</span>
                </div>
            <span style="background: linear-gradient(135deg, #6b5b95 0%, #8b7aa8 100%); color: white; padding: 6px 14px; border-radius: 20px; font-size: 10px; font-weight: 700; letter-spacing: 0.6px; text-transform: uppercase; box-shadow: 0 2px 8px rgba(107, 91, 149, 0.2); white-space: nowrap;">{gender}</span>
                </div>
        <div style="height: 140px; width: 100%; display: flex; align-items: center; justify-content: center; overflow: hidden;">
            <img src="{image_url}" style="max-width: 130px; max-height: 130px; width: auto; height: auto; object-fit: contain; filter: drop-shadow(0 4px 12px rgba(107, 91, 149, 0.12));">
            </div>
    </div>
    <div style="flex: 1; padding: 14px 16px 16px 16px; display: flex; flex-direction: column; align-items: center; justify-content: space-between;">
        <div style="width: 100%; text-align: center; min-height: 60px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 12px;">
            <h3 style="color: #2c2c2c; margin: 0 0 5px 0; font-size: 16px; font-weight: 600; line-height: 1.3; letter-spacing: -0.2px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{perfume_name}</h3>
            <p style="color: #6b5b95; font-style: italic; font-size: 13px; margin: 0; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">by {perfume_brand}</p>
        </div>
        <div style="width: 100%; background: linear-gradient(135deg, #f8f7fa 0%, #ffffff 100%); padding: 10px; border-radius: 12px; border: 1px solid #e8e4f0; min-height: 65px; display: flex; flex-direction: column; justify-content: center;">
            <p style="font-size: 9px; color: #8b7aa8; margin: 0 0 5px 0; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; text-align: center;">Accords</p>
            <p style="text-align: center; color: #6b5b95; font-size: 12px; font-weight: 600; margin: 0; line-height: 1.3; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{accords_str}</p>
        </div>
    </div>
</div>"""
        
        st.markdown(card_html, unsafe_allow_html=True)
        
        # Add spacing between card and buttons
        st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1], gap="small")
        with col1:
            if st.button("Remove", key=f"remove_inv_{index}", use_container_width=True):
                st.session_state.user_inventory.pop(index)
                save_user_inventory(st.session_state.user_inventory)
                st.rerun()
        with col2:
            view_clicked = st.button("View", key=f"view_inventory_{perfume['id']}_{index}", use_container_width=True)
            if view_clicked:
                # View details button does not remove, only shows details
                record_interaction(perfume['id'], 'click')
                st.session_state.current_perfume = perfume.copy()
                st.session_state.show_perfume_details = True
                st.session_state.detail_view_source = 'inventory'  # Source for navigation context
                # Exit add perfume mode if active
                if 'adding_perfume' in st.session_state:
                    st.session_state.adding_perfume = False
                st.rerun()

def display_addable_perfume_card(perfume: Dict):
    """
    Display perfume card with add and view buttons.
    
    """
    # Use perfume icon if no Image available
    image_url = perfume.get('image_url', '')
    if not image_url or image_url == '':
        image_url = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjI1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjI1MCIgZmlsbD0iI2U4ZTRmMCIvPjxwYXRoIGQ9Ik04MCA2MGgyMHY0MEg4MHoiIGZpbGw9IiM2YjViOTUiLz48cmVjdCB4PSI2MCIgeT0iMTAwIiB3aWR0aD0iNjAiIGhlaWdodD0iMTIwIiByeD0iMTAiIGZpbGw9IiM2YjViOTUiIG9wYWNpdHk9IjAuOCIvPjxyZWN0IHg9IjcwIiB5PSIxMTAiIHdpZHRoPSI0MCIgaGVpZ2h0PSI5MCIgZmlsbD0iI2M4YjhkOCIgb3BhY2l0eT0iMC42Ii8+PC9zdmc+'
    
    with st.container():
        st.markdown(f"""
            <div class="perfume-card" style="padding: 15px; height: 420px; display: flex; flex-direction: column; justify-content: space-between; width: 100%; box-sizing: border-box; overflow: visible; margin-bottom: 8px;">
                <div style="height: 200px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px; overflow: hidden;">
                    <img src="{image_url}" 
                         onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjI1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjI1MCIgZmlsbD0iI2U4ZTRmMCIvPjxwYXRoIGQ9Ik04MCA2MGgyMHY0MEg4MHoiIGZpbGw9IiM2YjViOTUiLz48cmVjdCB4PSI2MCIgeT0iMTAwIiB3aWR0aD0iNjAiIGhlaWdodD0iMTIwIiByeD0iMTAiIGZpbGw9IiM2YjViOTUiIG9wYWNpdHk9IjAuOCIvPjxyZWN0IHg9IjcwIiB5PSIxMTAiIHdpZHRoPSI0MCIgaGVpZ2h0PSI5MCIgZmlsbD0iI2M4YjhkOCIgb3BhY2l0eT0iMC42Ii8+PC9zdmc>'"
                         style="max-width: 140px; max-height: 180px; width: auto; height: auto; object-fit: contain; border-radius: 8px;">
                </div>
                <div style="flex: 1; display: flex; flex-direction: column; justify-content: center;">
                    <h4 style="color: #6b5b95; margin: 0 0 8px 0; text-align: center; font-size: 15px; line-height: 1.2; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; padding: 0 5px;">{perfume['name']}</h4>
                    <div style="text-align: center; border-bottom: 1px solid #e8e4f0; padding-bottom: 8px;">
                        <p style="color: #888; font-style: italic; font-size: 12px; margin: 0; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Brand: {perfume['brand']}</p>
                    </div>
                </div>
            </div>
    """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1], gap="small")
        with col1:
            if st.button("Add", key=f"add_to_inv_{perfume['id']}", use_container_width=True):
                was_added = add_to_user_inventory(perfume)
                if was_added:
                    record_interaction(perfume['id'], 'add_to_inventory')
                    st.success(f"Added to inventory")
        with col2:
            view_clicked = st.button("View", key=f"view_no_add_{perfume['id']}", use_container_width=True)
            if view_clicked:
                record_interaction(perfume['id'], 'click')
                st.session_state.current_perfume = perfume.copy()
                st.session_state.show_perfume_details = True
                st.session_state.adding_perfume = False  # Exit add mode
                st.rerun()

def render_filter_tags():
    """
    Display selected filters as tags with X buttons to remove them.
    """
    tags_html = '<div style="margin-bottom: 15px;">'
    
    for filter_name, values in st.session_state.selected_filters.items():
        # Replace underscores with spaces for display
        display_name = filter_name.replace('_', ' ').title()
        
        if filter_name == 'price':
            tags_html += f'<span class="filter-tag">Price: ${values[0]} - ${values[1]}</span>'
        elif isinstance(values, list):
            for value in values:
                tags_html += f'<span class="filter-tag">{display_name}: {value}</span>'
    
    tags_html += '</div>'
    st.markdown(tags_html, unsafe_allow_html=True)
    
    # Remove tag buttons
    cols = st.columns(len(st.session_state.selected_filters) + 1)
    idx = 0
    filters_to_remove = []
    
    for filter_name in list(st.session_state.selected_filters.keys()):
        # Replace underscores with spaces and capitalize for button display
        display_name = filter_name.replace('_', ' ').title()
        
        with cols[idx]:
            if st.button(f"Remove {display_name}", key=f"remove_{filter_name}"):
                filters_to_remove.append(filter_name)
        idx += 1
    
    for filter_name in filters_to_remove:
        del st.session_state.selected_filters[filter_name]
    
    if filters_to_remove:
                        st.rerun()
                
def filter_perfumes(perfumes: List[Dict]) -> List[Dict]:
    """Apply user-selected filters to parfume list"""
    filtered = perfumes.copy()
    
    if st.session_state.search_query:
        query = st.session_state.search_query.lower()
        filtered = [p for p in filtered if query in p['name'].lower() or query in p['brand'].lower()]
    
    if 'gender' in st.session_state.selected_filters:
        genders = st.session_state.selected_filters['gender']
        filtered = [p for p in filtered if p['gender'] in genders]
    
    if 'scent_type' in st.session_state.selected_filters:
        scents = st.session_state.selected_filters['scent_type']
        filtered = [p for p in filtered if p['scent_type'] in scents]
    
    return filtered

def create_donut_chart(note_counter: Counter, title: str):
    """Create donut chart showing top 10 notes"""
    if not note_counter:
        st.write("No data")
        return
    
    top_10 = note_counter.most_common(10)
    
    total = sum(note_counter.values())
    top_10_total = sum(count for _, count in top_10)
    rest_count = total - top_10_total
    
    # Prepare data top 10 from highest to lowest, then Rest
    labels = []
    values = []
    colors = []
    
    # Purple palette for top 10 (darkest for highest count)
    color_palette = [
        '#6b5b95',  # Main purple
        '#7a6a9f',  # Dark purple
        '#8979a9',  # Medium dark purple
        '#9888b3',  # Medium purple
        '#a797bd',  # Medium light purple
        '#b6a6c7',  # Light purple
        '#c5b5d1',  # Lighter purple
        '#d4c4db',  # Very light purple
        '#dcd0e3',  # Pale purple
        '#e4dae9',  # Very pale purple
    ]
    
    for i, (note, count) in enumerate(top_10):
        # Capitalize first letter of each word
        note_name = note.title() if isinstance(note, str) else note
        labels.append(note_name)
        values.append(count)
        colors.append(color_palette[i] if i < len(color_palette) else color_palette[-1])
    
    # Add Rest last
    if rest_count > 0:
        labels.append('Rest')
        values.append(rest_count)
        colors.append('#e8dff5')  # Very light purple for Rest
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=colors),
        direction='clockwise',
        sort=False  # Maintain original order
    )])
    
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="v", 
            yanchor="middle", 
            y=0.5, 
            xanchor="left", 
            x=1.1,
            traceorder="normal"  # Keep order: highest to lowest, then Rest
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=0, b=0, l=0, r=0),
        height=250
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})

def add_to_user_inventory(perfume: Dict) -> bool:
    """Add perfume to inventory, returns False if already exists"""
    if any(p['id'] == perfume['id'] for p in st.session_state.user_inventory):
        st.session_state.inventory_message = "already_exists"
        st.session_state.inventory_perfume_name = perfume.get('name', 'This perfume')
        st.error(f"**{perfume.get('name', 'This perfume')}** is already in your collection!")
        return False
    
    # Clean perfume object by removing ML-specific fields
    clean_perfume = perfume.copy()
    clean_perfume.pop('ml_score', None)
    clean_perfume.pop('ml_explanation', None)
    
    st.session_state.user_inventory.append(clean_perfume)
    save_user_inventory(st.session_state.user_inventory)
    
    st.session_state.inventory_message = "added"
    st.session_state.inventory_perfume_name = perfume.get('name', 'Perfume')
    
    return True

def render_landing_page():
    """Main landing page with search, questionnaire, and inventory options"""
    st.markdown('<div id="page-top" style="height: 1px;"></div>', unsafe_allow_html=True)
    
    if st.session_state.show_perfume_details and st.session_state.current_perfume:
        render_perfume_detail_view(st.session_state.current_perfume)
        return
    
    # Create three equal columns for the sections
    col1, col2, col3 = st.columns(3)
    
    # Section 1: Search
    with col1:
        st.markdown("""
            <div class="section-card">
                <div class="section-title">Search</div>
                <div class="section-description">
                    Find your perfect perfume using our advanced filter system. 
                    Search by brand, price, scent type, and more to discover fragrances tailored to your preferences.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Open Search", key="btn_search", use_container_width=True):
            st.session_state.active_section = "search"
            # Clear previous search when entering search section
            st.session_state.search_query = ""
            st.rerun()
    
    # Section 2: Questionnaire
    with col2:
        st.markdown("""
            <div class="section-card">
                <div class="section-title">Questionnaire</div>
                <div class="section-description">
                    Not sure what you're looking for? Take our personalized questionnaire 
                    to discover perfumes that match your unique scent profile and preferences.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Take Questionnaire", key="btn_questionnaire", use_container_width=True):
            st.session_state.active_section = "questionnaire"
            st.session_state.current_question = 0
            st.session_state.show_questionnaire_results = False
            st.session_state.questionnaire_answers = {}  # Reset all answers to start fresh
            st.rerun()
    
    # Section 3: Inventory
    with col3:
        st.markdown("""
            <div class="section-card">
                <div class="section-title">Perfume Inventory</div>
                <div class="section-description">
                    Manage your personal perfume collection. Add fragrances you own and 
                    view detailed analytics and recommendations based on your collection.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("View My Perfumes", key="btn_inventory", use_container_width=True):
            st.session_state.active_section = "inventory"
            st.rerun()
    
    # User favorites or Top 3 Most Popular Perfumes
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<h2 style="color: #6b5b95; text-align: center;">User Favorites</h2>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    render_user_favorites()

def render_user_favorites():
    """Display top 3 most clicked perfumes"""
    rankings = load_perfume_rankings()
    
    if not rankings:
        st.info("No user favorites yet. Start exploring perfumes!")
        return
    
    # Sort by clicks and get top 3
    top_perfumes_ids = sorted(rankings.items(), key=lambda x: x[1], reverse=True)[:3]
    
    all_perfumes = st.session_state.perfume_database
    top_perfumes = []
    for perfume_id, clicks in top_perfumes_ids:
        perfume = next((p for p in all_perfumes if p.get('id') == perfume_id or p.get('name') == perfume_id), None)
        if perfume:
            perfume_copy = perfume.copy()
            perfume_copy['clicks'] = clicks
            top_perfumes.append(perfume_copy)
    
    if not top_perfumes:
        st.info("No user favorites yet. Start exploring perfumes!")
        return
    
    cols = st.columns(3, gap="large")
    
    # Rank-specific badge colors (Gold, Silver, Bronze)
    rank_styles = [
        {'badge_bg': 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)', 'badge_text': 'white'},
        {'badge_bg': 'linear-gradient(135deg, #C0C0C0 0%, #A8A8A8 100%)', 'badge_text': 'white'},
        {'badge_bg': 'linear-gradient(135deg, #CD7F32 0%, #B87333 100%)', 'badge_text': 'white'}
    ]
    
    for idx, (col, perfume) in enumerate(zip(cols, top_perfumes)):
        with col:
            rank_num = idx + 1
            rank_style = rank_styles[idx] if idx < len(rank_styles) else rank_styles[0]
            
            image_url = perfume.get('image_url', '')
            if not image_url:
                image_url = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjI1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjI1MCIgZmlsbD0iI2U4ZTRmMCIvPjxwYXRoIGQ9Ik04MCA2MGgyMHY0MEg4MHoiIGZpbGw9IiM2YjViOTUiLz48cmVjdCB4PSI2MCIgeT0iMTAwIiB3aWR0aD0iNjAiIGhlaWdodD0iMTIwIiByeD0iMTAiIGZpbGw9IiM2YjViOTUiIG9wYWNpdHk9IjAuOCIvPjxyZWN0IHg9IjcwIiB5PSIxMTAiIHdpZHRoPSI0MCIgaGVpZ2h0PSI5MCIgZmlsbD0iI2M4YjhkOCIgb3BhY2l0eT0iMC42Ii8+PC9zdmc+'
            
            perfume_name = perfume.get('name', 'Unknown')
            perfume_brand = perfume.get('brand', 'Unknown')
            perfume_gender = perfume.get('gender', 'UNISEX').upper()
            perfume_clicks = perfume.get('clicks', 0)
            
            main_accords = perfume.get('main_accords', [])
            if isinstance(main_accords, list) and main_accords:
                accords_display = ', '.join(main_accords[:3])
            else:
                accords_display = 'Fresh, Floral'
            
            badge_bg = rank_style['badge_bg']
            badge_text = rank_style['badge_text']
            
            card_html = f'<div style="background: linear-gradient(135deg, #ffffff 0%, #fafafa 100%); border-radius: 20px; padding: 0; overflow: hidden; box-shadow: 0 4px 20px rgba(107, 91, 149, 0.12); height: 550px; display: flex; flex-direction: column;"><div style="background: linear-gradient(135deg, #6b5b95 0%, #8b7aa8 100%); padding: 18px 20px; display: flex; align-items: center; justify-content: space-between;"><div style="background: {badge_bg}; width: 45px; height: 45px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 800; color: {badge_text}; box-shadow: 0 4px 12px rgba(0,0,0,0.2); border: 3px solid white;">{rank_num}</div><span style="background: rgba(255,255,255,0.95); color: #6b5b95; padding: 6px 14px; border-radius: 20px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px;">{perfume_gender}</span></div><div style="flex: 1; padding: 25px 20px; display: flex; flex-direction: column; align-items: center; justify-content: space-between;"><div style="width: 100%; height: 180px; display: flex; align-items: center; justify-content: center; margin-bottom: 20px;"><img src="{image_url}" style="max-width: 160px; max-height: 160px; object-fit: contain; filter: drop-shadow(0 4px 12px rgba(107, 91, 149, 0.15));"></div><div style="text-align: center; width: 100%;"><h3 style="color: #2c2c2c; margin: 0 0 8px 0; font-size: 20px; font-weight: 600; line-height: 1.3;">{perfume_name}</h3><p style="color: #6b5b95; font-style: italic; font-size: 15px; margin: 0 0 15px 0; font-weight: 500;">by {perfume_brand}</p><div style="background: linear-gradient(135deg, #f8f7fa 0%, #ffffff 100%); padding: 12px; border-radius: 12px; border: 1px solid #e8e4f0; margin-bottom: 12px;"><p style="font-size: 11px; color: #8b7aa8; margin: 0 0 6px 0; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Accords</p><p style="color: #6b5b95; font-size: 14px; font-weight: 600; margin: 0; line-height: 1.4;">{accords_display}</p></div><div style="display: inline-flex; align-items: center; background: linear-gradient(135deg, #6b5b95 0%, #8b7aa8 100%); padding: 8px 16px; border-radius: 20px; box-shadow: 0 2px 8px rgba(107, 91, 149, 0.2);"><span style="color: white; font-size: 12px; font-weight: 700; letter-spacing: 0.5px;">Popular (Score: {perfume_clicks})</span></div></div></div></div>'
            
            st.markdown(card_html, unsafe_allow_html=True)
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            if st.button("View Full Details", key=f"fav_btn_{perfume.get('id', idx)}", use_container_width=True, type="primary"):
                record_interaction(perfume['id'], 'click')
                st.session_state.current_perfume = perfume
                st.session_state.show_perfume_details = True
                st.session_state.detail_view_source = 'home'
                st.rerun()

def render_search_section():
    """Search page with filters and live API search"""
    st.markdown('<div id="page-top" style="height: 1px;"></div>', unsafe_allow_html=True)
    
    if st.session_state.show_perfume_details and st.session_state.current_perfume:
        render_perfume_detail_view(st.session_state.current_perfume)
        return
    
    render_back_button("home", "Back to Home")
    
    st.markdown('<h2 style="color: #6b5b95;">Search for Perfumes</h2>', unsafe_allow_html=True)
    st.markdown('<h3 style="color: #6b5b95;">Search for brand / name</h3>', unsafe_allow_html=True)
    search_query = st.text_input(
        "Enter brand or perfume name...",
        value=st.session_state.search_query,
        placeholder="Enter brand or perfume name...",
        key="search_input",
        label_visibility="collapsed"
    )
    st.session_state.search_query = search_query
    
    st.markdown("---")
    
    # Filters
    st.markdown('<h3 style="color: #6b5b95;">Filters</h3>', unsafe_allow_html=True)
    
    all_brands = sorted(list(set([
        "3Lab", "4711", "7 Virtues", "8 Muse",
        "Abercrombie & Fitch", "Acqua di Parma", "Adidas", "Aerin", "Agent Provocateur", "Aigner", 
        "Ajmal", "Al Haramain", "Alaia", "Alexander McQueen", "Alfred Sung", "Amouage", 
        "Annick Goutal", "Anna Sui", "Aramis", "Ariana Grande", "Armaf", "Armani", "Atelier Cologne",
        "Azzaro", "Balenciaga", "Balmain", "Banana Republic", "Benefit", "Bentley", "Boucheron",
        "Bond No. 9", "Bottega Veneta", "Brecourt", "Britney Spears", "Bulgari", "Burberry", "Bvlgari", "Byredo",
        "Cacharel", "Calvin Klein", "Carolina Herrera", "Cartier", "Carven", "Celine", "Cerruti",
        "Chanel", "Chloe", "Chopard", "Christian Dior", "Christian Louboutin", "Clarins", "Clinique",
        "Coach", "Commodity", "Creed", "Curve", "Davidoff", "Diesel", "Diptyque", "DKNY", 
        "Dolce & Gabbana", "Donna Karan", "Dunhill", "Elizabeth Arden", "Elizabeth Taylor", 
        "Emporio Armani", "Escada", "Estee Lauder", "Eternity", "Etat Libre d'Orange",
        "Fendi", "Ferragamo", "Frederic Malle", "Gianni Versace", "Giorgio Armani", "Giorgio Beverly Hills",
        "Givenchy", "Gucci", "Guerlain", "Guess", "Halston", "Hermes", "Histoires de Parfums",
        "Hugo Boss", "Issey Miyake", "Jacquemus", "James Bond", "Jean Paul Gaultier", "Jennifer Aniston",
        "Jennifer Lopez", "Jessica Simpson", "Jimmy Choo", "Jo Malone", "John Varvatos", "Joop",
        "Juicy Couture", "Juliette Has a Gun", "Karl Lagerfeld", "Kate Spade", "Kenzo", "Kilian",
        "Lacoste", "Lalique", "Lancome", "Lanvin", "Laura Mercier", "Le Labo", "Loewe", "Lolita Lempicka",
        "Maison Francis Kurkdjian", "Maison Margiela", "Marc Jacobs", "Memo Paris", "Michael Kors", 
        "Missoni", "Miu Miu", "Molton Brown", "Montblanc", "Moschino", "Mugler", "Narciso Rodriguez",
        "Nasomatto", "Nautica", "Nest", "Nina Ricci", "Nishane", "Olivier Durbano",
        "Paco Rabanne", "Penhaligon's", "Philosophy", "Prada", "Ralph Lauren", "Rihanna", "Roberto Cavalli",
        "Rochas", "Salvatore Ferragamo", "Sarah Jessica Parker", "Serge Lutens", "Shiseido", "Sì",
        "Stella McCartney", "Thierry Mugler", "Tiffany & Co", "Tom Ford", "Tommy Hilfiger", "Tory Burch",
        "Trussardi", "Valentino", "Van Cleef & Arpels", "Vera Wang", "Versace", "Viktor & Rolf",
        "Vilhelm Parfumerie", "Xerjoff", "Yves Saint Laurent", "Zadig & Voltaire", "Zara"
    ] + [p['brand'] for p in st.session_state.perfume_database])))
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("Scent Type", expanded=False):
            scent_types = ["Floral", "Woody", "Fresh", "Citrus", "Oriental", "Gourmand", "Green", "Leather"]
            selected_scents = st.multiselect(
                "Select scent types",
                options=scent_types,
                default=st.session_state.selected_filters.get('scent_type', []),
                key="filter_scent"
            )
            if st.button("Save", key="save_scent"):
                if selected_scents:
                    st.session_state.selected_filters['scent_type'] = selected_scents
                elif 'scent_type' in st.session_state.selected_filters:
                    del st.session_state.selected_filters['scent_type']
                st.success("Scent type filter saved")
    
    with col2:
        with st.expander("For Whom", expanded=False):
            selected_gender = st.multiselect(
                "Select gender",
                options=["Male", "Female", "Unisex"],
                default=st.session_state.selected_filters.get('gender', []),
                key="filter_gender"
            )
            if st.button("Save", key="save_gender"):
                if selected_gender:
                    st.session_state.selected_filters['gender'] = selected_gender
                elif 'gender' in st.session_state.selected_filters:
                    del st.session_state.selected_filters['gender']
                st.success("Gender filter saved")
    
    st.markdown("---")
    
    # Display selected filters as tags
    if st.session_state.selected_filters:
        st.markdown('<h4 style="color: #6b5b95;">Selected Filters</h4>', unsafe_allow_html=True)
        render_filter_tags()
        st.markdown("---")
    
    # Reset and search button
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("Reset Filters", key="reset_filters", use_container_width=True):
            st.session_state.selected_filters = {}
            st.session_state.price_range = (0, 200)
            st.session_state.search_query = ""
            st.rerun()
    
    with col_btn2:
        if st.button("Search", key="do_search", use_container_width=True):
            st.session_state.search_context = st.session_state.selected_filters.copy()
            st.rerun()
    
        st.markdown("---")
    
    # Search results
    st.markdown('<h3 style="color: #6b5b95;">Search Results</h3>', unsafe_allow_html=True)
    display_search_results()

def display_search_results():
    """Display search results with live API integration"""
    has_search_query = st.session_state.search_query and len(st.session_state.search_query) >= 3
    has_filters = bool(st.session_state.selected_filters)
    force_show = st.session_state.get('force_show_results', False)
    
    if has_search_query:
        with st.spinner("Searching Fragella database..."):
            api_results = search_fragella_perfumes(FRAGELLA_API_KEY, st.session_state.search_query, limit=20)
            if api_results:
                transformed_results = [transform_api_perfume(p) for p in api_results]
                for perfume in transformed_results:
                    if not any(p['id'] == perfume['id'] for p in st.session_state.perfume_database):
                        st.session_state.perfume_database.append(perfume)
                
                if has_filters:
                    filtered_perfumes = filter_perfumes(transformed_results)
                else:
                    filtered_perfumes = transformed_results
            else:
                filtered_perfumes = []
    elif has_filters or force_show:
        # Use existing database with filters only
        filtered_perfumes = filter_perfumes(st.session_state.perfume_database)
        # Reset force_show flag
        if force_show:
            st.session_state.force_show_results = False
    else:
        # If no search and no filters
        st.info("Enter a perfume name or apply filters to see results")
        return
    
    # Apply ML ranking to sort perfumes by popularity
    sorted_perfumes = get_ml_sorted_perfumes(filtered_perfumes)
    
    st.write(f"Found {len(sorted_perfumes)} perfume(s)")
    
    if sorted_perfumes:
        for i in range(0, len(sorted_perfumes), 3):
            col1, col2, col3 = st.columns(3, gap="medium")
            
            with col1:
                if i < len(sorted_perfumes):
                    display_perfume_card(sorted_perfumes[i], show_ml_badge=True, card_index=i)
            
            with col2:
                if i + 1 < len(sorted_perfumes):
                    display_perfume_card(sorted_perfumes[i + 1], show_ml_badge=True, card_index=i+1)
            
            with col3:
                if i + 2 < len(sorted_perfumes):
                    display_perfume_card(sorted_perfumes[i + 2], show_ml_badge=True, card_index=i+2)
    else:
        st.info("No perfumes match your search criteria. Try different search terms or adjust your filters.")

# Perfume detail view
def render_perfume_detail_view(perfume: Dict):
    """
    Render detailed view of a perfume with all information.
    
    """
    # Force scroll to top when detail view opens
    components.html(
        """
        <script>
        window.parent.document.documentElement.scrollTop = 0;
        window.parent.document.body.scrollTop = 0;
        </script>
        """,
        height=0,
    )
    
    # Context-aware back button navigation
    if st.session_state.detail_view_source == 'home':
        # Coming from home/landing page User Favorites
        if st.button("← Back to Home", key="back_to_home", use_container_width=True):
            st.session_state.show_perfume_details = False
            st.session_state.current_perfume = None
            st.session_state.detail_view_source = 'search'  # Reset to default
            st.rerun()
    elif st.session_state.detail_view_source == 'inventory':
        # Coming from inventory
        if st.button("← Back to Inventory", key="back_to_inventory", use_container_width=True):
            st.session_state.show_perfume_details = False
            st.session_state.current_perfume = None
            st.session_state.detail_view_source = 'search'  # Reset to default
            st.rerun()
    elif st.session_state.show_questionnaire_results:
        # Coming from questionnaire results
        if st.button("← Back to Recommendations", key="back_to_questionnaire", use_container_width=True):
            st.session_state.show_perfume_details = False
            st.session_state.current_perfume = None
            st.session_state.detail_view_source = 'search'  # Reset to default
            st.rerun()
    else:
        # Coming from search section
        render_back_button("search", "Back to Results")
    
    # Centered image at top
    st.markdown(f'''
        <div style="background: linear-gradient(135deg, #fafafa 0%, #ffffff 100%);
                    padding: 50px;
                    border-radius: 28px;
                    text-align: center;
                    box-shadow: 0 8px 30px rgba(107, 91, 149, 0.1);
                    margin-bottom: 35px;
                    border: 1px solid #e8e4f0;
                    position: relative;
                    overflow: hidden;">
            <div style="position: absolute; top: -50px; right: -50px; width: 200px; height: 200px; 
                        background: radial-gradient(circle, rgba(107, 91, 149, 0.05) 0%, transparent 70%);"></div>
            <div style="position: absolute; bottom: -50px; left: -50px; width: 200px; height: 200px; 
                        background: radial-gradient(circle, rgba(171, 155, 185, 0.05) 0%, transparent 70%);"></div>
            <img src="{perfume['image_url']}" 
                 style="max-width: 400px;
                        height: auto;
                        max-height: 450px;
                        object-fit: contain;
                        filter: drop-shadow(0 10px 25px rgba(107, 91, 149, 0.15));
                        position: relative;
                        z-index: 1;">
        </div>
    ''', unsafe_allow_html=True)
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("Add to My Perfumes", key="add_to_inventory", use_container_width=True, type="primary"):
            was_added = add_to_user_inventory(perfume)
            if was_added:
                record_interaction(perfume['id'], 'add_to_inventory')
                st.success(f"Added {perfume['name']} to your collection")
        
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    
    # Perfume name and brand
    perfume_name = perfume["name"]
    perfume_brand = perfume["brand"]
    perfume_desc = perfume['description']
    longevity = perfume.get('longevity', 'Moderate')
    sillage = perfume.get('sillage', 'Moderate')
    
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 35px;">
            <h1 style="color: #6b5b95; 
                       margin: 0 0 12px 0; 
                       font-size: 48px; 
                       font-weight: 800;
                       letter-spacing: -1px;
                       line-height: 1.1;">
                {perfume_name}
            </h1>
            <div style="display: inline-flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                <div style="width: 40px; height: 2px; background: linear-gradient(90deg, transparent 0%, #6b5b95 100%);"></div>
                <p style="color: #8b7aa8; 
                          font-style: italic; 
                          font-size: 24px; 
                          margin: 0;
                          font-weight: 500;">
                    {perfume_brand}
                </p>
                <div style="width: 40px; height: 2px; background: linear-gradient(90deg, #6b5b95 0%, transparent 100%);"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Two collum layout: Description on Left, Main Accords on Right
    col_left, col_right = st.columns([1, 1], gap="large")
    
    # Description of left collum
    with col_left:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="color: #6b5b95; 
                           margin: 0; 
                           font-size: 32px; 
                           font-weight: 800;
                           text-transform: uppercase;
                           letter-spacing: 3px;
                           padding-bottom: 15px;
                           border-bottom: 5px solid #6b5b95;
                           width: 100%;">
                    Description
                </h2>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div style="text-align: center; margin-bottom: 30px;">
                <p style="color: #444; 
                          margin: 0; 
                          font-size: 19px; 
                          line-height: 1.8;
                          letter-spacing: 0.3px;
                          font-weight: 500;">
                    {perfume_desc}
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Longevity and sillage
        longevity_sillage_html = f"""
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 30px;">
                <div style="background: linear-gradient(135deg, #6b5b95 0%, #8b7aa8 100%); padding: 0; border-radius: 20px; box-shadow: 0 8px 25px rgba(107, 91, 149, 0.2); display: flex; align-items: center; justify-content: center; min-height: 180px;">
                    <div style="text-align: center; width: 100%;">
                        <div style="margin-bottom: 20px;">
                            <span style="color: rgba(255,255,255,0.9); font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px;">LONGEVITY</span>
                        </div>
                        <div>
                            <span style="font-size: 32px; font-weight: 900; color: white; text-shadow: 0 2px 10px rgba(0,0,0,0.2);">{longevity}</span>
                        </div>
                    </div>
                </div>
                <div style="background: linear-gradient(135deg, #ab9bb9 0%, #cbbbc9 100%); padding: 0; border-radius: 20px; box-shadow: 0 8px 25px rgba(171, 155, 185, 0.2); display: flex; align-items: center; justify-content: center; min-height: 180px;">
                    <div style="text-align: center; width: 100%;">
                        <div style="margin-bottom: 20px;">
                            <span style="color: #6b5b95; font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px;">SILLAGE</span>
                        </div>
                        <div>
                            <span style="font-size: 32px; font-weight: 900; color: #6b5b95; text-shadow: 0 2px 10px rgba(0,0,0,0.1);">{sillage}</span>
                        </div>
                    </div>
                </div>
            </div>
        """
        st.markdown(longevity_sillage_html, unsafe_allow_html=True)
    
    # Main accords in the right collum
    with col_right:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="color: #6b5b95; 
                           margin: 0; 
                           font-size: 32px; 
                           font-weight: 800;
                           text-transform: uppercase;
                           letter-spacing: 3px;
                           padding-bottom: 15px;
                           border-bottom: 5px solid #6b5b95;
                           width: 100%;">
                    Main Accords
                </h2>
            </div>
        """, unsafe_allow_html=True)
        
        # Define accord colors to display a full list with thematic colors for each accord
        accord_colors = {
            # Animal & Musk
            'animalic': '#8B7355', 'musk': '#D3C5B5', 'musky': '#E6D5E6', 'castoreum': '#6B5B4B',
            # Floral
            'floral': '#E8A5D4', 'white floral': '#F5F5F5', 'rose': '#FF69B4', 'jasmine': '#FFF8DC',
            'ylang ylang': '#FFE4B5', 'tuberose': '#FADADD', 'iris': '#9370DB', 'violet': '#8A2BE2',
            'lavender': '#B19CD9', 'orange blossom': '#FFE4B2', 'lily': '#FFFACD',
            # Fresh & Green
            'fresh': '#A8E6CF', 'green': '#90EE90', 'herbal': '#8FBC8F', 'aromatic': '#9370DB',
            'aquatic': '#7FCDCD', 'marine': '#5F9EA0', 'ozonic': '#B0E0E6', 'watery': '#ADD8E6',
            # Citrus
            'citrus': '#FFD93D', 'lemon': '#FFF44F', 'bergamot': '#F4D03F', 'orange': '#FFA500',
            'mandarin': '#FF8C00', 'grapefruit': '#FFB6C1', 'lime': '#BFFF00',
            # Woody
            'woody': '#8B6F47', 'cedar': '#A0826D', 'sandalwood': '#C19A6B', 'patchouli': '#6B5B4B',
            'vetiver': '#7C7356', 'oud': '#4A3728', 'agarwood': '#3E2723', 'pine': '#4A7856', 'cypress': '#5F7356',
            # Spicy & Warm
            'spicy': '#DC143C', 'warm spicy': '#D97548', 'cinnamon': '#B87333', 'clove': '#8B4513',
            'pepper': '#A9A9A9', 'pink pepper': '#F4A7B9', 'cardamom': '#E6BE8A', 'nutmeg': '#8B7355', 'ginger': '#DAA520',
            # Sweet & Gourmand
            'sweet': '#E85D75', 'gourmand': '#DDA15E', 'vanilla': '#F3E5AB', 'caramel': '#D2691E',
            'chocolate': '#7B3F00', 'honey': '#F4C542', 'tonka bean': '#D2B48C', 'almond': '#FFEBCD',
            'coconut': '#FFFFF0', 'coffee': '#6F4E37',
            # Fruity
            'fruity': '#FF6B6B', 'tropical': '#F4D03F', 'berry': '#8B008B', 'peach': '#FFDAB9',
            'apple': '#90EE90', 'pear': '#D1E231', 'plum': '#8E4585', 'cherry': '#DE3163', 'blackcurrant': '#2E0854',
            # Earthy & Mossy
            'earthy': '#8B8B7A', 'mossy': '#8A9A5B', 'oakmoss': '#6B8E23', 'peat': '#4A4A3A',
            # Oriental & Resinous
            'oriental': '#B8860B', 'amber': '#FFBF00', 'incense': '#8B7D6B', 'myrrh': '#8B7355',
            'benzoin': '#D2B48C', 'labdanum': '#8B7765', 'resinous': '#A0826D',
            # Leather & Tobacco
            'leather': '#654321', 'tobacco': '#7C5936', 'suede': '#8B7E66', 'birch tar': '#4A4A4A',
            # Powdery & Soft
            'powdery': '#E6C9E3', 'soft': '#F5E6E8', 'aldehydic': '#F0F0F0',
            # Balsamic
            'balsamic': '#8B7355', 'peru balsam': '#8B6914',
            # Lactonic & Creamy
            'lactonic': '#FFF8DC', 'creamy': '#FFFACD', 'milky': '#FFFEF0',
            # Fresh Spicy
            'fresh spicy': '#FF8C69',
            # Soapy & Clean
            'soapy': '#E0FFFF', 'clean': '#F0FFFF',
            # Coniferous
            'coniferous': '#228B22'
        }
        
        main_accords = perfume.get('main_accords', ['Fresh', 'Floral', 'Sweet'])
        
        # Assign intensity values
        if len(main_accords) > 0:
            decrement = min(7, 70 / len(main_accords))
            intensities = [max(100 - (i * decrement), 30) for i in range(len(main_accords))]
        else:
            intensities = []
        
        # Create horizontal bar chart data
        accord_data = []
        for i, accord in enumerate(main_accords):
            accord_lower = accord.lower().strip()
            color = accord_colors.get(accord_lower, '#6b5b95')
            accord_data.append({
                'Accord': accord_lower,
                'Intensity': intensities[i],
                'Color': color
            })
        
        if accord_data:
            fig_accords = go.Figure()
            
            for item in accord_data:
                fig_accords.add_trace(go.Bar(
                    y=[item['Accord']],
                    x=[item['Intensity']],
                    orientation='h',
                    marker=dict(
                        color=item['Color'],
                        line=dict(width=0)
                    ),
                    name=item['Accord'],
                    showlegend=False,
                    text=item['Accord'],
                    textposition='inside',
                    insidetextanchor='middle',
                    textfont=dict(color='white', size=15, family='Arial, sans-serif'),
                    hoverinfo='skip',
                    width=0.7
                ))
            
            chart_height = max(350, len(main_accords) * 55)
            
            fig_accords.update_layout(
                height=chart_height,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#333', size=15, family='Arial, sans-serif'),
                xaxis=dict(
                    title='',
                    showgrid=False,
                    showticklabels=False,
                    range=[0, 100],
                    fixedrange=True,
                    zeroline=False
                ),
                yaxis=dict(
                    title='',
                    showticklabels=False,
                    fixedrange=True,
                    autorange='reversed',
                    zeroline=False
                ),
                margin=dict(l=0, r=0, t=10, b=10),
                bargap=0.2,
                hovermode=False,
                autosize=True
            )
            
            # Accord bars in right column
            st.plotly_chart(fig_accords, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
    
    st.markdown("<div style='margin: 30px 0;'></div>", unsafe_allow_html=True)
    
    # Perfume Pyramid (Top, Heart, Base Notes)
    st.markdown('''
        <div style="margin-bottom: 30px; text-align: center;">
            <h3 style="color: #6b5b95; 
                       margin: 0; 
                       font-size: 32px; 
                       font-weight: 700;
                       letter-spacing: 1px;
                       text-transform: uppercase;
                       border-bottom: 5px solid #6b5b95;
                       padding-bottom: 18px;
                       display: inline-block;
                       min-width: 60%;">
                Perfume Pyramid
            </h3>
                </div>
            ''', unsafe_allow_html=True)
    
    # Custom CSS for note cards
    st.markdown("""
        <style>
        .note-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f7fa 100%);
            border-radius: 14px;
            padding: 14px 18px;
            margin: 10px 0;
            display: flex;
            align-items: center;
            box-shadow: 0 2px 8px rgba(107, 91, 149, 0.1);
            transition: all 0.3s ease;
            border: 1px solid #e8e4f0;
        }
        .note-icon {
            width: 50px;
            height: 50px;
            border-radius: 12px;
            margin-right: 16px;
            object-fit: cover;
            background: linear-gradient(135deg, #e8e4f0 0%, #f8f7fa 100%);
            padding: 10px;
            box-shadow: inset 0 2px 4px rgba(107, 91, 149, 0.1);
        }
        .note-name {
            font-size: 16px;
            color: #2c2c2c;
            font-weight: 600;
            letter-spacing: 0.3px;
        }
        .note-category-title {
            font-size: 18px;
            font-weight: 700;
            color: #6b5b95;
            margin-bottom: 15px;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            padding: 12px;
            background: linear-gradient(135deg, #f8f7fa 0%, #e8e4f0 100%);
            border-radius: 10px;
            border: 2px solid #d4c4db;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col_top, col_heart, col_base = st.columns(3)
    
    with col_top:
        st.markdown('<div class="note-category-title">Top Notes</div>', unsafe_allow_html=True)
        for note in perfume['top_notes']:
            if isinstance(note, dict):
                note_name = note.get('name', '')
                note_image = note.get('imageUrl', '')
                if note_image:
                    st.markdown(f"""
                        <div class="note-card">
                            <img src="{note_image}" class="note-icon">
                            <span class="note-name">{note_name}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="note-card">
                            <div class="note-icon"></div>
                            <span class="note-name">{note_name}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="note-card">
                        <div class="note-icon"></div>
                        <span class="note-name">{note}</span>
                    </div>
                """, unsafe_allow_html=True)
    
    with col_heart:
        st.markdown('<div class="note-category-title">Heart Notes</div>', unsafe_allow_html=True)
        for note in perfume['heart_notes']:
            if isinstance(note, dict):
                note_name = note.get('name', '')
                note_image = note.get('imageUrl', '')
                if note_image:
                    st.markdown(f"""
                        <div class="note-card">
                            <img src="{note_image}" class="note-icon">
                            <span class="note-name">{note_name}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="note-card">
                            <div class="note-icon"></div>
                            <span class="note-name">{note_name}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="note-card">
                        <div class="note-icon"></div>
                        <span class="note-name">{note}</span>
                    </div>
                """, unsafe_allow_html=True)
    
    with col_base:
        st.markdown('<div class="note-category-title">Base Notes</div>', unsafe_allow_html=True)
        for note in perfume['base_notes']:
            if isinstance(note, dict):
                note_name = note.get('name', '')
                note_image = note.get('imageUrl', '')
                if note_image:
                    st.markdown(f"""
                        <div class="note-card">
                            <img src="{note_image}" class="note-icon">
                            <span class="note-name">{note_name}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="note-card">
                            <div class="note-icon"></div>
                            <span class="note-name">{note_name}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="note-card">
                        <div class="note-icon"></div>
                        <span class="note-name">{note}</span>
                    </div>
                """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
    
    # Seasonality with 4 boxes side by side with ranking
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #6b5b95; 
                       margin: 0; 
                       font-size: 32px; 
                       font-weight: 800;
                       text-transform: uppercase;
                       letter-spacing: 3px;
                       padding-bottom: 15px;
                       border-bottom: 5px solid #6b5b95;
                       display: inline-block;
                       min-width: 60%;">
                Seasonality
            </h2>
        </div>
    """, unsafe_allow_html=True)
    
    seasonality = perfume.get('seasonality', {})
    
    # If no seasonality data exists, use defaults
    if not seasonality or all(v == 3 for v in seasonality.values()):
        seasonality = {'Winter': 3, 'Spring': 3, 'Summer': 3, 'Fall': 3}
    
    # Rank seasons from highest to lowest
    ranked_seasons = sorted(seasonality.items(), key=lambda x: x[1], reverse=True)
    
    season_ranks = {season: rank for rank, (season, score) in enumerate(ranked_seasons, 1)}
    
    # Season colors
    season_colors = {
        'Spring': '#b6a6c7',
        'Summer': '#9888b3',
        'Fall': '#7a6a9f',
        'Winter': '#6b5b95'
    }
    
    # Add explanation
    st.markdown("""
        <div style="background: linear-gradient(135deg, #f8f7fa 0%, #ffffff 100%); 
                    padding: 18px 25px; 
                    border-radius: 12px; 
                    border-left: 5px solid #6b5b95; 
                    margin-bottom: 30px;
                    box-shadow: 0 2px 8px rgba(107, 91, 149, 0.08);">
            <p style="margin: 0; color: #555; font-size: 15px; line-height: 1.6; font-weight: 500;">
                <strong style="color: #6b5b95;">What this means:</strong> Rankings show which seasons suit this perfume best. 
                <strong>1 = Best match</strong> for that season's characteristics. Rankings are based on the perfume's notes and intensity.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Season descriptions
    season_info = {
        'Spring': {'desc': 'Fresh & Blooming'},
        'Summer': {'desc': 'Light & Energetic'},
        'Fall': {'desc': 'Warm & Cozy'},
        'Winter': {'desc': 'Rich & Intense'}
    }
    
    # Create ranked order (1 to 4, left to right)
    ranked_seasons_list = sorted(season_ranks.items(), key=lambda x: x[1])
    
    # Build HTML for each season box
    boxes = []
    for season, rank in ranked_seasons_list:
        color = season_colors[season]
        desc = season_info[season]['desc']
        
        box_html = f'<div style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%); padding: 45px 20px; border-radius: 26px; box-shadow: 0 12px 35px rgba(107, 91, 149, 0.3); display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; min-height: 200px; border: 2px solid rgba(255,255,255,0.3);"><div style="background: rgba(255,255,255,0.25); width: 65px; height: 65px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 18px; box-shadow: 0 6px 20px rgba(0,0,0,0.2); border: 2px solid rgba(255,255,255,0.5);"><span style="font-size: 36px; font-weight: 900; color: white; text-shadow: 0 2px 10px rgba(0,0,0,0.3);">{rank}</span></div><h4 style="color: white; margin: 0 0 10px 0; font-size: 18px; font-weight: 800; text-transform: uppercase; letter-spacing: 2.5px; text-shadow: 0 3px 10px rgba(0,0,0,0.3); text-align: center;">{season}</h4><p style="color: rgba(255,255,255,0.95); font-size: 14px; margin: 0; font-weight: 600; letter-spacing: 1px; text-shadow: 0 2px 8px rgba(0,0,0,0.25); text-align: center;">{desc}</p></div>'
        boxes.append(box_html)
    
    st.markdown(f'<div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 20px; margin-bottom: 50px;">{"".join(boxes)}</div>', unsafe_allow_html=True)
    
    # Occasions based on Day/Night usage
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #6b5b95; 
                       margin: 0; 
                       font-size: 32px; 
                       font-weight: 800;
                       text-transform: uppercase;
                       letter-spacing: 3px;
                       padding-bottom: 15px;
                       border-bottom: 5px solid #6b5b95;
                       display: inline-block;
                       min-width: 60%;">
                Occasion
            </h2>
        </div>
    """, unsafe_allow_html=True)
    
    # Add explanation
    st.markdown("""
        <div style="background: linear-gradient(135deg, #f8f7fa 0%, #ffffff 100%); 
                    padding: 18px 25px; 
                    border-radius: 12px; 
                    border-left: 5px solid #6b5b95; 
                    margin-bottom: 30px;
                    box-shadow: 0 2px 8px rgba(107, 91, 149, 0.08);">
            <p style="margin: 0; color: #555; font-size: 15px; line-height: 1.6; font-weight: 500;">
                <strong style="color: #6b5b95;">What this means:</strong> Shows when this perfume works best. 
                <strong>Day</strong> = casual, office, daytime wear. <strong>Night</strong> = evening, formal events, dates.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    occasion = perfume.get('occasion', {'Day': 3, 'Night': 3})
    
    total = occasion.get('Day', 3) + occasion.get('Night', 3)
    day_percent = (occasion.get('Day', 3) / total * 100) if total > 0 else 50.0
    night_percent = (occasion.get('Night', 3) / total * 100) if total > 0 else 50.0
    
    # Format percentages with 1 decimal place
    day_display = f"{day_percent:.1f}%"
    night_display = f"{night_percent:.1f}%"
    
    # Only show label if section is wide enough
    day_label = day_display if day_percent > 5 else ""
    night_label = night_display if night_percent > 5 else ""
    
    # Create purple themed day/night visual
    occasion_html = f"""
        <div style="padding: 40px 60px; background: linear-gradient(135deg, #f8f7fa 0%, #ffffff 100%); border-radius: 20px; box-shadow: 0 8px 30px rgba(107, 91, 149, 0.15); margin: 30px 0; border: 1px solid #e8e4f0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
                <div style="text-align: center; flex: 1;">
                    <div style="font-size: 28px; font-weight: 900; color: #ab9bb9; text-transform: uppercase; letter-spacing: 2px;">DAY</div>
                </div>
                <div style="text-align: center; flex: 1;">
                    <div style="font-size: 28px; font-weight: 900; color: #6b5b95; text-transform: uppercase; letter-spacing: 2px;">NIGHT</div>
                </div>
            </div>
            <div style="position: relative; height: 70px; border-radius: 35px; overflow: hidden; box-shadow: 0 4px 15px rgba(107, 91, 149, 0.2); border: 2px solid #e8e4f0;">
                <div style="position: absolute; top: 0; left: 0; height: 100%; width: {day_percent}%; background: linear-gradient(90deg, #cbbbc9 0%, #ab9bb9 100%); box-shadow: inset 0 2px 8px rgba(255,255,255,0.3);"></div>
                <div style="position: absolute; top: 0; right: 0; height: 100%; width: {night_percent}%; background: linear-gradient(90deg, #8b7aa8 0%, #6b5b95 100%); box-shadow: inset 0 2px 8px rgba(0,0,0,0.1);"></div>
                <div style="position: absolute; top: 0; left: 0; width: {day_percent}%; height: 100%; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 26px; font-weight: 900; color: #fff; text-shadow: 0 2px 8px rgba(107, 91, 149, 0.4); z-index: 10;">{day_label}</span>
                </div>
                <div style="position: absolute; top: 0; right: 0; width: {night_percent}%; height: 100%; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 26px; font-weight: 900; color: #fff; text-shadow: 0 2px 8px rgba(0,0,0,0.3); z-index: 10;">{night_label}</span>
                </div>
            </div>
        </div>
    """
    st.markdown(occasion_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Similar perfume recommendations
    st.markdown('<h3 style="color: #6b5b95;">Similar Perfumes</h3>', unsafe_allow_html=True)
    
    similar_perfumes = get_similar_perfumes(perfume)
    
    if similar_perfumes:
        for i in range(0, len(similar_perfumes), 3):
            col1, col2, col3 = st.columns(3, gap="medium")
            
            with col1:
                if i < len(similar_perfumes):
                    display_perfume_card(similar_perfumes[i], show_ml_badge=True, source='current', card_index=i)
            
            with col2:
                if i + 1 < len(similar_perfumes):
                    display_perfume_card(similar_perfumes[i + 1], show_ml_badge=True, source='current', card_index=i+1)
            
            with col3:
                if i + 2 < len(similar_perfumes):
                    display_perfume_card(similar_perfumes[i + 2], show_ml_badge=True, source='current', card_index=i+2)

def get_similar_perfumes(perfume: Dict, limit: int = 4) -> List[Dict]:
    """
    Get similar perfumes based on scent type, gender etc.
    """
    all_perfumes = st.session_state.perfume_database
    similar = []
    
    for p in all_perfumes:
        # Skip the same perfume
        if p['id'] == perfume['id']:
            continue
        
        score = 0
        
        # Same scent type (high weight)
        if p['scent_type'] == perfume['scent_type']:
            score += 3
        
        # Same gender
        if p['gender'] == perfume['gender'] or p['gender'] == 'Unisex' or perfume['gender'] == 'Unisex':
            score += 2
        
        # Similar price range (+/- $30)
        if abs(p['price'] - perfume['price']) <= 30:
            score += 1
        
        # Match search context filters if available
        if st.session_state.search_context:
            if 'brand' in st.session_state.search_context:
                if p['brand'] in st.session_state.search_context['brand']:
                    score += 1
            
            if 'scent_type' in st.session_state.search_context:
                if p['scent_type'] in st.session_state.search_context['scent_type']:
                    score += 2
        
        if score > 0:
            similar.append((p, score))
    
    # Sort by score and return top matches
    similar.sort(key=lambda x: x[1], reverse=True)
    
    # Apply ML ranking to similar perfumes
    similar_perfumes = [p for p, score in similar[:limit * 2]]
    ml_sorted = get_ml_sorted_perfumes(similar_perfumes)
    
    return ml_sorted[:limit]

def render_questionnaire_section():
    """Questionnaire page with preference sliders"""
    st.markdown('<div id="page-top" style="height: 1px;"></div>', unsafe_allow_html=True)
    
    if st.session_state.show_perfume_details and st.session_state.current_perfume:
        render_perfume_detail_view(st.session_state.current_perfume)
        return
    
    if st.session_state.show_questionnaire_results:
        render_questionnaire_results()
        return
    
    render_back_button("home", "Back to Home")
    
    st.markdown('<h2 style="color: #6b5b95;">Perfume Questionnaire</h2>', unsafe_allow_html=True)
    st.write("Answer these questions to discover your perfect scent profile.")
    
    st.markdown("---")
    
    questions = [
        {
            "id": "intensity",
            "title": "Question 1 of 5",
            "left_label": "1 - Subtle",
            "right_label": "5 - Strong/Noticeable",
            "key": "q1_intensity"
        },
        {
            "id": "warmth",
            "title": "Question 2 of 5",
            "left_label": "1 - Fresh/Light",
            "right_label": "5 - Warm/Intense",
            "key": "q2_warmth"
        },
        {
            "id": "sweetness",
            "title": "Question 3 of 5",
            "left_label": "1 - Dry/Herbal",
            "right_label": "5 - Sweet/Gourmand",
            "key": "q3_sweetness"
        },
        {
            "id": "occasion",
            "title": "Question 4 of 5",
            "left_label": "1 - Daily/Office",
            "right_label": "5 - Evening/Event/Date",
            "key": "q4_occasion"
        },
        {
            "id": "character",
            "title": "Question 5 of 5",
            "left_label": "1 - Feminine",
            "right_label": "5 - Masculine",
            "key": "q5_character"
        }
    ]
    
    current_q = questions[st.session_state.current_question]
    
    # Ensure current question starts at middle position (3) if not answered yet
    if current_q['id'] not in st.session_state.questionnaire_answers:
        st.session_state.questionnaire_answers[current_q['id']] = 3
    
    st.markdown(f'<h3 style="color: #6b5b95;">{current_q["title"]}</h3>', unsafe_allow_html=True)
    st.markdown('<div class="bipolar-slider">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="bipolar-label" style="text-align: left;">{current_q["left_label"]}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="bipolar-label" style="text-align: right;">{current_q["right_label"]}</div>', unsafe_allow_html=True)
    
    # Slider graphic
    answer = st.slider(
        "Move slider to select",
        min_value=1,
        max_value=5,
        value=st.session_state.questionnaire_answers.get(current_q['id'], 3),
        step=1,
        key=current_q['key'],
        label_visibility="collapsed",
        format=""
    )
    
    # Custom numbers below the slider
    st.markdown("""
    <div class="scale-numbers">
        <span>1</span>
        <span>2</span>
        <span>3</span>
        <span>4</span>
        <span>5</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Store answer
    st.session_state.questionnaire_answers[current_q['id']] = answer
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation buttons
    col_back, col_next = st.columns(2)
    
    with col_back:
        if st.session_state.current_question > 0:
            if st.button("← Back", key="q_back", use_container_width=True):
                st.session_state.current_question -= 1
                # Set previous question's slider to middle position (3) if not answered yet
                prev_question_id = questions[st.session_state.current_question]['id']
                if prev_question_id not in st.session_state.questionnaire_answers:
                    st.session_state.questionnaire_answers[prev_question_id] = 3
                st.rerun()
    
    with col_next:
        if st.session_state.current_question < len(questions) - 1:
            if st.button("Next →", key="q_next", use_container_width=True):
                st.session_state.current_question += 1
                # Set next question's slider to middle position (3) if not answered yet
                next_question_id = questions[st.session_state.current_question]['id']
                if next_question_id not in st.session_state.questionnaire_answers:
                    st.session_state.questionnaire_answers[next_question_id] = 3
                st.rerun()
        else:
            if st.button("Submit", key="q_submit", use_container_width=True):
                st.session_state.show_questionnaire_results = True
                st.rerun()

def render_questionnaire_results():
    """Display questionnaire results with radar chart and recommendations"""
    st.markdown('<div id="page-top" style="height: 1px;"></div>', unsafe_allow_html=True)
    
    if st.button("← Back to Questionnaire", key="back_from_results", use_container_width=True):
        st.session_state.show_questionnaire_results = False
        st.session_state.current_question = 0  # Start from first question
        st.session_state.questionnaire_answers = {}  # Reset all answers to start fresh
        st.rerun()
    
    st.markdown('<h2 style="color: #6b5b95;">Your Scent Profile</h2>', unsafe_allow_html=True)
    
    answers = st.session_state.questionnaire_answers
    
    st.markdown('<h3 style="color: #6b5b95;">Profile Visualization</h3>', unsafe_allow_html=True)
    
    categories = ['Intensity', 'Warmth', 'Sweetness', 'Occasion', 'Gender']
    values = [
        answers.get('intensity', 3),
        answers.get('warmth', 3),
        answers.get('sweetness', 3),
        answers.get('occasion', 3),
        answers.get('character', 3)
    ]
    
    values += values[:1]
    categories += categories[:1]
    
    fig_radar = go.Figure()
    
    fig_radar.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(107, 91, 149, 0.3)',
        line=dict(color='#6b5b95', width=3),
        name='Your Profile'
    ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickmode='linear',
                tick0=0,
                dtick=1
            )
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=14, color='#333')
    )
    
    st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
    
    st.markdown("---")
    st.markdown('<h3 style="color: #6b5b95;">Recommended Perfumes</h3>', unsafe_allow_html=True)
    
    recommendations = get_questionnaire_recommendations()
    
    if recommendations:
        st.success(f"Based on your profile, we found {len(recommendations)} perfume(s) for you")
        
        for i in range(0, len(recommendations), 3):
            col1, col2, col3 = st.columns(3, gap="medium")
            
            with col1:
                if i < len(recommendations):
                    display_perfume_card(recommendations[i], show_ml_badge=True, source='questionnaire', card_index=i)
            
            with col2:
                if i + 1 < len(recommendations):
                    display_perfume_card(recommendations[i + 1], show_ml_badge=True, source='questionnaire', card_index=i+1)
            
            with col3:
                if i + 2 < len(recommendations):
                    display_perfume_card(recommendations[i + 2], show_ml_badge=True, source='questionnaire', card_index=i+2)
    else:
        st.info("We couldn't find perfect matches. Try browsing our search section.")

def get_questionnaire_recommendations() -> List[Dict]:
    """Get perfume recommendations based on questionnaire scoring system"""
    answers = st.session_state.questionnaire_answers
    all_perfumes = st.session_state.perfume_database
    scored_perfumes = []
    
    for perfume in all_perfumes:
        score = 0
        
        intensity = answers.get('intensity', 3)
        if intensity <= 2:
            if perfume['scent_type'] in ['Fresh', 'Citrus', 'Green']:
                score += 3
        elif intensity >= 4:
            if perfume['scent_type'] in ['Oriental', 'Leather', 'Woody']:
                score += 3
        else:
            score += 1
        
        warmth = answers.get('warmth', 3)
        if warmth <= 2:
            if perfume['scent_type'] in ['Fresh', 'Citrus', 'Green']:
                score += 3
        elif warmth >= 4:
            if perfume['scent_type'] in ['Oriental', 'Gourmand', 'Woody']:
                score += 3
        
        sweetness = answers.get('sweetness', 3)
        if sweetness <= 2:
            if perfume['scent_type'] in ['Green', 'Woody', 'Fresh']:
                score += 3
        elif sweetness >= 4:
            if perfume['scent_type'] in ['Gourmand', 'Floral']:
                score += 3
        
        occasion = answers.get('occasion', 3)
        occasion_scores = perfume.get('occasion', {'Day': 3, 'Night': 3})
        if occasion <= 2:
            score += occasion_scores.get('Day', 3)
        elif occasion >= 4:
            score += occasion_scores.get('Night', 3)
        else:
            score += 1
        
        character = answers.get('character', 3)
        if character <= 2:
            if perfume['gender'] == 'Female':
                score += 3
            elif perfume['gender'] == 'Unisex':
                score += 1
        elif character >= 4:
            if perfume['gender'] == 'Male':
                score += 3
            elif perfume['gender'] == 'Unisex':
                score += 1
        else:
            if perfume['gender'] == 'Unisex':
                score += 3
        
        scored_perfumes.append((perfume, score))
    
    scored_perfumes.sort(key=lambda x: x[1], reverse=True)
    top_perfumes = [p for p, score in scored_perfumes if score >= 5][:8]
    
    return get_ml_sorted_perfumes(top_perfumes)

def render_inventory_section():
    """Inventory page with collection stats and ML recommendations"""
    st.markdown('<div id="page-top" style="height: 1px;"></div>', unsafe_allow_html=True)
    
    
    # Continuing with normal rendering
    if st.session_state.show_perfume_details and st.session_state.current_perfume:
        render_perfume_detail_view(st.session_state.current_perfume)
        return
    
    if 'adding_perfume' in st.session_state and st.session_state.adding_perfume:
        render_add_perfume_view()
        return
    
    render_back_button("home", "Back to Home")
    
    st.markdown('<h2 style="color: #6b5b95;">My Perfumes</h2>', unsafe_allow_html=True)
    
    # Show success message if perfume was just added
    if st.session_state.get('show_add_success', False):
        perfume_name = st.session_state.get('added_perfume_name', 'Perfume')
        st.success(f"Added **{perfume_name}** to your collection!")
        st.session_state.show_add_success = False
    
    inventory = st.session_state.user_inventory
    
    # Show inventory count
    st.caption(f"You have {len(inventory)} perfume(s) in your collection")
    
    if not inventory:
        st.info("Your perfume collection is empty. Click the + button below to add perfumes.")
    
    # First item is "Add" button
    cols_per_row = 3
    all_items = ['add'] + inventory
    
    for i in range(0, len(all_items), cols_per_row):
        cols = st.columns(cols_per_row, gap="medium")
        
        for j in range(cols_per_row):
            idx = i + j
            if idx < len(all_items):
                with cols[j]:
                    if all_items[idx] == 'add':
                        st.markdown("""
                            <div class="perfume-card" style="padding: 15px; height: 420px; display: flex; flex-direction: column; justify-content: center; align-items: center; background: white; border: 3px dashed #6b5b95; border-radius: 12px; width: 100%; box-sizing: border-box; margin-bottom: 8px;">
                                <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                                    <p style="font-size: 60px; color: #6b5b95; margin: 0; line-height: 1;">+</p>
                                    <p style="color: #6b5b95; margin-top: 15px; font-weight: 600; font-size: 16px; text-align: center;">Add Perfume</p>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("Add New", key="btn_add_perfume", use_container_width=True, type="primary"):
                            st.session_state.active_section = "search"
                            st.session_state.search_query = ""
                            st.rerun()
                    else:
                        try:
                            display_inventory_perfume_card(all_items[idx], idx - 1)
                        except Exception as e:
                            st.error(f"Error displaying perfume: {str(e)}")
    
    if inventory:
        st.markdown("---")
        render_inventory_statistics(inventory)
        
        if len(inventory) >= ML_CONFIG['min_inventory_size']:
            st.markdown("---")
            render_ml_recommendations_in_inventory(inventory)

def render_add_perfume_view():
    """View for adding perfumes with search functionality"""
    st.markdown('<div id="page-top" style="height: 1px;"></div>', unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to Inventory", key="back_from_add", use_container_width=True):
        st.session_state.adding_perfume = False
        st.rerun()
    
    st.markdown('<h2 style="color: #6b5b95;">Add Perfume to Collection</h2>', unsafe_allow_html=True)
    
    # Search bar
    add_search = st.text_input(
        "Search for perfume to add (minimum 3 characters)",
        placeholder="Enter perfume name or brand...",
        key="add_search_input"
    )
    
    st.markdown("---")
    
    if add_search and len(add_search) >= 3:
        # Do live API search
        with st.spinner("Searching Fragella database..."):
            api_results = search_fragella_perfumes(FRAGELLA_API_KEY, add_search, limit=20)
            if api_results:
                # Transform results
                filtered = [transform_api_perfume(p) for p in api_results]
                for perfume in filtered:
                    if not any(p['id'] == perfume['id'] for p in st.session_state.perfume_database):
                        st.session_state.perfume_database.append(perfume)
            else:
                filtered = []
    else:
        filtered = st.session_state.perfume_database[:20]  # Limit to first 20
        if add_search and len(add_search) < 3:
            st.info("Please enter at least 3 characters to search")
    
    st.write(f"Found {len(filtered)} perfume(s)")
    
    for i in range(0, len(filtered), 3):
        col1, col2, col3 = st.columns(3, gap="medium")
        
        with col1:
            if i < len(filtered):
                display_addable_perfume_card(filtered[i])
        
        with col2:
            if i + 1 < len(filtered):
                display_addable_perfume_card(filtered[i + 1])
        
        with col3:
            if i + 2 < len(filtered):
                display_addable_perfume_card(filtered[i + 2])

def render_inventory_statistics(inventory: List[Dict]):
    """
    Render statistics and analytics for user's perfume collection.
    Displays donut charts for notes and bar charts for seasonality and occasion.
    
    """
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #6b5b95; 
                       margin: 0; 
                       font-size: 32px; 
                       font-weight: 800;
                       text-transform: uppercase;
                       letter-spacing: 3px;
                       padding-bottom: 15px;
                       border-bottom: 5px solid #6b5b95;
                       display: inline-block;
                       min-width: 60%;">
                Collection Statistics
            </h2>
        </div>
    """, unsafe_allow_html=True)
    
    # Add overall explanation
    st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.95); 
                    padding: 18px 25px; 
                    border-radius: 12px; 
                    border-left: 5px solid #6b5b95; 
                    margin-bottom: 30px;
                    box-shadow: 0 2px 8px rgba(107, 91, 149, 0.08);">
            <p style="margin: 0 0 15px 0; color: #555; font-size: 15px; line-height: 1.6; font-weight: 500;">
                <strong style="color: #6b5b95;">Understanding Your Collection:</strong> These charts analyze ALL perfumes in your collection to reveal patterns and preferences:
            </p>
            <ul style="color: #555; font-size: 15px; line-height: 1.8; margin: 0; padding-left: 25px;">
                <li><strong>Note Distribution:</strong> Shows which scent notes appear most frequently in your collection</li>
                <li><strong>Seasonality:</strong> Combines all perfume season ratings (1-5 stars each) to show which seasons your collection suits best</li>
                <li><strong>Occasion:</strong> Aggregates Day/Night suitability across all your perfumes to see if your collection leans casual or formal</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    # Donut charts for notes
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #6b5b95; 
                       margin: 0; 
                       font-size: 32px; 
                       font-weight: 800;
                       text-transform: uppercase;
                       letter-spacing: 3px;
                       padding-bottom: 15px;
                       border-bottom: 5px solid #6b5b95;
                       display: inline-block;
                       min-width: 60%;">
                Note Distribution
            </h2>
        </div>
    """, unsafe_allow_html=True)
    
    # Collect all notes
    top_notes = []
    heart_notes = []
    base_notes = []
    
    for perfume in inventory:
        # Handle both dict format (from API) and string format (old data)
        for note in perfume['top_notes']:
            top_notes.append(note['name'] if isinstance(note, dict) else note)
        for note in perfume['heart_notes']:
            heart_notes.append(note['name'] if isinstance(note, dict) else note)
        for note in perfume['base_notes']:
            base_notes.append(note['name'] if isinstance(note, dict) else note)
    
    # Create three columns for donut charts
    col_top, col_heart, col_base = st.columns(3)
    
    with col_top:
        st.markdown("**Top Notes**")
        top_counter = Counter(top_notes)
        create_donut_chart(top_counter, "Top Notes")
    
    with col_heart:
        st.markdown("**Heart Notes**")
        heart_counter = Counter(heart_notes)
        create_donut_chart(heart_counter, "Heart Notes")
    
    with col_base:
        st.markdown("**Base Notes**")
        base_counter = Counter(base_notes)
        create_donut_chart(base_counter, "Base Notes")
    
    st.markdown("---")
    
    # Seasonality based on count of perfumes by their most useful season
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #6b5b95; 
                       margin: 0; 
                       font-size: 32px; 
                       font-weight: 800;
                       text-transform: uppercase;
                       letter-spacing: 3px;
                       padding-bottom: 15px;
                       border-bottom: 5px solid #6b5b95;
                       display: inline-block;
                       min-width: 60%;">
                Seasonality
            </h2>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.95); 
                    padding: 18px 25px; 
                    border-radius: 12px; 
                    border-left: 5px solid #6b5b95; 
                    margin-bottom: 30px;
                    box-shadow: 0 2px 8px rgba(107, 91, 149, 0.08);">
            <p style="margin: 0; color: #555; font-size: 15px; line-height: 1.6; font-weight: 500;">
                <strong style="color: #6b5b95;">What this means:</strong> Each perfume is counted toward its most suitable season
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Count perfumes by their best season
    season_counts = {'Winter': 0, 'Fall': 0, 'Spring': 0, 'Summer': 0}
    
    for perfume in inventory:
        seasonality = perfume.get('seasonality', {'Winter': 3, 'Spring': 3, 'Summer': 3, 'Fall': 3})
        # Find the best season for this perfume
        best_season = max(seasonality.items(), key=lambda x: x[1])
        season_counts[best_season[0]] += 1
    
    # Sort by count (highest first)
    sorted_seasons = sorted(season_counts.items(), key=lambda x: x[1], reverse=True)
    seasons = [s[0] for s in sorted_seasons]
    values = [s[1] for s in sorted_seasons]
    
    # Season-specific colors
    season_colors = {
        'Spring': '#b6a6c7',
        'Summer': '#9888b3',
        'Fall': '#7a6a9f',
        'Winter': '#6b5b95'
    }
    colors = [season_colors.get(s, '#8b7aa8') for s in seasons]
    
    fig_season = go.Figure()
    
    for i, (season, value) in enumerate(zip(seasons, values)):
        fig_season.add_trace(go.Bar(
            y=[season],
            x=[value],
            orientation='h',
            marker=dict(
                color=colors[i]
            ),
            showlegend=False,
            text=f'<b>{value} perfume{"s" if value != 1 else ""}</b>',
            textposition='inside',
            insidetextanchor='middle',
            textfont=dict(size=18, color='white', family='Poppins, sans-serif'),
            hovertemplate=f'<b>{season}</b><br>{value} perfume{"s" if value != 1 else ""}<br><extra></extra>'
        ))
    
    fig_season.update_layout(
        height=300,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#6b5b95', size=16, family='Poppins, sans-serif'),
        xaxis=dict(
            title='',
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        yaxis=dict(
            title='',
            tickfont=dict(size=16, color='#6b5b95', family='Poppins, sans-serif'),
            showgrid=False
        ),
        margin=dict(l=100, r=40, t=20, b=40),
        bargap=0.25
    )
    
    st.plotly_chart(fig_season, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
    
    # Occasion visual
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #6b5b95; 
                       margin: 0; 
                       font-size: 32px; 
                       font-weight: 800;
                       text-transform: uppercase;
                       letter-spacing: 3px;
                       padding-bottom: 15px;
                       border-bottom: 5px solid #6b5b95;
                       display: inline-block;
                       min-width: 60%;">
                Occasion
            </h2>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.95); 
                    padding: 18px 25px; 
                    border-radius: 12px; 
                    border-left: 5px solid #6b5b95; 
                    margin-bottom: 30px;
                    box-shadow: 0 2px 8px rgba(107, 91, 149, 0.08);">
            <p style="margin: 0; color: #555; font-size: 15px; line-height: 1.6; font-weight: 500;">
                <strong style="color: #6b5b95;">What this means:</strong> How your collection balances between casual daytime and elegant evening wear
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Aggregate occasion scores
    occasion_totals = {'Day': 0, 'Night': 0}
    
    for perfume in inventory:
        for occasion, score in perfume.get('occasion', {'Day': 3, 'Night': 3}).items():
            if occasion in occasion_totals:
                occasion_totals[occasion] += score
    
    total = occasion_totals['Day'] + occasion_totals['Night']
    day_percent = (occasion_totals['Day'] / total * 100) if total > 0 else 50.0
    night_percent = (occasion_totals['Night'] / total * 100) if total > 0 else 50.0
    
    # Format percentages with 1 decimal place
    day_display = f"{day_percent:.1f}%"
    night_display = f"{night_percent:.1f}%"
    
    # Only show label if section is wide enough
    day_label = day_display if day_percent > 5 else ""
    night_label = night_display if night_percent > 5 else ""
    
    # Create purple-themed day/night visual
    occasion_html = f"""
        <div style="padding: 40px 60px; background: linear-gradient(135deg, #f8f7fa 0%, #ffffff 100%); border-radius: 20px; box-shadow: 0 8px 30px rgba(107, 91, 149, 0.15); margin: 30px 0; border: 1px solid #e8e4f0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
                <div style="text-align: center; flex: 1;">
                    <div style="font-size: 28px; font-weight: 900; color: #ab9bb9; text-transform: uppercase; letter-spacing: 2px;">DAY</div>
                </div>
                <div style="text-align: center; flex: 1;">
                    <div style="font-size: 28px; font-weight: 900; color: #6b5b95; text-transform: uppercase; letter-spacing: 2px;">NIGHT</div>
                </div>
            </div>
            <div style="position: relative; height: 70px; border-radius: 35px; overflow: hidden; box-shadow: 0 4px 15px rgba(107, 91, 149, 0.2); border: 2px solid #e8e4f0;">
                <div style="position: absolute; top: 0; left: 0; height: 100%; width: {day_percent}%; background: linear-gradient(90deg, #cbbbc9 0%, #ab9bb9 100%); box-shadow: inset 0 2px 8px rgba(255,255,255,0.3);"></div>
                <div style="position: absolute; top: 0; right: 0; height: 100%; width: {night_percent}%; background: linear-gradient(90deg, #8b7aa8 0%, #6b5b95 100%); box-shadow: inset 0 2px 8px rgba(0,0,0,0.1);"></div>
                <div style="position: absolute; top: 0; left: 0; width: {day_percent}%; height: 100%; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 26px; font-weight: 900; color: #fff; text-shadow: 0 2px 8px rgba(107, 91, 149, 0.4); z-index: 10;">{day_label}</span>
                </div>
                <div style="position: absolute; top: 0; right: 0; width: {night_percent}%; height: 100%; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 26px; font-weight: 900; color: #fff; text-shadow: 0 2px 8px rgba(0,0,0,0.3); z-index: 10;">{night_label}</span>
                </div>
            </div>
        </div>
    """
    st.markdown(occasion_html, unsafe_allow_html=True)

# ML recommendations in the inventory
def render_ml_recommendations_in_inventory(inventory: List[Dict]):
    """Render ML-powered recommendations at the bottom of inventory section"""
    
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #6b5b95; 
                       margin: 0; 
                       font-size: 32px; 
                       font-weight: 800;
                       text-transform: uppercase;
                       letter-spacing: 3px;
                       padding-bottom: 15px;
                       border-bottom: 5px solid #6b5b95;
                       display: inline-block;
                       min-width: 60%;">
                Recommendations Based on Your Scent Profile
            </h2>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.95); 
                    padding: 18px 25px; 
                    border-radius: 12px; 
                    border-left: 5px solid #6b5b95; 
                    margin-bottom: 30px;
                    box-shadow: 0 2px 8px rgba(107, 91, 149, 0.08);">
            <p style="margin: 0; color: #555; font-size: 15px; line-height: 1.6; font-weight: 500;">
                <strong style="color: #6b5b95;">What this means:</strong> Machine learning analyzes your collection to suggest personalized perfumes.
            </p>
            <p style="margin: 10px 0 0 0; color: #666; font-size: 14px; line-height: 1.5;">
                <strong>To add these perfumes:</strong> Use the search function below to find them by name.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Add "Go to Search" button right after description
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Search Recommended Perfumes", key="ml_to_search", use_container_width=True, type="primary"):
            st.session_state.active_section = "search"
            st.rerun()
    
    st.markdown('<div style="margin-top: 30px; margin-bottom: 20px;"></div>', unsafe_allow_html=True)
    
    all_perfumes = st.session_state.perfume_database
    
    # Auto-create recommendations (no button needed)
    with st.spinner("Analyzing your collection..."):
        recommendations = get_ml_recommendations(
            inventory, 
            all_perfumes, 
            ML_CONFIG,
            ML_MODEL_FILE,
            ML_SCALER_FILE,
            top_n=6,  # Show 6 recommendations
            ensure_diversity=True
        )
    
    if not recommendations:
        st.info("No strong matches found in the catalog. Keep adding perfumes to improve recommendations!")
        return
    
    # Display the recommendations in a simple grid
    st.write(f"Showing {len(recommendations)} personalized recommendations")
    
    for i in range(0, len(recommendations), 3):
        cols = st.columns(3)
        
        for j in range(3):
            idx = i + j
            if idx < len(recommendations):
                perfume = recommendations[idx]
                
                with cols[j]:
                    # ML Score badge
                    match_score = int(perfume['ml_score'] * 100)
                    badge_color = "#4CAF50" if match_score >= 80 else "#6b5b95" if match_score >= 70 else "#888"
                    
                    image_url = perfume.get('image_url', '')
                    if not image_url:
                        image_url = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjI1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjI1MCIgZmlsbD0iI2U4ZTRmMCIvPjxwYXRoIGQ9Ik04MCA2MGgyMHY0MEg4MHoiIGZpbGw9IiM2YjViOTUiLz48cmVjdCB4PSI2MCIgeT0iMTAwIiB3aWR0aD0iNjAiIGhlaWdodD0iMTIwIiByeD0iMTAiIGZpbGw9IiM2YjViOTUiIG9wYWNpdHk9IjAuOCIvPjxyZWN0IHg9IjcwIiB5PSIxMTAiIHdpZHRoPSI0MCIgaGVpZ2h0PSI5MCIgZmlsbD0iI2M4YjhkOCIgb3BhY2l0eT0iMC42Ci8+PC9zdmc+'
                    
                    gender = perfume.get('gender', 'UNISEX').upper()
                    perfume_name = perfume.get('name', 'Unknown')
                    perfume_brand = perfume.get('brand', 'Unknown')
                    accords = perfume.get('main_accords', ['Fresh', 'Floral'])[:3]
                    accords_str = ', '.join(accords)
                    perfume_type = perfume.get('perfume_type', 'Eau de Parfum')
                    
                    # Card with green match badge at top
                    card_html = f"""<div style="background: linear-gradient(135deg, #ffffff 0%, #fafafa 100%); border-radius: 16px; padding: 0; overflow: hidden; box-shadow: 0 2px 12px rgba(107, 91, 149, 0.08); border: 1px solid #e8e4f0; height: 420px; display: flex; flex-direction: column; width: 100%; box-sizing: border-box; margin-bottom: 8px;">
    <div style="padding: 15px; background: linear-gradient(180deg, #f8f7fa 0%, transparent 100%);">
        <div style="display: flex; justify-content: flex-start; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 10px; min-height: 26px;">
            <div style="background: {badge_color}; padding: 8px 18px; border-radius: 20px; box-shadow: 0 3px 10px rgba(76, 175, 80, 0.3);">
                <span style="color: white; font-size: 14px; font-weight: 800; letter-spacing: 0.8px; text-transform: uppercase; white-space: nowrap;">{match_score}%</span>
                            </div>
            <div style="background: linear-gradient(135deg, #ab9bb9 0%, #8b7aa8 100%); padding: 6px 14px; border-radius: 20px; box-shadow: 0 2px 8px rgba(107, 91, 149, 0.2);">
                <span style="color: white; font-size: 10px; font-weight: 700; letter-spacing: 0.6px; text-transform: uppercase; white-space: nowrap;">{perfume_type}</span>
                            </div>
            <span style="background: linear-gradient(135deg, #6b5b95 0%, #8b7aa8 100%); color: white; padding: 6px 14px; border-radius: 20px; font-size: 10px; font-weight: 700; letter-spacing: 0.6px; text-transform: uppercase; box-shadow: 0 2px 8px rgba(107, 91, 149, 0.2); white-space: nowrap;">{gender}</span>
                            </div>
        <div style="height: 140px; width: 100%; display: flex; align-items: center; justify-content: center; overflow: hidden;">
            <img src="{image_url}" style="max-width: 130px; max-height: 130px; width: auto; height: auto; object-fit: contain; filter: drop-shadow(0 4px 12px rgba(107, 91, 149, 0.12));">
                        </div>
    </div>
    <div style="flex: 1; padding: 14px 16px 16px 16px; display: flex; flex-direction: column; align-items: center; justify-content: space-between;">
        <div style="width: 100%; text-align: center; min-height: 60px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 12px;">
            <h3 style="color: #2c2c2c; margin: 0 0 5px 0; font-size: 16px; font-weight: 600; line-height: 1.3; letter-spacing: -0.2px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{perfume_name}</h3>
            <p style="color: #6b5b95; font-style: italic; font-size: 13px; margin: 0; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">by {perfume_brand}</p>
        </div>
        <div style="width: 100%; background: linear-gradient(135deg, #f8f7fa 0%, #ffffff 100%); padding: 10px; border-radius: 12px; border: 1px solid #e8e4f0; min-height: 65px; display: flex; flex-direction: column; justify-content: center;">
            <p style="font-size: 9px; color: #8b7aa8; margin: 0 0 5px 0; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; text-align: center;">Accords</p>
            <p style="text-align: center; color: #6b5b95; font-size: 12px; font-weight: 600; margin: 0; line-height: 1.3; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{accords_str}</p>
        </div>
    </div>
</div>"""
                    
                    st.markdown(card_html, unsafe_allow_html=True)


# Main Scentify application
def main():
    """
    Main entry point which gets called when running the app.
    """
    # Apply all the custom CSS styling
    apply_custom_styling()
    
    initialize_session_state()
    
    render_header()
    
    # Figure out which page to show based on what button was clicked
    if st.session_state.active_section == "home":
        render_landing_page()
        
    elif st.session_state.active_section == "search":
        render_search_section()
        
    elif st.session_state.active_section == "questionnaire":
        render_questionnaire_section()
        
    elif st.session_state.active_section == "inventory":
        render_inventory_section()
    
    # Footer
    st.markdown("""
        <div style="text-align: center; margin-top: 60px; padding: 20px 0; color: #6b5b95; font-size: 14px; font-weight: 400;">
            made with love by Jil, Diego, Luis, Livio and Micha
        </div>
    """, unsafe_allow_html=True)


# Run Application
if __name__ == "__main__":
    main()
