import numpy as np
import pickle
import os
import random
from typing import List, Dict, Optional, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
from collections import Counter


def extract_perfume_features(perfume: Dict) -> np.ndarray:
    """Extract numerical features from perfume data"""
    features = []
    
    # Define all possible main accords
    all_accords = [
        'floral', 'fresh', 'woody', 'citrus', 'oriental', 'spicy', 
        'sweet', 'gourmand', 'fruity', 'aromatic', 'green', 'aquatic',
        'leather', 'powdery', 'herbal', 'amber', 'musk', 'vanilla',
        'rose', 'jasmine', 'lavender', 'bergamot', 'sandalwood', 'patchouli',
        'oud', 'vetiver', 'tobacco', 'animalic', 'earthy', 'smoky'
    ]
    
    # Extract main accords as binary features
    perfume_accords = perfume.get('main_accords', [])
    perfume_accords_lower = [accord.lower() if isinstance(accord, str) else '' for accord in perfume_accords]
    
    for accord in all_accords:
        has_accord = any(accord in pa for pa in perfume_accords_lower)
        features.append(1.0 if has_accord else 0.0)
    
    # Seasonality features
    seasonality = perfume.get('seasonality', {})
    features.append(float(seasonality.get('Winter', 3)) / 5.0)
    features.append(float(seasonality.get('Fall', 3)) / 5.0)
    features.append(float(seasonality.get('Spring', 3)) / 5.0)
    features.append(float(seasonality.get('Summer', 3)) / 5.0)
    
    # Occasion features
    occasion = perfume.get('occasion', {})
    features.append(float(occasion.get('Day', 3)) / 5.0)
    features.append(float(occasion.get('Night', 3)) / 5.0)
    
    # Longevity
    longevity_map = {
        'very weak': 0.1, 'weak': 0.3, 'moderate': 0.5, 'long lasting': 0.7,
        'long-lasting': 0.7, 'eternal': 0.9, 'very long lasting': 0.9
    }
    longevity_str = str(perfume.get('longevity', 'moderate')).lower()
    longevity_score = longevity_map.get(longevity_str, 0.5)
    features.append(longevity_score)
    
    # Sillage
    sillage_map = {
        'intimate': 0.2, 'weak': 0.3, 'moderate': 0.5, 'strong': 0.7, 'enormous': 0.9
    }
    sillage_str = str(perfume.get('sillage', 'moderate')).lower()
    sillage_score = sillage_map.get(sillage_str, 0.5)
    features.append(sillage_score)
    
    # Gender
    gender_map = {'Male': 0.0, 'Unisex': 0.5, 'Female': 1.0}
    gender = perfume.get('gender', 'Unisex')
    features.append(gender_map.get(gender, 0.5))
    
    return np.array(features)


def build_training_dataset(user_inventory: List[Dict], all_perfumes: List[Dict], ml_config: Dict) -> Tuple[np.ndarray, np.ndarray]:
    """
    Builds training data: positive samples (perfumes they own) and negative samples  
    (random perfumes they don't own). Returns feature matrix X and labels y.
    """
    X_positive = []
    X_negative = []
    
    # Get IDs of owned perfumes
    owned_ids = {p['id'] for p in user_inventory}
    
    # Extract features from positive samples
    for perfume in user_inventory:
        features = extract_perfume_features(perfume)
        X_positive.append(features)
    
    # Get all non-owned perfumes
    non_owned = [p for p in all_perfumes if p['id'] not in owned_ids]
    
    # Sample negative examples
    num_negatives = len(user_inventory) * ml_config['negative_samples_ratio']
    if len(non_owned) > num_negatives:
        negative_samples = random.sample(non_owned, int(num_negatives))
    else:
        negative_samples = non_owned
    
    # Extract features from negative samples
    for perfume in negative_samples:
        features = extract_perfume_features(perfume)
        X_negative.append(features)
    
    # Combine positive and negative samples
    X = np.array(X_positive + X_negative)
    y = np.array([1] * len(X_positive) + [0] * len(X_negative))
    
    return X, y


def train_ml_model(user_inventory: List[Dict], all_perfumes: List[Dict], ml_config: Dict, model_file: str, scaler_file: str) -> Optional[Tuple]:
    """
    Trains a machine learning model based on what perfumes the user owns.
    
    We take perfumes they own (positive examples) and randomly
    sample perfumes they don't own (negative examples), then train a model to
    tell the difference. That model can then score new perfumes.
    
    We use Logistic Regression by default because its simple and works well.
    """
    # Check if user has enough perfumes to train
    if len(user_inventory) < ml_config['min_inventory_size']:
        return None
    
    try:
        # Build training dataset
        X, y = build_training_dataset(user_inventory, all_perfumes, ml_config)
        
        if len(X) == 0:
            return None
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train model based on configuration
        if ml_config['model_type'] == 'decision_tree':
            model = DecisionTreeClassifier(
                max_depth=5,
                min_samples_split=2,
                min_samples_leaf=1,
                random_state=ml_config['random_state']
            )
        else:  # Default to logistic regression
            model = LogisticRegression(
                max_iter=1000,
                random_state=ml_config['random_state'],
                solver='lbfgs'
            )
        
        # Fit the model
        model.fit(X_scaled, y)
        
        # Get feature importance
        if hasattr(model, 'feature_importances_'):
            feature_importance = model.feature_importances_
        elif hasattr(model, 'coef_'):
            feature_importance = np.abs(model.coef_[0])
        else:
            feature_importance = None
        
        # Save model and scaler
        os.makedirs('data', exist_ok=True)
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        with open(scaler_file, 'wb') as f:
            pickle.dump(scaler, f)
        
        return model, scaler, feature_importance
    
    except Exception as e:
        print(f"Error training ML model: {e}")
        return None


def load_ml_model(model_file: str, scaler_file: str) -> Optional[Tuple]:
    """Load previously trained ML model and scaler from disk."""
    try:
        if os.path.exists(model_file) and os.path.exists(scaler_file):
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
            with open(scaler_file, 'rb') as f:
                scaler = pickle.load(f)
            return model, scaler
        return None
    except Exception as e:
        print(f"Error loading ML model: {e}")
        return None


def get_ml_recommendations(user_inventory: List[Dict], 
                          all_perfumes: List[Dict], 
                          ml_config: Dict,
                          model_file: str,
                          scaler_file: str,
                          top_n: int = 10,
                          ensure_diversity: bool = True) -> List[Dict]:
    """
    This is the main recommendation engine
    
    How it works:
    1. Trains a model on the user's perfume collection (or loads an existing one)
    2. Runs every non-owned perfume through the model to get a match score
    3. Sorts by score and returns the top N
    4. Makes sure we don't recommend 10 nearly-identical perfumes (diversity filter)
    
    The 'ml_score' is basically "probability the user will like this" (0-1 scale).
    We only show perfumes with >50% match probability.
    """
    # Check if user has enough perfumes
    if len(user_inventory) < ml_config['min_inventory_size']:
        return []
    
    # Train or load model
    model_data = train_ml_model(user_inventory, all_perfumes, ml_config, model_file, scaler_file)
    if not model_data:
        # Try loading existing model
        model_data = load_ml_model(model_file, scaler_file)
        if not model_data:
            return []
    
    model, scaler = model_data[0], model_data[1]
    
    # Get IDs of owned perfumes
    owned_ids = {p['id'] for p in user_inventory}
    
    # Get candidate perfumes (non-owned)
    candidates = [p for p in all_perfumes if p['id'] not in owned_ids]
    
    if not candidates:
        return []
    
    # Score each candidate
    scored_perfumes = []
    for perfume in candidates:
        try:
            # Extract features
            features = extract_perfume_features(perfume)
            features_scaled = scaler.transform(features.reshape(1, -1))
            
            # Get prediction probability
            if hasattr(model, 'predict_proba'):
                prob = model.predict_proba(features_scaled)[0][1]
            else:
                prob = float(model.predict(features_scaled)[0])
            
            # Only include if above threshold
            if prob >= ml_config['min_recommendation_probability']:
                perfume_copy = perfume.copy()
                perfume_copy['ml_score'] = prob
                perfume_copy['ml_explanation'] = generate_ml_explanation(perfume, user_inventory, prob)
                scored_perfumes.append(perfume_copy)
        
        except Exception as e:
            print(f"Error scoring perfume {perfume.get('name', 'Unknown')}: {e}")
            continue
    
    # Sort by probability score
    scored_perfumes.sort(key=lambda p: p['ml_score'], reverse=True)
    
    # Apply diversity if requested
    if ensure_diversity and len(scored_perfumes) > top_n:
        scored_perfumes = apply_diversity_filter(scored_perfumes, top_n)
    
    return scored_perfumes[:top_n]


def apply_diversity_filter(perfumes: List[Dict], top_n: int) -> List[Dict]:
    """Make sure diversity in scent types between recommendations."""
    if not perfumes:
        return []
    
    selected = []
    scent_type_counts = {}
    
    # Try to balance scent types
    for perfume in perfumes:
        if len(selected) >= top_n:
            break
        
        scent_type = perfume.get('scent_type', 'Fresh')
        current_count = scent_type_counts.get(scent_type, 0)
        
        # Allow if this scent type is underrepresented or we're still filling
        max_per_type = max(2, top_n // 5)
        if current_count < max_per_type or len(selected) < top_n // 2:
            selected.append(perfume)
            scent_type_counts[scent_type] = current_count + 1
    
    # Fill remaining slots with highest scores if needed
    if len(selected) < top_n:
        remaining = [p for p in perfumes if p not in selected]
        selected.extend(remaining[:top_n - len(selected)])
    
    return selected


def generate_ml_explanation(perfume: Dict, user_inventory: List[Dict], score: float) -> str:
    """Create readable explanation for why a perfume was recommended."""
    # Analyze user's preferences from inventory
    all_user_accords = []
    for inv_perfume in user_inventory:
        all_user_accords.extend(inv_perfume.get('main_accords', []))
    
    # Get most common accords in user's collection
    accord_counter = Counter([a.lower() for a in all_user_accords if isinstance(a, str)])
    top_user_accords = [accord for accord, _ in accord_counter.most_common(3)]
    
    # Find matching accords in recommended perfume
    perfume_accords = [a.lower() for a in perfume.get('main_accords', []) if isinstance(a, str)]
    matching_accords = [a for a in perfume_accords if a in top_user_accords]
    
    # Build explanation
    if matching_accords:
        accord_text = ", ".join(matching_accords[:2])
        explanation = f"Matches your preference for {accord_text} scents"
    else:
        explanation = f"Complements your collection with {perfume_accords[0] if perfume_accords else 'unique'} notes"
    
    # Add confidence level
    if score >= 0.8:
        confidence = "Highly recommended"
    elif score >= 0.7:
        confidence = "Strong match"
    else:
        confidence = "Good match"
    
    return f"{confidence} - {explanation} ({int(score * 100)}% match)"


def get_model_insights(user_inventory: List[Dict], ml_config: Dict) -> Dict:
    """Get insights about the trained ML model and user preferences."""
    insights = {
        'inventory_size': len(user_inventory),
        'can_train_model': len(user_inventory) >= ml_config['min_inventory_size'],
        'model_type': ml_config['model_type'],
        'top_preferences': [],
        'diversity_score': 0.0
    }
    
    if not user_inventory:
        return insights
    
    # Analyze user preferences
    all_accords = []
    scent_types = []
    for perfume in user_inventory:
        all_accords.extend(perfume.get('main_accords', []))
        scent_types.append(perfume.get('scent_type', 'Fresh'))
    
    # Top preferences
    accord_counter = Counter([a.lower() for a in all_accords if isinstance(a, str)])
    insights['top_preferences'] = [
        {'name': accord.title(), 'count': count} 
        for accord, count in accord_counter.most_common(5)
    ]
    
    # Diversity score (unique scent types / total)
    if scent_types:
        insights['diversity_score'] = len(set(scent_types)) / len(scent_types)
    
    return insights

