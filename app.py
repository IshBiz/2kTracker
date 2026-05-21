import streamlit as st
import pandas as pd
import database as db
import json

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
    div.stButton > button { background-color: #222222; color: #e0e0e0; border: 1px solid #333333; border-radius: 4px; font-size: 14px; padding: 10px; width: 100%;}
    div.stButton > button:hover { border-color: #ff7b00; color: #ff7b00; background-color: #1a1a1a;}
    div.stButton > button:focus:not(:active) { border-color: #ff7b00; color: #ff7b00;}
    .metric-value {font-size: 32px; font-weight: bold; color: white;}
    .metric-label {font-size: 12px; color: #888; text-transform: uppercase;}
    [data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"] { display: none !important;}
    </style>
""", unsafe_allow_html=True)

if 'page' not in st.session_state: st.session_state.page = "landing"
if 'current_player_id' not in st.session_state: st.session_state.current_player_id = None
if 'attr_cart' not in st.session_state: st.session_state.attr_cart = {}
if 'badge_cart' not in st.session_state: st.session_state.badge_cart = {}


def navigate(page_name):
    st.session_state.attr_cart = {}
    st.session_state.badge_cart = {}
    st.session_state.page = page_name


def get_header(pending_cost=0, projected_ovr=None):
    profile = db.fetch_df("SELECT * FROM player_profile WHERE id = ?", (st.session_state.current_player_id,)).iloc[0]
    remaining_xp = int(profile['total_xp']) - pending_cost

    if pending_cost > 0:
        xp_display = f"<span style='float: right; font-size: 20px;'>XP <span class='orange-text'>{remaining_xp:,}</span> <span style='color: #ff4b4b; font-size: 16px;'>(-{pending_cost:,})</span></span>"
    else:
        xp_display = f"<span style='float: right; font-size: 20px;'>XP <span class='orange-text'>{int(profile['total_xp']):,}</span></span>"

    ovr = projected_ovr if projected_ovr else int(profile['overall_rating'])
    ovr_display = f"<span class='orange-text'>{ovr} OVR</span>"
    header_str = f"<strong>{profile['name']}</strong> | {profile['position']} | #{profile['jersey_number']} | {ovr_display} | Season {int(profile['current_season'])} {xp_display}"
    return header_str, profile


# ==========================================
# PAGE 0: LANDING
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
            player_options = {f"{row['name']} | {row['position']} | {row['overall_rating']} OVR": int(row['id']) for
                              _, row in players_df.iterrows()}
            selected_label = st.selectbox("Select Player Save", list(player_options.keys()))
            selected_id = player_options[selected_label]
            if st.button("LOAD PLAYER", key="load_btn"):
                st.session_state.current_player_id = selected_id
                navigate("overview")
                st.rerun()
            with st.expander("⚠️ DELETE THIS CAREER"):
                st.error("This will permanently wipe this player's stats and games.")
                confirm_del = st.checkbox(f"I understand, delete {selected_label.split(' | ')[0]}")
                if st.button("CONFIRM DELETE", disabled=not confirm_del):
                    db.delete_player(selected_id)
                    st.success("Career successfully deleted!")
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
                jersey = st.number_input("Jersey", 0, 99, 0)
            with c2:
                weight = st.number_input("Weight (lbs)", 150, 400, 220)
            with c3:
                wingspan = st.number_input("Wingspan (ft)", min_value=5.0, max_value=9.0, value=6.8, format="%.1f")
            if st.form_submit_button("CREATE CAREER"):
                if name:
                    new_id = db.create_player(name, pos, jersey, weight, wingspan)
                    st.session_state.current_player_id = new_id
                    navigate("overview")
                    st.rerun()
                else:
                    st.error("Player name is required.")

# ==========================================
# PAGE 1: OVERVIEW
# ==========================================
elif st.session_state.page == "overview":
    header_html, profile = get_header()
    # Explicitly cast to Python int to prevent numpy blob errors
    curr_season = int(profile['current_season'])

    if st.button("⬅ CHANGE PLAYER / MAIN MENU"):
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
                stats['fgm'] = st.number_input("FGM", 0);
                stats['tpm'] = st.number_input("3PM", 0)
                stats['ftm'] = st.number_input("FTM", 0);
                stats['ast'] = st.number_input("AST", 0)
                stats['dreb'] = st.number_input("DREB", 0);
                stats['stl'] = st.number_input("STL", 0)
                stats['dunks'] = st.number_input("DUNKS", 0);
                stats['win'] = st.checkbox("WIN")
            with c2:
                stats['fga'] = st.number_input("FGA", 0);
                stats['tpa'] = st.number_input("3PA", 0)
                stats['fta'] = st.number_input("FTA", 0);
                stats['to_val'] = st.number_input("TO", 0)
                stats['oreb'] = st.number_input("OREB", 0);
                stats['fls'] = st.number_input("FLS", 0)
                stats['blk'] = st.number_input("BLK", 0)

            if st.form_submit_button("SUBMIT GAME"):
                stats['fgm'] = max(stats['fgm'], stats['tpm'])
                stats['fga'] = max(stats['fga'], stats['fgm'])
                stats['tpa'] = max(stats['tpa'], stats['tpm'])
                pts = ((stats['fgm'] - stats['tpm']) * 2) + (stats['tpm'] * 3) + stats['ftm']
                reb = stats['dreb'] + stats['oreb']

                base_salary = 300
                win_bonus = 250 if stats['win'] else 0
                positive_xp = (pts * 8) + (stats['ast'] * 20) + (reb * 12) + (stats['blk'] * 40) + (stats['stl'] * 40)
                negative_xp = (stats['to_val'] * 20) + (stats['fls'] * 15) + ((stats['fga'] - stats['fgm']) * 5)
                final_xp = max(50, int(base_salary + win_bonus + positive_xp - negative_xp))

                uncompleted_df = db.fetch_df("SELECT * FROM endorsements WHERE player_id = ? AND completed = 0",
                                             (st.session_state.current_player_id,))
                unlocked_msgs = []
                games_played = len(
                    db.fetch_df("SELECT id FROM games WHERE player_id = ?", (st.session_state.current_player_id,))) + 1

                if not uncompleted_df.empty:
                    for _, endo in uncompleted_df.iterrows():
                        name = endo['endorsement_name']
                        payout = int(endo['payout'])
                        unlocked = False
                        if name == 'Shoe Deal: The 40-Bomb' and pts >= 40:
                            unlocked = True
                        elif name == 'National TV: 50-Point Game' and pts >= 50:
                            unlocked = True
                        elif name == 'Energy Drink: Triple Double':
                            doubles = sum([1 for x in [pts, reb, stats['ast'], stats['stl'], stats['blk']] if x >= 10])
                            if doubles >= 3: unlocked = True
                        elif name == 'Cereal Box: Rainmaker' and stats['tpm'] >= 10:
                            unlocked = True
                        elif name == 'Apparel Sponsor: Defensive Menace' and stats['stl'] >= 5 and stats['blk'] >= 5:
                            unlocked = True
                        elif name == 'State Farm: The Playmaker' and stats['ast'] >= 20:
                            unlocked = True
                        elif name == 'Gatorade: Board Man Gets Paid' and reb >= 25:
                            unlocked = True
                        elif name == 'Local Hero: 10 Games Played' and games_played >= 10:
                            unlocked = True

                        if unlocked:
                            db.complete_endorsement(st.session_state.current_player_id, name, payout)
                            unlocked_msgs.append(f"🏆 {name} (+{payout:,} XP)")

                db.insert_game(st.session_state.current_player_id, curr_season, stats, final_xp)
                if unlocked_msgs:
                    for msg in unlocked_msgs: st.toast(msg, icon="💰")
                    st.balloons()
                st.rerun()

    with col_right:
        st.markdown(f"<h1>SEASON {curr_season} OVERVIEW</h1>", unsafe_allow_html=True)
        games_df = db.fetch_df("SELECT * FROM games WHERE player_id = ? AND season_number = ?",
                               (st.session_state.current_player_id, curr_season))

        if not games_df.empty:
            games_df['fgm_adj'] = games_df[['fgm', 'tpm']].max(axis=1)
            games_df['fga_adj'] = games_df[['fga', 'fgm_adj']].max(axis=1)
            games_df['tpa_adj'] = games_df[['tpa', 'tpm']].max(axis=1)
            games_df['pts'] = ((games_df['fgm_adj'] - games_df['tpm']) * 2) + (games_df['tpm'] * 3) + games_df['ftm']
            games_df['reb'] = games_df['dreb'] + games_df['oreb']

            wins = int(games_df['win'].sum())
            losses = len(games_df) - wins
            total_fgm = games_df['fgm_adj'].sum()
            total_fga = games_df['fga_adj'].sum()
            fg_pct = (total_fgm / total_fga * 100) if total_fga > 0 else 0.0
            total_tpm = games_df['tpm'].sum()
            total_tpa = games_df['tpa_adj'].sum()
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
            st.markdown("### RECENT GAMES")

            recent_games = games_df.tail(5).iloc[::-1]
            for _, game in recent_games.iterrows():
                w_l = "W" if game['win'] else "L"
                border_col = "#00ff00" if game['win'] else "#ff4b4b"

                st.markdown(f"""
                    <div style='background-color: #222222; padding: 12px 15px; border-left: 5px solid {border_col}; border-radius: 4px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.2);'>
                        <span style='font-weight: bold; font-size: 18px; color: {border_col}; width: 35px;'>{w_l}</span>
                        <span style='color: #e0e0e0; font-size: 15px; flex-grow: 1; text-align: left;'>
                            <b style='color:#ffffff;'>{int(game['pts'])}</b> PTS &nbsp;|&nbsp; 
                            <b style='color:#ffffff;'>{int(game['reb'])}</b> REB &nbsp;|&nbsp; 
                            <b style='color:#ffffff;'>{int(game['ast'])}</b> AST &nbsp;|&nbsp; 
                            <b style='color:#ffffff;'>{int(game['stl'])}</b> STL &nbsp;|&nbsp; 
                            <b style='color:#ffffff;'>{int(game['blk'])}</b> BLK
                        </span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No games played in Season {curr_season} yet.")

    st.markdown("---")
    nav1, nav2, nav3, nav4 = st.columns(4)
    with nav1:
        st.button("ATTRIBUTES ➔", on_click=navigate, args=("attributes",))
    with nav2:
        st.button("BADGES ➔", on_click=navigate, args=("badges",))
    with nav3:
        st.button("ENDORSEMENTS ➔", on_click=navigate, args=("endorsements",))
    with nav4:
        st.button("CAREER / SEASONS ➔", on_click=navigate, args=("career",))

# ==========================================
# PAGE 2: ATTRIBUTES
# ==========================================
elif st.session_state.page == "attributes":
    attr_df = db.fetch_df("SELECT * FROM player_attributes WHERE player_id = ?", (st.session_state.current_player_id,))
    categories = attr_df['category'].unique()


    def calculate_upgrade_cost(start_lvl, target_lvl, multiplier):
        total = 0
        for lvl in range(start_lvl, target_lvl):
            if lvl < 60:
                base = 25
            else:
                base = 50 + ((lvl - 60) ** 1.8) * 8
            total += int(base * multiplier)
        return total


    pending_cost = 0
    upgrades_to_commit = {}
    simulated_attrs = {}
    for _, row in attr_df.iterrows():
        attr_name = row['attribute_name']
        curr_lvl = int(row['current_level'])
        if attr_name in st.session_state.attr_cart:
            target_lvl = st.session_state.attr_cart[attr_name]
            cost = calculate_upgrade_cost(curr_lvl, target_lvl, row['cost_multiplier'])
            pending_cost += cost
            upgrades_to_commit[attr_name] = target_lvl
            simulated_attrs[attr_name] = target_lvl
        else:
            simulated_attrs[attr_name] = curr_lvl

    raw_profile = db.fetch_df("SELECT position, overall_rating FROM player_profile WHERE id = ?",
                              (st.session_state.current_player_id,)).iloc[0]
    current_ovr = int(raw_profile['overall_rating'])
    projected_ovr = db.calculate_ovr(raw_profile['position'], simulated_attrs)

    header_html, profile = get_header(pending_cost, projected_ovr)
    st.button("⬅ BACK TO SEASON", on_click=navigate, args=("overview",))
    st.markdown(f"<h1 style='color: #ff7b00; display: inline;'>ATTRIBUTES</h1> <br> {header_html}",
                unsafe_allow_html=True)
    st.caption("Click any attribute to allocate a point. Your XP is only spent when you click Confirm.")

    remaining_xp = int(profile['total_xp']) - pending_cost
    st.markdown("### 🛒 Upgrade Cart")
    if projected_ovr > current_ovr: st.success(
        f"📈 **OVR Increase:** Your pending upgrades will raise your overall from {current_ovr} to **{projected_ovr}**!")

    c1, c2, c3 = st.columns([1, 1, 3])
    with c1:
        if st.button("✅ CONFIRM & PAY", disabled=(pending_cost == 0 or remaining_xp < 0), use_container_width=True):
            db.commit_batch_attribute_upgrades(st.session_state.current_player_id, upgrades_to_commit, pending_cost,
                                               projected_ovr)
            st.session_state.attr_cart = {}
            st.toast("Attributes upgraded successfully!", icon="🔥")
            if projected_ovr > current_ovr: st.balloons()
            st.rerun()
    with c2:
        if st.button("❌ RESET CART", disabled=(pending_cost == 0), use_container_width=True):
            st.session_state.attr_cart = {}
            st.rerun()

    st.markdown("---")
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
                virtual_lvl = st.session_state.attr_cart.get(attr_name, curr_lvl)
                if virtual_lvl >= int(row['max_level']):
                    st.button(f"⭐ {attr_name} (MAX)", key=f"max_attr_{attr_name}", disabled=True,
                              use_container_width=True)
                else:
                    next_click_cost = calculate_upgrade_cost(virtual_lvl, virtual_lvl + 1, row['cost_multiplier'])
                    can_afford = remaining_xp >= next_click_cost
                    prefix = "🛒" if virtual_lvl > curr_lvl else "➕"
                    if st.button(f"{prefix} {attr_name}: {virtual_lvl}  •  {next_click_cost} XP",
                                 key=f"up_attr_{attr_name}", disabled=not can_afford, use_container_width=True):
                        st.session_state.attr_cart[attr_name] = virtual_lvl + 1
                        st.rerun()

# ==========================================
# PAGE 3: BADGES
# ==========================================
elif st.session_state.page == "badges":
    TIER_INFO = {
        0: {"name": "Locked", "bg": "#333333", "text": "#aaaaaa", "cost_to_next": 1500},
        1: {"name": "Bronze", "bg": "#cd7f32", "text": "#ffffff", "cost_to_next": 4000},
        2: {"name": "Silver", "bg": "#c0c0c0", "text": "#000000", "cost_to_next": 10000},
        3: {"name": "Gold", "bg": "#ffd700", "text": "#000000", "cost_to_next": 25000},
        4: {"name": "HoF", "bg": "#800080", "text": "#ffffff", "cost_to_next": 50000},
        5: {"name": "Legend", "bg": "#ff0000", "text": "#ffffff", "cost_to_next": None}
    }

    badges_df = db.fetch_df("SELECT * FROM badges WHERE player_id = ?", (st.session_state.current_player_id,))
    categories = badges_df['category'].unique()

    pending_cost = 0
    upgrades_to_commit = {}
    for _, row in badges_df.iterrows():
        badge_name = row['badge_name']
        curr_lvl = int(row['level'])
        if badge_name in st.session_state.badge_cart:
            target_lvl = st.session_state.badge_cart[badge_name]
            cost = sum(TIER_INFO[lvl]["cost_to_next"] for lvl in range(curr_lvl, target_lvl))
            pending_cost += cost
            upgrades_to_commit[badge_name] = target_lvl

    header_html, profile = get_header(pending_cost)
    st.button("⬅ BACK TO SEASON", on_click=navigate, args=("overview",))
    st.markdown(f"<h1 style='color: #ff7b00; display: inline;'>BADGES</h1> <br> {header_html}", unsafe_allow_html=True)

    remaining_xp = int(profile['total_xp']) - pending_cost
    st.markdown("### 🛒 Upgrade Cart")
    c1, c2, c3 = st.columns([1, 1, 3])
    with c1:
        if st.button("✅ CONFIRM & PAY", disabled=(pending_cost == 0 or remaining_xp < 0), use_container_width=True):
            db.commit_batch_badge_upgrades(st.session_state.current_player_id, upgrades_to_commit, pending_cost)
            st.session_state.badge_cart = {}
            st.toast("Badges upgraded successfully!", icon="🔥")
            st.rerun()
    with c2:
        if st.button("❌ RESET CART", disabled=(pending_cost == 0), use_container_width=True):
            st.session_state.badge_cart = {}
            st.rerun()
    st.markdown("---")

    cols = st.columns(len(categories))
    for i, cat in enumerate(categories):
        with cols[i]:
            st.markdown(
                f"<h4 style='color:#a0a0a0; border-bottom: 1px solid #333; padding-bottom: 5px; margin-bottom: 15px; font-size: 16px;'>{cat}</h4>",
                unsafe_allow_html=True)
            cat_df = badges_df[badges_df['category'] == cat]
            for _, row in cat_df.iterrows():
                badge_name = row['badge_name']
                curr_lvl = int(row['level'])
                virtual_lvl = st.session_state.badge_cart.get(badge_name, curr_lvl)

                bg_color = TIER_INFO[virtual_lvl]["bg"]
                text_color = TIER_INFO[virtual_lvl]["text"]
                tier_name = TIER_INFO[virtual_lvl]["name"]

                st.markdown(
                    f"<div style='background-color: {bg_color}; color: {text_color}; padding: 8px; border-radius: 4px; text-align: center; font-weight: bold; font-size: 14px; margin-bottom: 5px;'>{badge_name}<br><span style='font-size:11px; font-weight:normal;'>{tier_name}</span></div>",
                    unsafe_allow_html=True)

                if virtual_lvl >= 5:
                    st.button("MAX TIER", key=f"max_badge_{badge_name}", disabled=True, use_container_width=True)
                else:
                    next_cost = TIER_INFO[virtual_lvl]["cost_to_next"]
                    can_afford = remaining_xp >= next_cost
                    prefix = "🛒" if virtual_lvl > curr_lvl else "➕"
                    if st.button(f"{prefix} Upgrade ({next_cost:,} XP)", key=f"up_badge_{badge_name}",
                                 disabled=not can_afford, use_container_width=True):
                        st.session_state.badge_cart[badge_name] = virtual_lvl + 1
                        st.rerun()
                st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# ==========================================
# PAGE 4: ENDORSEMENTS
# ==========================================
elif st.session_state.page == "endorsements":
    header_html, profile = get_header()
    st.button("⬅ BACK TO SEASON", on_click=navigate, args=("overview",))
    st.markdown(f"<h1 style='color: #ff7b00; display: inline;'>ENDORSEMENTS</h1> <br> {header_html}",
                unsafe_allow_html=True)
    st.caption("Hit these milestones during your games to trigger massive one-time XP sponsorship payouts.")

    endorsements_df = db.fetch_df("SELECT * FROM endorsements WHERE player_id = ?",
                                  (st.session_state.current_player_id,))
    cols = st.columns(3)
    for idx, row in endorsements_df.iterrows():
        col = cols[idx % 3]
        with col:
            name = row['endorsement_name']
            desc = row['description']
            payout = int(row['payout'])
            completed = int(row['completed'])

            if completed:
                bg_color, border_color, status, text_color = "#1a3a1a", "#00ff00", "✅ COMPLETED", "#aaaaaa"
            else:
                bg_color, border_color, status, text_color = "#222222", "#ff7b00", f"💰 {payout:,} XP", "#ffffff"

            st.markdown(
                f"<div style='background-color: {bg_color}; color: {text_color}; padding: 15px; border-left: 4px solid {border_color}; border-radius: 4px; margin-bottom: 15px;'><div style='font-size: 16px; font-weight: bold; margin-bottom: 5px; color: #ffffff;'>{name}</div><div style='font-size: 12px; margin-bottom: 10px; height: 35px;'>{desc}</div><div style='font-size: 14px; font-weight: bold; color: {border_color};'>{status}</div></div>",
                unsafe_allow_html=True)

# ==========================================
# PAGE 5: CAREER & SEASONS
# ==========================================
elif st.session_state.page == "career":
    header_html, profile = get_header()
    # Explicitly cast to Python int to prevent numpy blob errors
    curr_season = int(profile['current_season'])

    st.button("⬅ BACK TO SEASON", on_click=navigate, args=("overview",))
    st.markdown(f"<h1 style='color: #ff7b00; display: inline;'>CAREER & AWARDS</h1> <br> {header_html}",
                unsafe_allow_html=True)

    st.subheader("Historical Seasons")
    seasons_df = db.fetch_df(
        "SELECT season_number, games_played, wins, losses, ppg, rpg, apg, spg, bpg, awards_json FROM season_records WHERE player_id = ? ORDER BY season_number ASC",
        (st.session_state.current_player_id,))

    if not seasons_df.empty:
        for _, row in seasons_df.iterrows():
            awards_list = json.loads(row['awards_json']) if row['awards_json'] and row['awards_json'] != "[]" else []
            awards_str = " &nbsp;|&nbsp; ".join([f"🏆 {a}" for a in awards_list]) if awards_list else "No Major Awards"

            st.markdown(f"""
                <div style='background-color: #1e1e1e; border: 1px solid #333333; border-radius: 6px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);'>
                    <div style='display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 15px;'>
                        <span style='font-size: 20px; font-weight: bold; color: #ff7b00;'>SEASON {int(row['season_number'])}</span>
                        <span style='font-size: 16px; color: #aaaaaa; padding-top: 3px;'>
                            {int(row['games_played'])} GP &nbsp;|&nbsp; 
                            <span style='color:#00ff00; font-weight: bold;'>{int(row['wins'])}W</span> - <span style='color:#ff4b4b; font-weight: bold;'>{int(row['losses'])}L</span>
                        </span>
                    </div>

                    <div style='display: flex; justify-content: space-around; margin-bottom: 15px;'>
                        <div style='text-align: center;'><div style='font-size: 12px; color: #888888; text-transform: uppercase;'>PPG</div><div style='font-size: 24px; font-weight: bold; color: #ffffff;'>{float(row['ppg']):.1f}</div></div>
                        <div style='text-align: center;'><div style='font-size: 12px; color: #888888; text-transform: uppercase;'>RPG</div><div style='font-size: 24px; font-weight: bold; color: #ffffff;'>{float(row['rpg']):.1f}</div></div>
                        <div style='text-align: center;'><div style='font-size: 12px; color: #888888; text-transform: uppercase;'>APG</div><div style='font-size: 24px; font-weight: bold; color: #ffffff;'>{float(row['apg']):.1f}</div></div>
                        <div style='text-align: center;'><div style='font-size: 12px; color: #888888; text-transform: uppercase;'>SPG</div><div style='font-size: 24px; font-weight: bold; color: #ffffff;'>{float(row['spg']):.1f}</div></div>
                        <div style='text-align: center;'><div style='font-size: 12px; color: #888888; text-transform: uppercase;'>BPG</div><div style='font-size: 24px; font-weight: bold; color: #ffffff;'>{float(row['bpg']):.1f}</div></div>
                    </div>

                    <div style='font-size: 14px; color: #ffd700; font-weight: bold; background-color: #2a2a2a; padding: 10px; border-radius: 4px; text-align: center;'>
                        {awards_str}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("You haven't completed a season yet. End your current season to log your stats here.")

    st.markdown("---")

    st.subheader(f"End Season {curr_season}")
    games_df = db.fetch_df("SELECT * FROM games WHERE player_id = ? AND season_number = ?",
                           (st.session_state.current_player_id, curr_season))

    if games_df.empty:
        st.warning("You must play at least one game to end the season.")
    else:
        with st.expander("🏁 ADVANCE TO NEXT SEASON", expanded=True):
            st.markdown(
                "Select any awards you won this year. Be honest! These will be permanently etched into your legacy and pay out massive XP.")
            with st.form("end_season_form"):
                a1, a2 = st.columns(2)
                with a1:
                    aw_champ = st.checkbox("NBA Champion (50,000 XP)")
                    aw_fmvp = st.checkbox("Finals MVP (25,000 XP)")
                    aw_mvp = st.checkbox("League MVP (25,000 XP)")
                with a2:
                    aw_dpoy = st.checkbox("Defensive Player of the Year (15,000 XP)")
                    aw_roy = st.checkbox("Rookie of the Year (15,000 XP)")
                    aw_allnba = st.checkbox("All-NBA First Team (10,000 XP)")

                if st.form_submit_button("LOCK IN AWARDS & START NEW SEASON"):
                    aw_payout = 0
                    aw_list = []
                    if aw_champ: aw_payout += 50000; aw_list.append("NBA Champion")
                    if aw_fmvp: aw_payout += 25000; aw_list.append("Finals MVP")
                    if aw_mvp: aw_payout += 25000; aw_list.append("MVP")
                    if aw_dpoy: aw_payout += 15000; aw_list.append("DPOY")
                    if aw_roy: aw_payout += 15000; aw_list.append("ROY")
                    if aw_allnba: aw_payout += 10000; aw_list.append("All-NBA 1st Team")

                    games_df['fgm_adj'] = games_df[['fgm', 'tpm']].max(axis=1)
                    games_df['pts'] = ((games_df['fgm_adj'] - games_df['tpm']) * 2) + (games_df['tpm'] * 3) + games_df[
                        'ftm']

                    # Strictly cast pandas aggregations to Python primitives to protect SQLite
                    stats_summary = {
                        "gp": int(len(games_df)),
                        "wins": int(games_df['win'].sum()),
                        "losses": int(len(games_df) - int(games_df['win'].sum())),
                        "ppg": float(round(games_df['pts'].mean(), 1)),
                        "rpg": float(round((games_df['dreb'] + games_df['oreb']).mean(), 1)),
                        "apg": float(round(games_df['ast'].mean(), 1)),
                        "spg": float(round(games_df['stl'].mean(), 1)),
                        "bpg": float(round(games_df['blk'].mean(), 1))
                    }

                    db.process_season_end(st.session_state.current_player_id, curr_season, stats_summary, aw_list,
                                          aw_payout)
                    st.toast(f"Season {curr_season} completed! Earned {aw_payout:,} XP.", icon="🏆")
                    st.rerun()