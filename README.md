# Scentify

Perfume recommendation system with ML-based personalization.

## Overview

Web application for perfume discovery and recommendations. Features search, filtering, questionnaire-based matching, and machine learning recommendations based on user preferences.

## Requirements

- Python 3.7+
- Fragella API key
- Internet connection

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create `.env` file in project root:

```env
FRAGELLA_API_KEY=your_api_key_here
```

## Usage

```bash
streamlit run scentify.py
```

Application runs at `http://localhost:8501`

## Features

### Search
- Full-text search by brand or perfume name
- Filters: scent type, gender
- Live API integration with Fragella database
- Detailed perfume view with notes, accords, seasonality

### Questionnaire
- Bipolar scale questionnaire (10 questions)
- Matching algorithm based on user preferences
- Returns ranked perfume recommendations

### Inventory Management
- Personal perfume collection storage
- Add/remove functionality
- Persistent storage in JSON format

### ML Recommendations
- Requires minimum 2 perfumes in inventory
- Features: main accords (one-hot encoded), seasonality scores, longevity/sillage ratings, gender encoding
- Algorithm: Linear Regression with StandardScaler
- Model retrains on inventory changes
- Predictions stored in session state

## Tech Stack

- **Frontend**: Streamlit
- **Visualization**: Plotly
- **ML**: scikit-learn (LinearRegression, StandardScaler)
- **API**: Fragella REST API
- **Storage**: JSON files

## Data Persistence

Application creates `data/` directory containing:
- `user_perfume_inventory.json` - User's perfume collection
- `user_interactions.json` - Click and interaction logs
- `perfume_rankings.json` - Popularity rankings
- `ml_model.pkl` - Trained regression model
- `ml_scaler.pkl` - Feature scaler

## Project Structure

```
FCF_final/
├── scentify.py              # Main application
├── api/
│   └── fragella.py          # API integration
├── data_handlers/
│   └── persistence.py       # Data storage functions
├── ml/
│   └── recommender.py       # ML recommendation engine
├── ui/
│   ├── detail_components.py # UI components
│   └── styles.py            # CSS styling
└── data/                    # Generated at runtime
```

## API Integration

Uses Fragella API endpoints:
- `GET /perfumes` - Initial perfume data
- `GET /perfumes?search={query}` - Search functionality

## Troubleshooting

**Application won't start:**
- Verify API key in `.env` file
- Check internet connection
- Ensure all dependencies installed: `pip install -r requirements.txt`

**No recommendations appearing:**
- Add at least 2 perfumes to inventory
- Verify perfume data loaded successfully

**API errors:**
- Validate API key
- Check Fragella API status
- Review network connectivity

## Authors

Jil, Diego, Luis, Livio, Micha

