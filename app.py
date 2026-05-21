import streamlit as st
import pandas as pd
import database as db

st.set_page_config(page_title="2K Career Tracker", layout="wide", initial_sidebar_state="collapsed")
db.init_db()

st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="InputInstructions"] {display: none !important;}

    .stApp {background-color: #1a1a1a; color: #e0e0e0;}
    h1, h2, h3 {color: #ffffff; font-style: italic;}
    .orange-text {color: #ff7b00 !important; font-weight: bold;}

    div.stButton > button {
        background-color: #222222; color: #e0e0e0; border: 1px solid #333333; 
        border-radius: 4px; font-size: 14px; padding: 10px; width: 100%;
    }
    div.stButton > button:hover {
        border-color: #ff7b00; color: #ff7b00; background-color: #1a1a1a;
    }
    div.stButton > button:focus:not(:active) {
        border-color: #ff7b00; color: #ff7b00;
    }
    .metric-value {font-size: 32px; font-weight: bold; color: white;}
    .metric-label {font-size: 12px; color: #888; text-transform: uppercase;}
    
    /* Force-hide Streamlit's custom plus/minus step buttons */
    [data-testid="stNumberInputStepUp"],
    [data-testid="stNumberInputStepDown"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# State Management
if 'page' not in st.session_state:
    st.session_state.page = "landing"
if 'current_player_id' not in st.session_state:
    st.session_state.current_player_id = None


def navigate(page_name):
    st.session_state.page = page_name


# Define the dynamic header for the main pages
def get_header():
    profile = db.fetch_df("SELECT * FROM player_profile WHERE id = ?", (st.session_state.current_player_id,)).iloc[0]
    xp_display = f"<span style='float: right; font-size: 20px;'>XP <span class='orange-text'>{profile['total_xp']}</span></span>"
    return f"**{profile['name']}** | {profile['position']} | #{profile['jersey_number']} {xp_display}", profile


# ==========================================
# PAGE 0: LANDING / PLAYER SELECTION
# ==========================================
if st.session_state.page == "landing":
    st.markdown("<h1 style='text-align: center; color: #ff7b00; font-size: 60px;'>2K CAREER TRACKER</h1>",
                unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📁 LOAD EXISTING CAREER")
        players_df = db.fetch_df("SELECT * FROM player_profile")

        if not players_df.empty:
            player_options = {f"{row['name']} | {row['position']} | {row['overall_rating']} OVR": row['id'] for _, row
                              in players_df.iterrows()}
            selected_label = st.selectbox("Select Player Save", list(player_options.keys()))
            if st.button("LOAD PLAYER", key="load_btn"):
                st.session_state.current_player_id = player_options[selected_label]
                navigate("overview")
                st.rerun()
        else:
            st.info("No saved careers found. Create one to get started!")

    with col2:
        st.subheader("🌟 CREATE NEW PLAYER")
        with st.form("create_player_form", clear_on_submit=True):
            name = st.text_input("Player Name")
            pos = st.selectbox("Position", ["PG", "SG", "SF", "PF", "C"])

            c1, c2, c3 = st.columns(3)
            with c1:
                jersey = st.number_input("Jersey Number", min_value=0, max_value=99, value=0)
            with c2:
                weight = st.number_input("Weight (lbs)", min_value=150, max_value=400, value=220)
            with c3:
                # Updated to float for feet with 1 decimal place (e.g., 6.8 ft)
                wingspan = st.number_input("Wingspan (ft)", min_value=5.0, max_value=9.0, value=6.8, format="%.1f")

            if st.form_submit_button("CREATE CAREER"):
                if name:
                    new_id = db.create_player(name, pos, jersey, weight, wingspan)
                    st.session_state.current_player_id = new_id
                    st.success(f"Career created for {name}!")
                    navigate("overview")
                    st.rerun()
                else:
                    st.error("Player name is required.")

# ==========================================
# PAGE 1: OVERVIEW & SUBMISSION
# ==========================================
elif st.session_state.page == "overview":
    header_html, profile = get_header()

    # Back to Menu button
    if st.button("⬅ CHANGE PLAYER / MAIN MENU", key="back_to_main"):
        st.session_state.current_player_id = None
        navigate("landing")
        st.rerun()

    st.markdown(header_html, unsafe_allow_html=True)
    st.markdown("---")

    col_left, col_right = st.columns([1.2, 2.5])

    with col_left:
        with st.form("game_submission", clear_on_submit=True):
            st.markdown("### ENTER GAME STATS")
            c1, c2 = st.columns(2)
            stats = {}
            with c1:
                stats['fgm'] = st.number_input("FGM", 0)
                stats['tpm'] = st.number_input("3PM", 0)
                stats['ftm'] = st.number_input("FTM", 0)
                stats['ast'] = st.number_input("AST", 0)
                stats['dreb'] = st.number_input("DREB", 0)
                stats['stl'] = st.number_input("STL", 0)
                stats['dunks'] = st.number_input("DUNKS", 0)
                stats['win'] = st.checkbox("WIN")
            with c2:
                stats['fga'] = st.number_input("FGA", 0)
                stats['tpa'] = st.number_input("3PA", 0)
                stats['fta'] = st.number_input("FTA", 0)
                stats['to_val'] = st.number_input("TO", 0)
                stats['oreb'] = st.number_input("OREB", 0)
                stats['fls'] = st.number_input("FLS", 0)
                stats['blk'] = st.number_input("BLK", 0)

            if st.form_submit_button("SUBMIT GAME"):
                actual_fgm = max(stats['fgm'], stats['tpm'])
                two_pointers_made = actual_fgm - stats['tpm']
                pts = (two_pointers_made * 2) + (stats['tpm'] * 3) + stats['ftm']
                xp = (pts * 10) + (stats['ast'] * 15) + ((stats['dreb'] + stats['oreb']) * 15) + (stats['blk'] * 20) + (
                            stats['stl'] * 20)
                if stats['win']: xp = int(xp * 1.5)

                db.insert_game(st.session_state.current_player_id, stats, xp)
                st.rerun()

    with col_right:
        st.markdown("<h1>SEASON OVERVIEW</h1>", unsafe_allow_html=True)
        games_df = db.fetch_df("SELECT * FROM games WHERE player_id = ?", (st.session_state.current_player_id,))

        if not games_df.empty:
            games_df['fgm_adj'] = games_df[['fgm', 'tpm']].max(axis=1)
            games_df['pts'] = ((games_df['fgm_adj'] - games_df['tpm']) * 2) + (games_df['tpm'] * 3) + games_df['ftm']
            games_df['reb'] = games_df['dreb'] + games_df['oreb']

            wins = int(games_df['win'].sum())
            losses = len(games_df) - wins
            total_fgm = games_df['fgm_adj'].sum()
            total_fga = games_df['fga'].sum()
            fg_pct = (total_fgm / total_fga * 100) if total_fga > 0 else 0.0
            total_tpm = games_df['tpm'].sum()
            total_tpa = games_df['tpa'].sum()
            tp_pct = (total_tpm / total_tpa * 100) if total_tpa > 0 else 0.0

            m1, m2, m3, m4, m5, m6, m7, m8 = st.columns(8)
            m1.markdown(f"<div class='metric-label'>W-L</div><div class='metric-value'>{wins}-{losses}</div>",
                        unsafe_allow_html=True)
            m2.markdown(
                f"<div class='metric-label'>PPG</div><div class='metric-value'>{games_df['pts'].mean():.1f}</div>",
                unsafe_allow_html=True)
            m3.markdown(
                f"<div class='metric-label'>APG</div><div class='metric-value'>{games_df['ast'].mean():.1f}</div>",
                unsafe_allow_html=True)
            m4.markdown(
                f"<div class='metric-label'>RPG</div><div class='metric-value'>{games_df['reb'].mean():.1f}</div>",
                unsafe_allow_html=True)
            m5.markdown(
                f"<div class='metric-label'>SPG</div><div class='metric-value'>{games_df['stl'].mean():.1f}</div>",
                unsafe_allow_html=True)
            m6.markdown(
                f"<div class='metric-label'>BPG</div><div class='metric-value'>{games_df['blk'].mean():.1f}</div>",
                unsafe_allow_html=True)
            m7.markdown(f"<div class='metric-label'>FG%</div><div class='metric-value'>{fg_pct:.1f}%</div>",
                        unsafe_allow_html=True)
            m8.markdown(f"<div class='metric-label'>3P%</div><div class='metric-value'>{tp_pct:.1f}%</div>",
                        unsafe_allow_html=True)

            st.markdown("---")
            display_df = games_df[['win', 'pts', 'reb', 'ast', 'stl', 'blk']].tail(5).iloc[::-1]
            display_df['win'] = display_df['win'].apply(lambda x: 'W' if x else 'L')
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No games played yet. Submit a game to see stats!")

    st.markdown("---")
    nav1, nav2, nav3 = st.columns(3)
    with nav1:
        st.button("ATTRIBUTES ➔", on_click=navigate, args=("attributes",))
    with nav2:
        st.button("BADGES ➔", on_click=navigate, args=("badges",))

# ==========================================
# PAGE 2: ATTRIBUTES
# ==========================================
elif st.session_state.page == "attributes":
    header_html, profile = get_header()
    st.button("⬅ BACK TO SEASON", on_click=navigate, args=("overview",))
    st.markdown(f"<h1 style='color: #ff7b00; display: inline;'>ATTRIBUTES</h1> <br> {header_html}",
                unsafe_allow_html=True)
    st.caption("Hover over an attribute to see the upgrade cost. Click to instantly upgrade by 1 level.")

    attr_df = db.fetch_df("SELECT * FROM player_attributes WHERE player_id = ?", (st.session_state.current_player_id,))
    categories = attr_df['category'].unique()


    def calculate_next_level_cost(current_level, multiplier):
        base_cost = 50
        if current_level >= 60:
            base_cost += (current_level - 60) * 15
        return int(base_cost * multiplier)


    cols = st.columns(len(categories))

    for i, cat in enumerate(categories):
        with cols[i]:
            st.markdown(
                f"<h4 style='color:#a0a0a0; border-bottom: 1px solid #333; padding-bottom: 5px; font-size: 16px;'>{cat}</h4>",
                unsafe_allow_html=True)
            cat_df = attr_df[attr_df['category'] == cat]

            for _, row in cat_df.iterrows():
                attr_name = row['attribute_name']
                curr_lvl = int(row['current_level'])
                max_lvl = int(row['max_level'])
                multiplier = row['cost_multiplier']

                if curr_lvl >= max_lvl:
                    st.button(f"⭐ {attr_name} (MAX)", key=f"max_{attr_name}", disabled=True, use_container_width=True)
                else:
                    cost = calculate_next_level_cost(curr_lvl, multiplier)
                    btn_label = f"➕ {attr_name}: {curr_lvl}  •  {cost} XP"
                    if st.button(btn_label, key=f"up_{attr_name}", use_container_width=True):
                        if profile['total_xp'] >= cost:
                            db.commit_attribute_upgrade(st.session_state.current_player_id, attr_name, curr_lvl + 1,
                                                        cost)
                            st.rerun()
                        else:
                            st.toast(f"❌ Not enough XP! You need {cost} XP.", icon="⚠️")

# ==========================================
# PAGE 3: BADGES
# ==========================================
elif st.session_state.page == "badges":
    header_html, profile = get_header()
    st.button("⬅ BACK TO SEASON", on_click=navigate, args=("overview",))
    st.markdown(f"<h1 style='color: #ff7b00; display: inline;'>BADGES</h1> <br> {header_html}", unsafe_allow_html=True)

    badges_df = db.fetch_df("SELECT * FROM badges WHERE player_id = ?", (st.session_state.current_player_id,))
    cols = st.columns(3)

    for idx, row in badges_df.iterrows():
        badge_name = row['badge_name']
        tier = row['tier']
        cost = row['cost']
        unlocked = row['unlocked']

        col = cols[idx % 3]
        with col:
            if unlocked == 1:
                st.button(f"✅ {badge_name} ({tier}) • UNLOCKED", key=f"b_un_{badge_name}", disabled=True,
                          use_container_width=True)
            else:
                btn_label = f"🔒 {badge_name} ({tier})  •  {cost} XP"
                if st.button(btn_label, key=f"b_buy_{badge_name}", use_container_width=True):
                    if profile['total_xp'] >= cost:
                        db.commit_badge_update(st.session_state.current_player_id, badge_name, 1, cost)
                        st.toast(f"🎉 Successfully unlocked {badge_name}!", icon="🔥")
                        st.rerun()
                    else:
                        st.toast(f"❌ Not enough XP! You need {cost} XP.", icon="⚠️")