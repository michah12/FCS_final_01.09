import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from typing import Dict, List


def scroll_to_top():
    """Force scroll to top when detail view opens"""
    components.html(
        """
        <script>
        window.parent.document.documentElement.scrollTop = 0;
        window.parent.document.body.scrollTop = 0;
        </script>
        """,
        height=0,
    )


def render_detail_back_button(render_back_button_func):
    """Render context-aware back button based on where user came from"""
    if st.session_state.detail_view_source == 'home':
        if st.button("← Back to Home", key="back_to_home", use_container_width=True):
            st.session_state.show_perfume_details = False
            st.session_state.current_perfume = None
            st.session_state.detail_view_source = 'search'
            st.rerun()
    elif st.session_state.detail_view_source == 'inventory':
        if st.button("← Back to Inventory", key="back_to_inventory", use_container_width=True):
            st.session_state.show_perfume_details = False
            st.session_state.current_perfume = None
            st.session_state.detail_view_source = 'search'
            st.rerun()
    elif st.session_state.show_questionnaire_results:
        if st.button("← Back to Recommendations", key="back_to_questionnaire", use_container_width=True):
            st.session_state.show_perfume_details = False
            st.session_state.current_perfume = None
            st.session_state.detail_view_source = 'search'
            st.rerun()
    else:
        render_back_button_func("search", "Back to Results")


def render_perfume_image(perfume: Dict):
    """Render centered perfume image"""
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


def render_add_button(perfume: Dict, add_func, record_func):
    """Render add to inventory button"""
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("Add to My Perfumes", key="add_to_inventory", use_container_width=True, type="primary"):
            add_func(perfume)
            record_func(perfume['id'], 'add_to_inventory')
            st.success(f"Added {perfume['name']} to your collection")


def render_perfume_title(perfume: Dict):
    """Render perfume name and brand"""
    perfume_name = perfume["name"]
    perfume_brand = perfume["brand"]
    
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


def render_section_header(title: str):
    """Render standardized section header"""
    st.markdown(f"""
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
                {title}
            </h2>
        </div>
    """, unsafe_allow_html=True)


def render_description(perfume: Dict):
    """Render perfume description"""
    perfume_desc = perfume['description']
    
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


def render_performance_metrics(perfume: Dict):
    """Render longevity and sillage boxes"""
    longevity = perfume.get('longevity', 'Moderate')
    sillage = perfume.get('sillage', 'Moderate')
    
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


def get_accord_colors() -> Dict[str, str]:
    """Get color mapping for perfume accords"""
    return {
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


def render_main_accords_chart(perfume: Dict):
    """Render horizontal bar chart of main accords"""
    accord_colors = get_accord_colors()
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
    
    # Display as horizontal bars using plotly
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
        
        # Calculate dynamic height based on number of accords
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
                automargin=True
            ),
            margin=dict(l=0, r=0, t=0, b=0, pad=0),
            dragmode=False
        )
        
        st.plotly_chart(fig_accords, use_container_width=True, config={
            'displayModeBar': False, 
            'staticPlot': True
        })


def render_note_card(note):
    """Render a single note card"""
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


def render_notes_pyramid(perfume: Dict):
    """Render top/heart/base notes pyramid"""
    # Note card CSS
    st.markdown("""
        <style>
        .note-category-title {
            text-align: center;
            color: #6b5b95;
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .note-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f7fa 100%);
            border-radius: 16px;
            padding: 18px;
            margin: 12px 0;
            border: 2px solid #e8e4f0;
            display: flex;
            align-items: center;
            gap: 18px;
            box-shadow: 0 3px 12px rgba(107, 91, 149, 0.08);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .note-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(107, 91, 149, 0.15);
        }
        .note-icon {
            width: 50px;
            height: 50px;
            border-radius: 12px;
            object-fit: cover;
            background: #e8e4f0;
            flex-shrink: 0;
        }
        .note-name {
            color: #6b5b95;
            font-size: 16px;
            font-weight: 600;
            text-transform: capitalize;
            flex: 1;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
    
    render_section_header("Fragrance Notes")
    
    col_top, col_heart, col_base = st.columns(3, gap="medium")
    
    with col_top:
        st.markdown('<div class="note-category-title">Top Notes</div>', unsafe_allow_html=True)
        for note in perfume['top_notes']:
            render_note_card(note)
    
    with col_heart:
        st.markdown('<div class="note-category-title">Heart Notes</div>', unsafe_allow_html=True)
        for note in perfume['heart_notes']:
            render_note_card(note)
    
    with col_base:
        st.markdown('<div class="note-category-title">Base Notes</div>', unsafe_allow_html=True)
        for note in perfume['base_notes']:
            render_note_card(note)


def render_seasonality(perfume: Dict):
    """Render seasonality boxes"""
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
    render_section_header("Seasonality")
    
    seasonality = perfume.get('seasonality', {'Spring': 3, 'Summer': 3, 'Fall': 3, 'Winter': 3})
    
    col_spring, col_summer, col_fall, col_winter = st.columns(4, gap="medium")
    
    seasons = [
        ('Spring', col_spring, '#A8D5BA'),
        ('Summer', col_summer, '#FFD93D'),
        ('Fall', col_fall, '#D97548'),
        ('Winter', col_winter, '#6b5b95')
    ]
    
    for season_name, col, color in seasons:
        score = seasonality.get(season_name, 3)
        with col:
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%); 
                            padding: 30px 20px; 
                            border-radius: 20px; 
                            text-align: center; 
                            box-shadow: 0 8px 25px rgba(107, 91, 149, 0.2);
                            min-height: 180px;
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;">
                    <div style="height: 48px; margin-bottom: 15px;"></div>
                    <div style="color: white; font-size: 18px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px;">{season_name}</div>
                    <div style="color: white; font-size: 28px; font-weight: 900;">{score}/5</div>
                </div>
            """, unsafe_allow_html=True)


def render_gender_boxes(perfume: Dict):
    """Render gender suitability boxes"""
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
    render_section_header("For Whom")
    
    gender = perfume.get('gender', 'Unisex')
    
    # Calculate percentages
    if gender == 'Male':
        male_p, female_p, unisex_p = 70, 15, 15
    elif gender == 'Female':
        male_p, female_p, unisex_p = 15, 70, 15
    elif gender == 'Unisex':
        male_p, female_p, unisex_p = 33, 33, 34
    else:
        male_p, female_p, unisex_p = 33, 33, 34
    
    col_male, col_female, col_unisex = st.columns(3, gap="medium")
    
    genders = [
        ('Male', col_male, male_p, '#6b5b95'),
        ('Female', col_female, female_p, '#E8A5D4'),
        ('Unisex', col_unisex, unisex_p, '#A8D5BA')
    ]
    
    for gender_name, col, percentage, color in genders:
        with col:
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%); 
                            padding: 40px 20px; 
                            border-radius: 20px; 
                            text-align: center; 
                            box-shadow: 0 8px 25px rgba(107, 91, 149, 0.2);
                            min-height: 180px;
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;">
                    <div style="color: white; font-size: 20px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px;">{gender_name}</div>
                    <div style="color: white; font-size: 42px; font-weight: 900; text-shadow: 0 2px 10px rgba(0,0,0,0.2);">{percentage}%</div>
                </div>
            """, unsafe_allow_html=True)


def render_occasion_bar(perfume: Dict):
    """Render day/night occasion bar"""
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
    render_section_header("Best Time to Wear")
    
    occasion = perfume.get('occasion', {'Day': 3, 'Night': 3})
    day_score = occasion.get('Day', 3)
    night_score = occasion.get('Night', 3)
    
    total = day_score + night_score
    if total > 0:
        day_percent = (day_score / total) * 100
        night_percent = (night_score / total) * 100
    else:
        day_percent = 50
        night_percent = 50
    
    day_display = f"{day_percent:.1f}%"
    night_display = f"{night_percent:.1f}%"
    
    day_label = day_display if day_percent > 5 else ""
    night_label = night_display if night_percent > 5 else ""
    
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

