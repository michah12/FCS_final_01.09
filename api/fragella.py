"""
Fragella API Integration
Functions for calling the Fragella API and transforming perfume data
"""
import streamlit as st
import requests
from typing import Optional, List, Dict


def call_fragella_api(api_key: str, endpoint: str, params: Optional[Dict] = None) -> Optional[List[Dict]]:
    """Call Fragella API and return perfume data"""
    headers = {
        "x-api-key": api_key
    }
    
    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=15)
        
        response.raise_for_status()
        
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.warning(f"API returned 404 - Perfume not found or API endpoint changed. Try a different search term.")
        else:
            st.error(f"API Error: {str(e)}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {str(e)}")
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def search_fragella_perfumes(api_key: str, query: str, limit: int = 20) -> List[Dict]:
    """Search Fragella API for perfumes matching query (min 3 chars)"""
    if len(query) < 3:
        return []
    
    endpoint = "https://api.fragella.com/api/v1/fragrances"
    params = {
        "search": query,
        "limit": min(limit, 20)
    }
    
    result = call_fragella_api(api_key, endpoint, params)
    
    if result:
        return result
    else:
        return []


def transform_api_perfume(api_perfume: Dict) -> Dict:
    """Transform API perfume data to internal format"""
    notes_obj = api_perfume.get('Notes', {})
    top_notes = []
    heart_notes = []
    base_notes = []
    
    if notes_obj:
        if 'Top' in notes_obj and notes_obj['Top']:
            top_notes = [{'name': note.get('name', ''), 'imageUrl': note.get('imageUrl', '')} 
                        for note in notes_obj['Top'] if note.get('name')]
        
        if 'Middle' in notes_obj and notes_obj['Middle']:
            heart_notes = [{'name': note.get('name', ''), 'imageUrl': note.get('imageUrl', '')} 
                          for note in notes_obj['Middle'] if note.get('name')]
        
        if 'Base' in notes_obj and notes_obj['Base']:
            base_notes = [{'name': note.get('name', ''), 'imageUrl': note.get('imageUrl', '')} 
                         for note in notes_obj['Base'] if note.get('name')]
    
    seasonality = {}
    season_ranking = api_perfume.get('Season Ranking', api_perfume.get('SeasonRanking', api_perfume.get('season_ranking', [])))
    
    if season_ranking and isinstance(season_ranking, list):
        for season_obj in season_ranking:
            if isinstance(season_obj, dict):
                season_name = season_obj.get('name', season_obj.get('season', '')).title()
                season_score = season_obj.get('score', season_obj.get('value', None))
                
                if season_score is not None:
                    score = max(0, min(5, float(season_score)))
                    
                    if 'winter' in season_name.lower():
                        seasonality['Winter'] = round(score, 1)
                    elif 'fall' in season_name.lower() or 'autumn' in season_name.lower():
                        seasonality['Fall'] = round(score, 1)
                    elif 'spring' in season_name.lower():
                        seasonality['Spring'] = round(score, 1)
                    elif 'summer' in season_name.lower():
                        seasonality['Summer'] = round(score, 1)
    
    if not seasonality:
        seasonality = {"Winter": 3, "Fall": 3, "Spring": 3, "Summer": 3}
    
    occasion_ranking = api_perfume.get('Occasion Ranking', api_perfume.get('OccasionRanking', api_perfume.get('occasion_ranking', [])))
    
    day_scores = []
    night_scores = []
    
    if occasion_ranking and isinstance(occasion_ranking, list):
        for occ_obj in occasion_ranking:
            if isinstance(occ_obj, dict):
                occ_name = occ_obj.get('name', occ_obj.get('occasion', '')).lower()
                occ_score = occ_obj.get('score', occ_obj.get('value', None))
                
                if occ_score is not None:
                    occ_score = float(occ_score)
                
                    if any(word in occ_name for word in ['professional', 'casual', 'daily', 'day', 'office', 'sport', 'work', 'business']):
                        day_scores.append(occ_score)
                    elif any(word in occ_name for word in ['night', 'evening', 'date', 'romantic', 'party', 'formal', 'special']):
                        night_scores.append(occ_score)
    
    occasion = {}
    if day_scores:
        occasion['Day'] = round(max(0, min(5, sum(day_scores) / len(day_scores))), 1)
    if night_scores:
        occasion['Night'] = round(max(0, min(5, sum(night_scores) / len(night_scores))), 1)
    
    if not occasion:
        occasion = {"Day": 3, "Night": 3}
    
    oil_type = api_perfume.get('OilType', 'Eau de Parfum')
    
    perfume_type = "Eau de Parfum"
    if oil_type:
        oil_type_lower = oil_type.lower()
        if 'eau de parfum' in oil_type_lower or 'edp' in oil_type_lower:
            perfume_type = "Eau de Parfum"
        elif 'eau de toilette' in oil_type_lower or 'edt' in oil_type_lower:
            perfume_type = "Eau de Toilette"
        elif 'parfum' in oil_type_lower or 'extrait' in oil_type_lower:
            perfume_type = "Parfum"
        elif 'eau de cologne' in oil_type_lower or 'edc' in oil_type_lower:
            perfume_type = "Eau de Cologne"
        else:
            perfume_type = oil_type
    
    size = "50ml"
    if oil_type and 'ml' in oil_type.lower():
        import re
        match = re.search(r'(\d+)\s*ml', oil_type.lower())
        if match:
            size = f"{match.group(1)}ml"
    
    price = api_perfume.get('price', api_perfume.get('Price', 75))
    try:
        price = int(price)
    except:
        price = 75
    
    gender = api_perfume.get('Gender', 'Unisex')
    if 'women' in gender.lower():
        gender = 'Female'
    elif 'men' in gender.lower():
        gender = 'Male'
    else:
        gender = 'Unisex'
    
    main_accords = api_perfume.get('Main Accords', [])
    scent_type = "Fresh"
    if main_accords:
        first_accord = main_accords[0].lower() if isinstance(main_accords, list) else ""
        if 'floral' in first_accord:
            scent_type = "Floral"
        elif 'woody' in first_accord or 'wood' in first_accord:
            scent_type = "Woody"
        elif 'citrus' in first_accord:
            scent_type = "Citrus"
        elif 'oriental' in first_accord or 'spicy' in first_accord:
            scent_type = "Oriental"
        elif 'sweet' in first_accord or 'gourmand' in first_accord:
            scent_type = "Gourmand"
        elif 'green' in first_accord or 'herbal' in first_accord:
            scent_type = "Green"
        elif 'leather' in first_accord:
            scent_type = "Leather"
    
    rating = api_perfume.get('rating', '0')
    try:
        rating = float(rating)
    except:
        rating = 0.0
    
    transformed = {
        "id": f"api_{api_perfume.get('Name', '').replace(' ', '_').lower()}",
        "name": api_perfume.get('Name', 'Unknown'),
        "brand": api_perfume.get('Brand', 'Unknown'),
        "price": price,
        "size": size,
        "perfume_type": perfume_type,
        "gender": gender,
        "scent_type": scent_type,
        "description": f"A {api_perfume.get('Longevity', 'moderate')} fragrance with {api_perfume.get('Sillage', 'moderate')} projection.",
        "image_url": api_perfume.get('Image URL', 'https://via.placeholder.com/300x400/c8b8d8/FFFFFF?text=Perfume'),
        "top_notes": top_notes if top_notes else [{"name": "Bergamot", "imageUrl": ""}, {"name": "Lemon", "imageUrl": ""}],
        "heart_notes": heart_notes if heart_notes else [{"name": "Jasmine", "imageUrl": ""}, {"name": "Rose", "imageUrl": ""}],
        "base_notes": base_notes if base_notes else [{"name": "Musk", "imageUrl": ""}, {"name": "Vanilla", "imageUrl": ""}],
        "main_accords": main_accords if main_accords else ["Fresh", "Floral"],
        "seasonality": seasonality,
        "occasion": occasion,
        "longevity": api_perfume.get('Longevity', 'Moderate'),
        "sillage": api_perfume.get('Sillage', 'Moderate'),
        "rating": rating
    }
    
    return transformed


@st.cache_data(ttl=7200, show_spinner="Loading perfume database...")
def get_initial_perfumes(api_key: str) -> List[Dict]:
    """Load initial perfume database by searching popular brands and scents"""
    perfumes = []
    
    search_terms = [
        "Dior", "Chanel", "Gucci", "Versace", "Tom Ford",
        "Prada", "Armani", "Yves Saint Laurent", "Givenchy", "Burberry",
        "Dolce Gabbana", "Calvin Klein", "Hugo Boss", "Valentino", "Hermes",
        "Rose", "Oud", "Vanilla", "Lavender", "Jasmine",
        "Citrus", "Sandalwood", "Amber", "Musk", "Bergamot"
    ]
    
    for term in search_terms:
        results = search_fragella_perfumes(api_key, term, limit=20)
        if results:
            for api_perfume in results:
                transformed = transform_api_perfume(api_perfume)
                if not any(p['id'] == transformed['id'] for p in perfumes):
                    perfumes.append(transformed)
        
        if len(perfumes) >= 300:
            break
    
    return perfumes

