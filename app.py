import streamlit as st
import pandas as pd
import database as db
import json

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

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
if 'celebration' not in st.session_state: st.session_state.celebration = None


def navigate(page_name):
    st.session_state.attr_cart = {}
    st.session_state.badge_cart = {}
    st.session_state.page = page_name


def show_pending_celebration():
    celebration = st.session_state.get("celebration")
    if not celebration:
        return

    st.toast(celebration["message"], icon=celebration.get("icon", "🔥"))
    if celebration.get("effect") == "snow":
        st.snow()
    else:
        st.balloons()
    st.session_state.celebration = None


def get_archetype_key(profile):
    return profile.get("archetype", "balanced_star") if hasattr(profile, "get") else "balanced_star"


def calculate_takeover_bonus(stats, pts, reb, archetype_key):
    if archetype_key == "sharpshooter":
        return stats['tpm'] * 24
    if archetype_key == "lockdown_defender":
        return (stats['stl'] * 40) + (stats['blk'] * 40)
    if archetype_key == "slashing_playmaker":
        return (stats['ast'] * 20) + (stats['dunks'] * 30)
    if archetype_key == "playmaking_shot_creator":
        return (stats['ast'] * 20) + (stats['fgm'] * 8)
    if archetype_key == "two_way_finisher":
        return (stats['dunks'] * 35) + (stats['stl'] * 25) + (stats['blk'] * 25)
    if archetype_key == "rim_protector":
        return (stats['blk'] * 40) + (reb * 6)
    if archetype_key == "glass_cleaner":
        return reb * 12
    if archetype_key == "inside_out_scorer":
        return (stats['tpm'] * 16) + (stats['dunks'] * 25)
    return 0


def game_matches_endorsement(name, stats, pts, reb, games_played):
    if name == 'Shoe Deal: The 40-Bomb':
        return pts >= 40
    if name == 'National TV: 50-Point Game':
        return pts >= 50
    if name == 'Energy Drink: Triple Double':
        return sum([1 for x in [pts, reb, stats['ast'], stats['stl'], stats['blk']] if x >= 10]) >= 3
    if name == 'Cereal Box: Rainmaker':
        return stats['tpm'] >= 10
    if name == 'Apparel Sponsor: Defensive Menace':
        return stats['stl'] >= 5 and stats['blk'] >= 5
    if name == 'State Farm: The Playmaker':
        return stats['ast'] >= 20
    if name == 'Gatorade: Board Man Gets Paid':
        return reb >= 25
    if name == 'Local Hero: 10 Games Played':
        return games_played >= 10
    if name == 'Foot Locker: Sniper Night':
        return stats['tpm'] >= 12
    if name == 'Splash Brothers Feature':
        return pts >= 35 and stats['tpm'] >= 8
    if name == 'Jordan Brand: Clamp Session':
        return stats['stl'] >= 7
    if name == 'NBA Cares: No Fly Zone':
        return stats['blk'] >= 6
    if name == 'Sprite: Highlight Factory':
        return stats['dunks'] >= 5 and stats['ast'] >= 10
    if name == 'And1: Rim Pressure':
        return stats['fta'] >= 12
    if name == 'Tissot: Shot Clock Killer':
        return pts >= 30 and stats['ast'] >= 10
    if name == 'Ankle Tape Sponsor':
        return stats['ast'] >= 20
    if name == 'Above The Rim Mixtape':
        return stats['dunks'] >= 8
    if name == 'Two-Way Takeover Feature':
        return pts >= 25 and stats['stl'] >= 3 and stats['blk'] >= 3
    if name == 'Block Party Broadcast':
        return stats['blk'] >= 8
    if name == 'Paint Patrol Sponsor':
        return stats['blk'] >= 5 and stats['win']
    if name == 'Board Man Elite':
        return reb >= 30
    if name == 'Second-Chance Sponsor':
        return stats['oreb'] >= 10
    if name == 'Three-Level Clinic':
        return pts >= 40 and stats['tpm'] >= 4 and stats['dunks'] >= 3
    if name == 'Offensive Threat Feature':
        return pts >= 55
    return False


def season_award_endorsement_matches(name, awards_won):
    award_set = set(awards_won)
    award_triggers = {
        'Three-Point Crown Campaign': 'MVP',
        'Kia Defensive Legacy': 'DPOY',
        'Anchor of the Year': 'DPOY',
        'Floor General Spotlight': 'All-NBA 1st Team',
        'All-NBA Two-Way Bonus': 'All-NBA 1st Team',
        'Glass Work All-NBA Bonus': 'All-NBA 1st Team',
        'MVP Campaign: Creator Edition': 'MVP',
        'Scoring Champ MVP Push': 'MVP',
    }
    return award_triggers.get(name) in award_set


def prepare_games_df(games_df):
    if games_df.empty:
        return games_df
    games_df = games_df.copy()
    games_df['fgm_adj'] = games_df[['fgm', 'tpm']].max(axis=1)
    games_df['fga_adj'] = games_df[['fga', 'fgm_adj']].max(axis=1)
    games_df['tpa_adj'] = games_df[['tpa', 'tpm']].max(axis=1)
    games_df['pts'] = ((games_df['fgm_adj'] - games_df['tpm']) * 2) + (games_df['tpm'] * 3) + games_df['ftm']
    games_df['reb'] = games_df['dreb'] + games_df['oreb']
    games_df['game_no'] = games_df.groupby('season_number').cumcount() + 1
    return games_df


def get_build_radar_values(player_id):
    attr_df = db.fetch_df("SELECT category, attribute_name, current_level FROM player_attributes WHERE player_id = ?",
                          (player_id,))
    groups = {
        "Inside Scoring": ["Close Shot", "Driving Layup", "Standing Dunk", "Driving Dunk", "Post Hook",
                           "Post Control", "Draw Foul"],
        "Outside Scoring": ["Mid-Range Shot", "Three-Point Shot", "Free Throw", "Post Fade", "Shot IQ",
                            "Offensive Consistency"],
        "Playmaking": ["Ball Handle", "Pass IQ", "Pass Accuracy", "Pass Vision", "Hands", "Speed With Ball"],
        "Defense": ["Interior Defense", "Perimeter Defense", "Block", "Steal", "Offensive Rebound",
                    "Defensive Rebound", "Defensive Consistency", "Help Defense IQ", "Pass Perception"],
        "Athleticism": ["Speed", "Vertical", "Strength", "Stamina", "Hustle", "Agility"],
    }
    values = {}
    for label, attrs in groups.items():
        subset = attr_df[attr_df['attribute_name'].isin(attrs)]
        values[label] = float(subset['current_level'].mean()) if not subset.empty else 0.0
    return values


def render_build_radar(player_id):
    radar_values = get_build_radar_values(player_id)
    labels = list(radar_values.keys())
    values = list(radar_values.values())

    if go:
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=labels + [labels[0]],
            fill='toself',
            line=dict(color='#ff7b00', width=3),
            fillcolor='rgba(255, 123, 0, 0.28)',
            name='Build'
        ))
        fig.update_layout(
            template=None,
            paper_bgcolor='#1a1a1a',
            plot_bgcolor='#1a1a1a',
            font=dict(color='#e0e0e0'),
            margin=dict(l=30, r=30, t=20, b=20),
            polar=dict(
                bgcolor='#1a1a1a',
                radialaxis=dict(visible=True, range=[0, 99], gridcolor='#333333', tickfont=dict(color='#888888')),
                angularaxis=dict(gridcolor='#333333')
            ),
            showlegend=False,
            height=360,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Plotly is not installed, so the radar chart is shown as fallback bars.")
        for label, value in radar_values.items():
            st.progress(value / 99, text=f"{label}: {value:.1f}")


def get_header(pending_cost=0, projected_ovr=None):
    profile = db.fetch_df("SELECT * FROM player_profile WHERE id = ?", (st.session_state.current_player_id,)).iloc[0]
    remaining_xp = int(profile['total_xp']) - pending_cost

    if pending_cost > 0:
        xp_display = f"<span style='float: right; font-size: 20px;'>XP <span class='orange-text'>{remaining_xp:,}</span> <span style='color: #ff4b4b; font-size: 16px;'>(-{pending_cost:,})</span></span>"
    else:
        xp_display = f"<span style='float: right; font-size: 20px;'>XP <span class='orange-text'>{int(profile['total_xp']):,}</span></span>"

    ovr = projected_ovr if projected_ovr else int(profile['overall_rating'])
    ovr_display = f"<span class='orange-text'>{ovr} OVR</span>"
    archetype = db.get_archetype(get_archetype_key(profile))
    header_str = f"<strong>{profile['name']}</strong> | {profile['position']} | #{profile['jersey_number']} | {ovr_display} | {archetype['name']} | Season {int(profile['current_season'])} {xp_display}"
    return header_str, profile


def validate_and_adjust_game_stats(stats):
    warnings = []

    if stats["tpm"] > stats["fgm"]:
        warnings.append(f"You entered {stats['tpm']} made threes but only {stats['fgm']} field goals. FGM will be adjusted to {stats['tpm']}.")
        stats["fgm"] = stats["tpm"]

    if stats["fgm"] > stats["fga"]:
        warnings.append(f"You entered {stats['fgm']} made field goals but only {stats['fga']} field goal attempts. FGA will be adjusted to {stats['fgm']}.")
        stats["fga"] = stats["fgm"]

    if stats["tpm"] > stats["tpa"]:
        warnings.append(f"You entered {stats['tpm']} made threes but only {stats['tpa']} three-point attempts. 3PA will be adjusted to {stats['tpm']}.")
        stats["tpa"] = stats["tpm"]

    if stats["ftm"] > stats["fta"]:
        warnings.append(f"You entered {stats['ftm']} made free throws but only {stats['fta']} free throw attempts. FTA will be adjusted to {stats['ftm']}.")
        stats["fta"] = stats["ftm"]

    pts = ((stats["fgm"] - stats["tpm"]) * 2) + (stats["tpm"] * 3) + stats["ftm"]

    if stats["to_val"] >= 15:
        warnings.append("Turnovers are extremely high. Double-check that this is intentional.")
    if stats["fls"] >= 8:
        warnings.append("Fouls are extremely high. Double-check that this is intentional.")
    if pts > 150:
        warnings.append(f"You entered a {pts}-point game. If this is intentional, submit again after reviewing the numbers.")

    return stats, warnings


show_pending_celebration()

GAME_TYPE_MULTIPLIERS = {
                    "Regular Season": 1.0,
                    "Prime-Time/Rivalry": 1.2,
                    "Playoffs": 1.5,
                    "Elimination Game": 2.0,
                }

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
            archetype_options = {info["name"]: key for key, info in db.ARCHETYPES.items()}
            selected_archetype_name = st.selectbox("Archetype / Takeover", list(archetype_options.keys()))
            selected_archetype = db.get_archetype(archetype_options[selected_archetype_name])
            st.caption(f"{selected_archetype['takeover']} - {selected_archetype['description']} {selected_archetype['xp_bonus']}")
            create_archetype_key = archetype_options[selected_archetype_name]
            next_challenge = db.get_coach_challenge(create_archetype_key, 0)

            st.markdown(f"""
                <div style='background-color:#221a10; border:1px solid #ff7b00; border-radius:8px; padding:14px; margin-top:10px;'>
                    <div style='font-size:13px; color:#ffb066; text-transform:uppercase; font-weight:bold;'>Sample Coach's Challenge</div>
                    <div style='font-size:22px; color:#ffffff; font-weight:bold; margin-top:4px;'>{next_challenge['name']}</div>
                    <div style='font-size:14px; color:#dddddd; margin-top:4px;'>{next_challenge['description']}</div>
                    <div style='font-size:14px; color:#00ff99; font-weight:bold; margin-top:8px;'>Reward: +{int(next_challenge['bonus']):,} XP before game multiplier</div>
                </div>
            """, unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                jersey = st.number_input("Jersey", 0, 99, 0)
            with c2:
                height = st.text_input("Height", value="6'7\"", placeholder="6'7\"")
            with c3:
                weight = st.number_input("Weight (lbs)", 150, 400, 220)
            with c4:
                wingspan = st.number_input("Wingspan (ft)", min_value=5.0, max_value=9.0, value=6.8, format="%.1f")

            if st.form_submit_button("CREATE CAREER"):
                if name:
                    new_id = db.create_player(name, pos, jersey, weight, wingspan,
                                              archetype_options[selected_archetype_name], height)
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
    archetype_key = get_archetype_key(profile)
    archetype = db.get_archetype(archetype_key)

    if st.button("⬅ CHANGE PLAYER / MAIN MENU"):
        st.session_state.current_player_id = None
        navigate("landing")
        st.rerun()

    st.markdown(header_html, unsafe_allow_html=True)
    st.caption(f"{archetype['takeover']} - {archetype['xp_bonus']}")
    if archetype_key == "balanced_star":
        with st.expander("Set Archetype For This Save"):
            st.caption("Older saves default to Balanced Star. Pick one archetype to unlock its bonuses and endorsements.")
            migrated_options = {info["name"]: key for key, info in db.ARCHETYPES.items() if key != "balanced_star"}
            migrated_choice = st.selectbox("Choose Archetype", list(migrated_options.keys()))
            if st.button("LOCK ARCHETYPE", use_container_width=True):
                db.set_player_archetype(st.session_state.current_player_id, migrated_options[migrated_choice])
                st.session_state.celebration = {
                    "message": f"{migrated_choice} takeover activated!",
                    "effect": "balloons",
                    "icon": "🔥"
                }
                st.rerun()
    st.markdown("---")
    col_left, col_right = st.columns([1.2, 2.5])

    with col_left:
        with st.form("game_submission", clear_on_submit=True):
            st.markdown("### ENTER GAME STATS")
            st.markdown("#### Matchup Context")
            m1, m2 = st.columns(2)
            with m1:
                opponent_team = st.text_input("Opponent Team", placeholder="Lakers")
                home_away = st.selectbox("Home/Away", ["Home", "Away", "Neutral"])
                game_type = st.selectbox("Game Type", list(GAME_TYPE_MULTIPLIERS.keys()))
            with m2:
                your_team_score = st.number_input("Your Team Score", 0, 250, 0)
                opponent_score = st.number_input("Opponent Score", 0, 250, 0)
                is_playoffs = st.checkbox("Playoff Game")
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
                stats, validation_warnings = validate_and_adjust_game_stats(stats)
                for warning in validation_warnings:
                    st.warning(warning)
                pts = ((stats['fgm'] - stats['tpm']) * 2) + (stats['tpm'] * 3) + stats['ftm']
                reb = stats['dreb'] + stats['oreb']
                if your_team_score > 0 or opponent_score > 0:
                    stats['win'] = your_team_score > opponent_score

                base_salary = 300
                win_bonus = 250 if stats['win'] else 0
                positive_xp = (pts * 8) + (stats['ast'] * 20) + (reb * 12) + (stats['blk'] * 40) + (stats['stl'] * 40)
                negative_xp = (stats['to_val'] * 20) + (stats['fls'] * 15) + ((stats['fga'] - stats['fgm']) * 5)
                takeover_bonus = calculate_takeover_bonus(stats, pts, reb, archetype_key)
                raw_xp = max(50, int(base_salary + win_bonus + positive_xp + takeover_bonus - negative_xp))

                games_played_before = len(
                    db.fetch_df("SELECT id FROM games WHERE player_id = ?", (st.session_state.current_player_id,))
                )

                coach_challenge = db.get_coach_challenge(archetype_key, games_played_before)
                challenge_done = db.coach_challenge_completed(coach_challenge, stats, pts, reb)
                challenge_bonus = int(coach_challenge["bonus"]) if challenge_done else 0

                xp_multiplier = GAME_TYPE_MULTIPLIERS[game_type]
                final_xp = max(50, int((raw_xp + challenge_bonus) * xp_multiplier))

                stats["opponent_team"] = opponent_team
                stats["your_team_score"] = int(your_team_score)
                stats["opponent_score"] = int(opponent_score)
                stats["home_away"] = home_away
                stats["is_playoffs"] = int(is_playoffs or game_type in ["Playoffs", "Elimination Game"])
                stats["game_type"] = game_type
                stats["xp_multiplier"] = float(xp_multiplier)
                stats["coach_challenge_name"] = coach_challenge["name"]
                stats["coach_challenge_completed"] = int(challenge_done)
                stats["coach_challenge_bonus"] = challenge_bonus

                uncompleted_df = db.fetch_df("SELECT * FROM endorsements WHERE player_id = ? AND completed = 0",
                                             (st.session_state.current_player_id,))
                unlocked_msgs = []
                games_played = len(
                    db.fetch_df("SELECT id FROM games WHERE player_id = ?", (st.session_state.current_player_id,))) + 1

                if not uncompleted_df.empty:
                    for _, endo in uncompleted_df.iterrows():
                        name = endo['endorsement_name']
                        payout = int(endo['payout'])
                        unlocked = game_matches_endorsement(name, stats, pts, reb, games_played)

                        if unlocked:
                            db.complete_endorsement(st.session_state.current_player_id, name, payout)
                            unlocked_msgs.append(f"🏆 {name} (+{payout:,} XP)")

                new_game_id = db.insert_game(st.session_state.current_player_id, curr_season, stats, final_xp)
                db.check_game_milestones(st.session_state.current_player_id, new_game_id, curr_season, stats, pts, reb)
                if unlocked_msgs:
                    for msg in unlocked_msgs: st.toast(msg, icon="💰")
                    st.balloons()
                if takeover_bonus > 0:
                    st.toast(f"{archetype['name']} Takeover Bonus: +{takeover_bonus:,} XP", icon="🔥")
                st.rerun()

    with col_right:
        st.markdown(f"<h1>SEASON {curr_season} OVERVIEW</h1>", unsafe_allow_html=True)
        games_df = db.fetch_df("SELECT * FROM games WHERE player_id = ? AND season_number = ?",
                               (st.session_state.current_player_id, curr_season))
        games_df = prepare_games_df(games_df)

        if not games_df.empty:
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
            st.markdown("### BUILD RADAR")
            render_build_radar(st.session_state.current_player_id)

            st.markdown("---")
            st.markdown("### RECENT GAMES")

            recent_games = games_df.tail(5).iloc[::-1]
            for _, game in recent_games.iterrows():
                w_l = "W" if game['win'] else "L"
                border_col = "#00ff00" if game['win'] else "#ff4b4b"

                opponent = game.get("opponent_team", "") if hasattr(game, "get") else ""
                opponent = opponent if opponent else "Opponent"
                your_score = int(game.get("your_team_score", 0)) if "your_team_score" in game else 0
                opp_score = int(game.get("opponent_score", 0)) if "opponent_score" in game else 0
                score_text = f"{your_score}-{opp_score}" if your_score or opp_score else "Score N/A"
                venue = game.get("home_away", "Home") if "home_away" in game else "Home"
                game_type_label = game.get("game_type", "Regular Season") if "game_type" in game else "Regular Season"

                st.markdown(f"""
                    <div style='background-color: #222222; padding: 12px 15px; border-left: 5px solid {border_col}; border-radius: 4px; margin-bottom: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);'>
                        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;'>
                            <span style='font-weight: bold; font-size: 18px; color: {border_col};'>{w_l} vs {opponent}, {score_text}</span>
                            <span style='font-size:12px; color:#ffb066;'>{venue} • {game_type_label} • +{int(game['xp_earned']):,} XP</span>
                        </div>
                        <span style='color: #e0e0e0; font-size: 15px;'>
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
    nav1, nav2, nav3, nav4, nav5, nav6, nav7 = st.columns(7)
    with nav1:
        st.button("ATTRIBUTES ➔", on_click=navigate, args=("attributes",))
    with nav2:
        st.button("BADGES ➔", on_click=navigate, args=("badges",))
    with nav3:
        st.button("ENDORSEMENTS ➔", on_click=navigate, args=("endorsements",))
    with nav4:
        st.button("ANALYTICS", on_click=navigate, args=("analytics",))
    with nav5:
        st.button("CAREER / SEASONS ➔", on_click=navigate, args=("career",))
    with nav6:
        st.button("PLAYER BIO ➔", on_click=navigate, args=("bio",))
    with nav7:
        st.button("TENDENCIES ➔", on_click=navigate, args=("tendencies",))

# ==========================================
# PAGE 2: ATTRIBUTES
# ==========================================
elif st.session_state.page == "attributes":
    attr_df = db.fetch_df("SELECT * FROM player_attributes WHERE player_id = ?", (st.session_state.current_player_id,))
    categories = attr_df['category'].unique()
    raw_profile = db.fetch_df("SELECT position, overall_rating, archetype FROM player_profile WHERE id = ?",
                              (st.session_state.current_player_id,)).iloc[0]
    archetype_key = get_archetype_key(raw_profile)


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
            discount = db.get_attribute_discount(archetype_key, row['category'], attr_name)
            cost = calculate_upgrade_cost(curr_lvl, target_lvl, row['cost_multiplier'] * discount)
            pending_cost += cost
            upgrades_to_commit[attr_name] = target_lvl
            simulated_attrs[attr_name] = target_lvl
        else:
            simulated_attrs[attr_name] = curr_lvl

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
            crossed_thresholds = [threshold for threshold in [80, 90, 99] if current_ovr < threshold <= projected_ovr]
            if crossed_thresholds:
                threshold = crossed_thresholds[-1]
                st.session_state.celebration = {
                    "message": f"Major OVR milestone reached: {threshold} OVR!",
                    "effect": "snow" if threshold == 99 else "balloons",
                    "icon": "🔥"
                }
            elif projected_ovr > current_ovr:
                st.session_state.celebration = {
                    "message": f"OVR increased to {projected_ovr}!",
                    "effect": "balloons",
                    "icon": "🔥"
                }
            st.rerun()
    with c2:
        if st.button("❌ RESET CART", disabled=(pending_cost == 0), use_container_width=True):
            st.session_state.attr_cart = {}
            st.rerun()

    st.markdown("---")
    st.subheader("🧠 Build Planner")

    with st.expander("Plan Cheapest Path to Target OVR", expanded=False):
        target_ovr = st.number_input("Target OVR", min_value=current_ovr, max_value=99, value=min(99, current_ovr + 1))

        position_weights = db.OVR_WEIGHTS.get(raw_profile["position"], {})
        sorted_impact_attrs = sorted(
            [(attr, weight) for attr, weight in position_weights.items()],
            key=lambda item: item[1],
            reverse=True
        )

        st.caption("Highest OVR-impact attributes for your position:")
        st.write(", ".join([f"{attr} ({weight})" for attr, weight in sorted_impact_attrs[:8]]))

        if st.button("CALCULATE CHEAPEST PATH", use_container_width=True):
            planner_attrs = {row["attribute_name"]: int(row["current_level"]) for _, row in attr_df.iterrows()}
            planner_steps = []
            planner_cost = 0
            planner_savings = 0

            safety = 0
            while db.calculate_ovr(raw_profile["position"], planner_attrs) < target_ovr and safety < 500:
                safety += 1
                best_option = None

                for _, row in attr_df.iterrows():
                    attr_name = row["attribute_name"]
                    current_level = planner_attrs[attr_name]
                    if current_level >= int(row["max_level"]):
                        continue

                    old_ovr = db.calculate_ovr(raw_profile["position"], planner_attrs)
                    test_attrs = planner_attrs.copy()
                    test_attrs[attr_name] += 1
                    new_ovr = db.calculate_ovr(raw_profile["position"], test_attrs)

                    discount = db.get_attribute_discount(archetype_key, row["category"], attr_name)
                    discounted_cost = calculate_upgrade_cost(current_level, current_level + 1, row["cost_multiplier"] * discount)
                    normal_cost = calculate_upgrade_cost(current_level, current_level + 1, row["cost_multiplier"])

                    ovr_gain = max(0.01, new_ovr - old_ovr)
                    efficiency = discounted_cost / ovr_gain

                    option = {
                        "attr": attr_name,
                        "cost": discounted_cost,
                        "normal_cost": normal_cost,
                        "new_level": current_level + 1,
                        "efficiency": efficiency,
                    }

                    if best_option is None or option["efficiency"] < best_option["efficiency"]:
                        best_option = option

                if best_option is None:
                    break

                planner_attrs[best_option["attr"]] = best_option["new_level"]
                planner_steps.append(best_option)
                planner_cost += best_option["cost"]
                planner_savings += best_option["normal_cost"] - best_option["cost"]

            final_planned_ovr = db.calculate_ovr(raw_profile["position"], planner_attrs)

            if final_planned_ovr >= target_ovr:
                st.success(f"Cheapest projected path to {target_ovr} OVR: {planner_cost:,} XP")
                st.caption(f"Archetype discount savings: {int(planner_savings):,} XP")

                grouped = {}
                for step in planner_steps:
                    grouped.setdefault(step["attr"], 0)
                    grouped[step["attr"]] += 1

                for attr, amount in grouped.items():
                    st.write(f"+{amount} {attr}")
            else:
                st.warning("Could not find a path to that OVR with current caps.")

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
                    discount = db.get_attribute_discount(archetype_key, row['category'], attr_name)
                    next_click_cost = calculate_upgrade_cost(virtual_lvl, virtual_lvl + 1,
                                                             row['cost_multiplier'] * discount)
                    can_afford = remaining_xp >= next_click_cost
                    discount_tag = " (20% off)" if discount < 1 else ""
                    prefix = "🛒" if virtual_lvl > curr_lvl else "➕"
                    if st.button(f"{prefix} {attr_name}: {virtual_lvl}  •  {next_click_cost} XP{discount_tag}",
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
            legend_unlocks = [
                badge_name for badge_name, target_lvl in upgrades_to_commit.items()
                if target_lvl >= 5 and int(badges_df[badges_df['badge_name'] == badge_name].iloc[0]['level']) < 5
            ]
            db.commit_batch_badge_upgrades(st.session_state.current_player_id, upgrades_to_commit, pending_cost)
            st.session_state.badge_cart = {}
            st.toast("Badges upgraded successfully!", icon="🔥")
            if legend_unlocks:
                st.session_state.celebration = {
                    "message": f"Legend badge unlocked: {legend_unlocks[0]}!",
                    "effect": "snow",
                    "icon": "🔥"
                }
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
# PAGE 4: BOX SCORE & ANALYTICS
# ==========================================
elif st.session_state.page == "analytics":
    header_html, profile = get_header()
    curr_season = int(profile['current_season'])

    st.button("â¬… BACK TO SEASON", on_click=navigate, args=("overview",))
    st.markdown(f"<h1 style='color: #ff7b00; display: inline;'>BOX SCORE & ANALYTICS</h1> <br> {header_html}",
                unsafe_allow_html=True)

    games_df = db.fetch_df("SELECT * FROM games WHERE player_id = ? ORDER BY season_number ASC, id ASC",
                           (st.session_state.current_player_id,))
    games_df = prepare_games_df(games_df)

    if games_df.empty:
        st.info("No games logged yet. Submit a game to unlock analytics.")
    else:
        st.subheader("Career Highs")
        st.markdown("---")
        st.subheader("Advanced Analytics")

        total_pts = games_df["pts"].sum()
        total_fgm = games_df["fgm_adj"].sum()
        total_fga = games_df["fga_adj"].sum()
        total_tpm = games_df["tpm"].sum()
        total_tpa = games_df["tpa_adj"].sum()
        total_ftm = games_df["ftm"].sum()
        total_fta = games_df["fta"].sum()
        total_ast = games_df["ast"].sum()
        total_to = games_df["to_val"].sum()
        total_xp = games_df["xp_earned"].sum()

        fg_pct = (total_fgm / total_fga * 100) if total_fga else 0
        tp_pct = (total_tpm / total_tpa * 100) if total_tpa else 0
        ft_pct = (total_ftm / total_fta * 100) if total_fta else 0
        ts_pct = (total_pts / (2 * (total_fga + 0.44 * total_fta)) * 100) if (total_fga + 0.44 * total_fta) else 0
        points_per_shot = total_pts / total_fga if total_fga else 0
        ast_to = total_ast / total_to if total_to else total_ast
        win_pct = games_df["win"].mean() * 100
        avg_xp = total_xp / len(games_df)

        a1, a2, a3, a4, a5, a6 = st.columns(6)
        a1.metric("FG%", f"{fg_pct:.1f}%")
        a2.metric("3P%", f"{tp_pct:.1f}%")
        a3.metric("FT%", f"{ft_pct:.1f}%")
        a4.metric("TS%", f"{ts_pct:.1f}%")
        a5.metric("PTS / Shot", f"{points_per_shot:.2f}")
        a6.metric("AST/TO", f"{ast_to:.2f}")

        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Win %", f"{win_pct:.1f}%")
        b2.metric("Avg XP/Game", f"{avg_xp:,.0f}")
        b3.metric("Career Games", len(games_df))
        b4.metric("Career Points", int(total_pts))

        st.markdown("### Form Indicators")
        last5 = games_df.tail(5)
        last10 = games_df.tail(10)

        f1, f2 = st.columns(2)
        with f1:
            if not last5.empty:
                st.success(
                    f"Last 5: {last5['pts'].mean():.1f} PPG | {last5['ast'].mean():.1f} APG | "
                    f"{(last5['fgm_adj'].sum() / last5['fga_adj'].sum() * 100) if last5['fga_adj'].sum() else 0:.1f} FG% | "
                    f"{int(last5['win'].sum())}-{len(last5) - int(last5['win'].sum())} Record"
                )
        with f2:
            if not last10.empty:
                st.info(
                    f"Last 10: {last10['pts'].mean():.1f} PPG | {last10['ast'].mean():.1f} APG | "
                    f"{int(last10['win'].sum())}-{len(last10) - int(last10['win'].sum())} Record"
                )
        high_cols = st.columns(6)
        highs = [
            ("PTS", "pts"),
            ("REB", "reb"),
            ("AST", "ast"),
            ("STL", "stl"),
            ("BLK", "blk"),
            ("3PM", "tpm"),
        ]
        for col, (label, field) in zip(high_cols, highs):
            best_row = games_df.loc[games_df[field].idxmax()]
            col.markdown(
                f"<div class='metric-label'>{label}</div><div class='metric-value'>{int(best_row[field])}</div><div style='font-size: 12px; color: #888;'>Season {int(best_row['season_number'])}</div>",
                unsafe_allow_html=True)

        st.markdown("---")
        st.subheader(f"Season {curr_season} Progression")
        season_games = games_df[games_df['season_number'] == curr_season].copy()
        if season_games.empty:
            st.info("No games logged in the current season yet.")
        else:
            chart_df = season_games[['game_no', 'pts', 'reb', 'ast', 'stl', 'blk']].set_index('game_no')
            st.line_chart(chart_df)

        st.markdown("---")
        st.subheader("Full Game Log")
        log_df = games_df.copy()
        log_df['W/L'] = log_df['win'].apply(lambda value: "W" if value else "L")
        display_df = log_df[['season_number', 'game_no', 'W/L', 'pts', 'reb', 'ast', 'stl', 'blk', 'tpm',
                             'fga_adj', 'xp_earned']].rename(columns={
            'season_number': 'Season',
            'game_no': 'Game',
            'pts': 'PTS',
            'reb': 'REB',
            'ast': 'AST',
            'stl': 'STL',
            'blk': 'BLK',
            'tpm': '3PM',
            'fga_adj': 'FGA',
            'xp_earned': 'XP'
        })
        page_size = 10
        total_pages = max(1, (len(display_df) + page_size - 1) // page_size)
        page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
        start = (int(page_num) - 1) * page_size
        st.dataframe(display_df.iloc[start:start + page_size], use_container_width=True, hide_index=True)

# ==========================================
# PAGE 5: ENDORSEMENTS
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
    all_games_df = db.fetch_df(
        "SELECT * FROM games WHERE player_id = ?",
        (st.session_state.current_player_id,)
    )
    all_games_df = prepare_games_df(all_games_df)

    all_seasons_df = db.fetch_df(
        "SELECT awards_json FROM season_records WHERE player_id = ?",
        (st.session_state.current_player_id,)
    )

    all_awards = []
    if not all_seasons_df.empty:
        for _, award_row in all_seasons_df.iterrows():
            if award_row["awards_json"]:
                all_awards.extend(json.loads(award_row["awards_json"]))

    career_points = int(all_games_df["pts"].sum()) if not all_games_df.empty else 0
    career_rebounds = int(all_games_df["reb"].sum()) if not all_games_df.empty else 0
    career_assists = int(all_games_df["ast"].sum()) if not all_games_df.empty else 0

    legacy_score = (
        career_points
        + career_rebounds * 1.2
        + career_assists * 1.5
        + all_awards.count("NBA Champion") * 10000
        + all_awards.count("MVP") * 5000
        + all_awards.count("Finals MVP") * 4000
        + all_awards.count("DPOY") * 3000
        + all_awards.count("All-NBA 1st Team") * 2000
        + all_awards.count("All-Defensive Team") * 1500
    )

    if legacy_score < 5000:
        legacy_rank = "G-League Prospect"
        goat_target = 5000
    elif legacy_score < 15000:
        legacy_rank = "Rising Star"
        goat_target = 15000
    elif legacy_score < 35000:
        legacy_rank = "All-Star"
        goat_target = 35000
    elif legacy_score < 75000:
        legacy_rank = "Hall of Famer"
        goat_target = 75000
    else:
        legacy_rank = "The GOAT"
        goat_target = max(legacy_score, 100000)

    progress_value = min(1.0, legacy_score / goat_target)

    st.subheader("🐐 G.O.A.T. Meter")
    st.markdown(f"**Legacy Rank:** {legacy_rank}  \n**Legacy Score:** {int(legacy_score):,}")
    st.progress(progress_value)

    st.subheader("🏆 Trophy Cabinet")
    trophy_counts = {
        "🏆": all_awards.count("NBA Champion"),
        "🏅": all_awards.count("MVP"),
        "💎": all_awards.count("Finals MVP"),
        "🛡️": all_awards.count("DPOY"),
        "⭐": all_awards.count("All-NBA 1st Team"),
        "🔒": all_awards.count("All-Defensive Team"),
        "🎯": all_awards.count("3PT Contest Winner"),
        "🚀": all_awards.count("Dunk Contest Winner"),
    }

    cabinet_html = ""
    for emoji, count in trophy_counts.items():
        if count > 0:
            cabinet_html += f"<span style='font-size:42px; margin-right:10px;' title='x{count}'>{emoji}</span><span style='color:#aaa; margin-right:18px;'>x{count}</span>"

    if cabinet_html:
        st.markdown(f"<div style='background:#222; padding:18px; border-radius:8px;'>{cabinet_html}</div>", unsafe_allow_html=True)
    else:
        st.info("No trophies yet. Build the legacy.")

    st.button("⬅ BACK TO SEASON", on_click=navigate, args=("overview",))
    st.markdown(f"<h1 style='color: #ff7b00; display: inline;'>CAREER & AWARDS</h1> <br> {header_html}",
                unsafe_allow_html=True)

    st.subheader("Team History Timeline")

    with st.expander("➕ Add Team History Entry"):
        with st.form("team_history_form"):
            th_season = st.number_input("Season Number", 1, 50, curr_season)
            th_team = st.text_input("Team Name")
            th_role = st.text_input("Role / Story", placeholder="Drafted by Trail Blazers, Signed with Bulls, Won MVP with Bulls")
            th_contract = st.number_input("Contract Years", 1, 10, 1)
            th_salary = st.number_input("Salary", 0, 100000000, 0)

            if st.form_submit_button("ADD TEAM HISTORY"):
                if th_team:
                    db.add_team_history(st.session_state.current_player_id, int(th_season), th_team, th_role, int(th_contract), int(th_salary))
                    st.success("Team history added.")
                    st.rerun()
                else:
                    st.error("Team name is required.")

    team_df = db.fetch_df(
        "SELECT * FROM team_history WHERE player_id = ? ORDER BY season_number ASC",
        (st.session_state.current_player_id,)
    )

    if team_df.empty:
        st.info("No team history yet.")
    else:
        for _, row in team_df.iterrows():
            st.markdown(f"""
                <div style='background:#222; border-left:4px solid #ff7b00; padding:12px; border-radius:6px; margin-bottom:8px;'>
                    <b style='color:#ff7b00;'>Season {int(row['season_number'])}</b> — 
                    <span style='color:#fff;'>{row['team_name']}</span>
                    <div style='color:#aaa; font-size:13px;'>{row['role']} • {int(row['contract_years'])} yr(s) • ${int(row['salary']):,}</div>
                </div>
            """, unsafe_allow_html=True)

    st.subheader("Historical Seasons")
    seasons_df = db.fetch_df(
        "SELECT season_number, games_played, wins, losses, ppg, rpg, apg, spg, bpg, awards_json FROM season_records WHERE player_id = ? ORDER BY season_number ASC",
        (st.session_state.current_player_id,))

    if not seasons_df.empty:
        for _, row in seasons_df.iterrows():
            awards_list = json.loads(row['awards_json']) if row['awards_json'] and row['awards_json'] != "[]" else []
            awards_str = " &nbsp;|&nbsp; ".join([f"🏆 {a}" for a in awards_list]) if awards_list else "No Major Awards"

            stat_html = "".join([
                f"<div style='text-align: center;'><div style='font-size: 12px; color: #888888; text-transform: uppercase;'>{label}</div><div style='font-size: 24px; font-weight: bold; color: #ffffff;'>{value:.1f}</div></div>"
                for label, value in [
                    ("PPG", float(row['ppg'])),
                    ("RPG", float(row['rpg'])),
                    ("APG", float(row['apg'])),
                    ("SPG", float(row['spg'])),
                    ("BPG", float(row['bpg'])),
                ]
            ])
            season_card_html = "".join([
                "<div style='background-color: #1e1e1e; border: 1px solid #333333; border-radius: 6px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);'>",
                "<div style='display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 15px;'>",
                f"<span style='font-size: 20px; font-weight: bold; color: #ff7b00;'>SEASON {int(row['season_number'])}</span>",
                f"<span style='font-size: 16px; color: #aaaaaa; padding-top: 3px;'>{int(row['games_played'])} GP &nbsp;|&nbsp; <span style='color:#00ff00; font-weight: bold;'>{int(row['wins'])}W</span> - <span style='color:#ff4b4b; font-weight: bold;'>{int(row['losses'])}L</span></span>",
                "</div>",
                f"<div style='display: flex; justify-content: space-around; margin-bottom: 15px;'>{stat_html}</div>",
                f"<div style='font-size: 14px; color: #ffd700; font-weight: bold; background-color: #2a2a2a; padding: 10px; border-radius: 4px; text-align: center;'>{awards_str}</div>",
                "</div>",
            ])
            st.markdown(season_card_html, unsafe_allow_html=True)
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
                a1, a2, a3 = st.columns(3)

                with a1:
                    aw_champ = st.checkbox("NBA Champion (50,000 XP)")
                    aw_fmvp = st.checkbox("Finals MVP (25,000 XP)")
                    aw_mvp = st.checkbox("League MVP (25,000 XP)")
                    aw_mip = st.checkbox("Most Improved Player (12,000 XP)")

                with a2:
                    aw_dpoy = st.checkbox("Defensive Player of the Year (15,000 XP)")
                    aw_clutch = st.checkbox("Clutch Player of the Year (10,000 XP)")
                    aw_sixth = st.checkbox("Sixth Man of the Year (10,000 XP)")
                    aw_allnba = st.checkbox("All-NBA First Team (10,000 XP)")
                    aw_alldef = st.checkbox("All-Defensive Team (8,000 XP)")

                with a3:
                    if curr_season == 1:
                        aw_roy = st.checkbox("Rookie of the Year (15,000 XP)")
                        aw_allrookie = st.checkbox("All-Rookie Team (7,500 XP)")
                    else:
                        aw_roy = False
                        aw_allrookie = False
                        st.caption("Rookie awards are only available in Season 1.")

                    aw_dunk = st.checkbox("Dunk Contest Winner (5,000 XP)")
                    aw_threept = st.checkbox("3PT Contest Winner (5,000 XP)")

                if st.form_submit_button("LOCK IN AWARDS & START NEW SEASON"):
                    aw_payout = 0
                    aw_list = []

                    if aw_champ: aw_payout += 50000; aw_list.append("NBA Champion")
                    if aw_fmvp: aw_payout += 25000; aw_list.append("Finals MVP")
                    if aw_mvp: aw_payout += 25000; aw_list.append("MVP")
                    if aw_mip: aw_payout += 12000; aw_list.append("Most Improved Player")
                    if aw_dpoy: aw_payout += 15000; aw_list.append("DPOY")
                    if aw_clutch: aw_payout += 10000; aw_list.append("Clutch Player of the Year")
                    if aw_sixth: aw_payout += 10000; aw_list.append("Sixth Man of the Year")
                    if aw_allnba: aw_payout += 10000; aw_list.append("All-NBA 1st Team")
                    if aw_alldef: aw_payout += 8000; aw_list.append("All-Defensive Team")
                    if aw_roy: aw_payout += 15000; aw_list.append("ROY")
                    if aw_allrookie: aw_payout += 7500; aw_list.append("All-Rookie Team")
                    if aw_dunk: aw_payout += 5000; aw_list.append("Dunk Contest Winner")
                    if aw_threept: aw_payout += 5000; aw_list.append("3PT Contest Winner")

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
                    season_endorsements = db.fetch_df(
                        "SELECT * FROM endorsements WHERE player_id = ? AND completed = 0",
                        (st.session_state.current_player_id,))
                    for _, endo in season_endorsements.iterrows():
                        if season_award_endorsement_matches(endo['endorsement_name'], aw_list):
                            payout = int(endo['payout'])
                            db.complete_endorsement(st.session_state.current_player_id, endo['endorsement_name'], payout)
                            st.toast(f"{endo['endorsement_name']} (+{payout:,} XP)", icon="🏆")
                    st.toast(f"Season {curr_season} completed! Earned {aw_payout:,} XP.", icon="🏆")
                    st.rerun()

# ==========================================
# PAGE 6: PLAYER BIO
# ==========================================
elif st.session_state.page == "bio":
    header_html, profile = get_header()
    st.button("⬅ BACK TO SEASON", on_click=navigate, args=("overview",))
    st.markdown(f"<h1 style='color: #ff7b00; display: inline;'>PLAYER BIO / CAREER IDENTITY</h1> <br> {header_html}",
                unsafe_allow_html=True)

    with st.form("bio_form"):
        c1, c2, c3 = st.columns(3)

        with c1:
            name = st.text_input("Name", value=str(profile.get("name", "")))
            nickname = st.text_input("Nickname", value=str(profile.get("nickname", "") or ""))
            age = st.number_input("Age", 16, 45, int(profile.get("age", 19) or 19))
            height = st.text_input("Height", value=str(profile.get("height", "") or ""), placeholder="6'7\"")

        with c2:
            position = st.selectbox("Position", ["PG", "SG", "SF", "PF", "C"], index=["PG", "SG", "SF", "PF", "C"].index(profile["position"]))
            jersey = st.number_input("Jersey Number", 0, 99, int(profile["jersey_number"]))
            weight = st.number_input("Weight (lbs)", 150, 400, int(profile["weight"]))
            wingspan = st.number_input("Wingspan (ft)", 5.0, 9.0, float(profile["wingspan"]), format="%.1f")

        with c3:
            handedness = st.selectbox("Handedness", ["Right", "Left"], index=0 if str(profile.get("handedness", "Right")) != "Left" else 1)
            college_country = st.text_input("College/Country", value=str(profile.get("college_country", "") or ""))
            draft_year = st.number_input("Draft Year", 0, 2100, int(profile.get("draft_year", 0) or 0))
            draft_pick = st.text_input("Draft Pick", value=str(profile.get("draft_pick", "") or ""), placeholder="Round 1, Pick 7")
            current_team = st.text_input("Current Team", value=str(profile.get("current_team", "") or ""))
            personality_type = st.selectbox(
                "Personality Type",
                ["Balanced", "Alpha Scorer", "Team-First Leader", "Defensive Anchor", "Flashy Entertainer", "Quiet Superstar"],
                index=0
            )

        if st.form_submit_button("SAVE BIO"):
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE player_profile
                SET name = ?, nickname = ?, age = ?, height = ?, position = ?, jersey_number = ?,
                    weight = ?, wingspan = ?, handedness = ?, college_country = ?, draft_year = ?,
                    draft_pick = ?, current_team = ?, personality_type = ?
                WHERE id = ?
            """, (
                name, nickname, int(age), height, position, int(jersey), int(weight), float(wingspan),
                handedness, college_country, int(draft_year), draft_pick, current_team, personality_type,
                st.session_state.current_player_id
            ))
            conn.commit()
            conn.close()
            st.success("Player bio updated.")
            st.rerun()

# ==========================================
# PAGE 7: TENDENCIES
# ==========================================
elif st.session_state.page == "tendencies":
    header_html, profile = get_header()
    st.button("⬅ BACK TO SEASON", on_click=navigate, args=("overview",))
    st.markdown(f"<h1 style='color: #ff7b00; display: inline;'>TENDENCIES</h1> <br> {header_html}",
                unsafe_allow_html=True)
    st.caption("Attributes affect success. Tendencies affect how often your player attempts actions in simulation/AI contexts.")

    tendencies_df = db.fetch_df(
        "SELECT * FROM tendencies WHERE player_id = ? ORDER BY category, tendency_name",
        (st.session_state.current_player_id,)
    )

    if tendencies_df.empty:
        db.initialize_tendencies(st.session_state.current_player_id, get_archetype_key(profile))
        st.rerun()

    for category in tendencies_df["category"].unique():
        with st.expander(category, expanded=(category in ["Jump Shooting", "Layups and Dunks", "Freelance"])):
            cat_df = tendencies_df[tendencies_df["category"] == category]
            for _, row in cat_df.iterrows():
                new_val = st.slider(row["tendency_name"], 0, 100, int(row["value"]), key=f"tend_{row['tendency_name']}")
                if new_val != int(row["value"]):
                    db.update_tendency(st.session_state.current_player_id, row["tendency_name"], new_val)