import sqlite3
import pandas as pd
import math
import json

DB_NAME = "nba2k_career.db"

# ==========================================
# 2K DYNAMIC OVR ENGINE MATRIX
# ==========================================
OVR_WEIGHTS = {
    'PG': {'Pass Accuracy': 1.0, 'Ball Handle': 1.0, 'Speed With Ball': 0.9, 'Three-Point Shot': 0.9,
           'Perimeter Defense': 0.8, 'Speed': 0.8, 'Driving Layup': 0.7, 'Steal': 0.7, 'Agility': 0.7,
           'Mid-Range Shot': 0.6, 'Pass Vision': 0.8, 'Pass IQ': 0.7, 'Offensive Consistency': 0.6,
           'Defensive Consistency': 0.5, 'Stamina': 0.5},
    'SG': {'Three-Point Shot': 1.0, 'Perimeter Defense': 0.9, 'Mid-Range Shot': 0.8, 'Speed': 0.8, 'Ball Handle': 0.7,
           'Driving Dunk': 0.7, 'Agility': 0.7, 'Steal': 0.6, 'Driving Layup': 0.6, 'Offensive Consistency': 0.7,
           'Defensive Consistency': 0.6, 'Stamina': 0.5, 'Speed With Ball': 0.6},
    'SF': {'Driving Dunk': 0.9, 'Perimeter Defense': 0.9, 'Three-Point Shot': 0.8, 'Speed': 0.8,
           'Interior Defense': 0.7, 'Strength': 0.6, 'Defensive Rebound': 0.6, 'Mid-Range Shot': 0.6, 'Agility': 0.7,
           'Driving Layup': 0.6, 'Defensive Consistency': 0.7, 'Offensive Consistency': 0.6, 'Stamina': 0.5},
    'PF': {'Interior Defense': 1.0, 'Defensive Rebound': 0.9, 'Strength': 0.9, 'Standing Dunk': 0.8, 'Block': 0.8,
           'Offensive Rebound': 0.7, 'Driving Dunk': 0.7, 'Close Shot': 0.7, 'Post Control': 0.6, 'Post Hook': 0.5,
           'Defensive Consistency': 0.8, 'Help Defense IQ': 0.7, 'Stamina': 0.5},
    'C': {'Defensive Rebound': 1.0, 'Interior Defense': 1.0, 'Block': 0.9, 'Strength': 0.9, 'Offensive Rebound': 0.9,
          'Standing Dunk': 0.8, 'Close Shot': 0.8, 'Post Hook': 0.6, 'Post Control': 0.6, 'Defensive Consistency': 0.8,
          'Help Defense IQ': 0.8, 'Stamina': 0.5}
}


def calculate_ovr(position, attributes_dict):
    weights = OVR_WEIGHTS.get(position, {})
    total_weight = 0
    weighted_sum = 0
    for attr, level in attributes_dict.items():
        w = weights.get(attr, 0.1)
        weighted_sum += level * w
        total_weight += w
    if total_weight == 0: return 60
    return math.floor(weighted_sum / total_weight)


# ==========================================
# CORE DATABASE FUNCTIONS
# ==========================================
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Updated: Added season_number
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS games (id INTEGER PRIMARY KEY AUTOINCREMENT, player_id INTEGER, season_number INTEGER DEFAULT 1, fgm INTEGER DEFAULT 0, fga INTEGER DEFAULT 0, tpm INTEGER DEFAULT 0, tpa INTEGER DEFAULT 0, ftm INTEGER DEFAULT 0, fta INTEGER DEFAULT 0, ast INTEGER DEFAULT 0, to_val INTEGER DEFAULT 0, dreb INTEGER DEFAULT 0, oreb INTEGER DEFAULT 0, stl INTEGER DEFAULT 0, fls INTEGER DEFAULT 0, dunks INTEGER DEFAULT 0, blk INTEGER DEFAULT 0, win INTEGER DEFAULT 0, xp_earned INTEGER DEFAULT 0)")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS player_attributes (player_id INTEGER, category TEXT, attribute_name TEXT, current_level INTEGER DEFAULT 60, max_level INTEGER DEFAULT 99, cost_multiplier INTEGER DEFAULT 1, PRIMARY KEY (player_id, attribute_name))")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS badges (player_id INTEGER, category TEXT, badge_name TEXT, level INTEGER DEFAULT 0, PRIMARY KEY (player_id, badge_name))")
    # Updated: Added current_season
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS player_profile (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, position TEXT, jersey_number INTEGER, weight INTEGER, wingspan REAL, total_xp INTEGER DEFAULT 0, overall_rating INTEGER DEFAULT 60, current_season INTEGER DEFAULT 1)")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS endorsements (player_id INTEGER, endorsement_name TEXT, description TEXT, payout INTEGER, completed INTEGER DEFAULT 0, PRIMARY KEY (player_id, endorsement_name))")

    # NEW: Historical Season Records
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS season_records
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       player_id
                       INTEGER,
                       season_number
                       INTEGER,
                       games_played
                       INTEGER,
                       wins
                       INTEGER,
                       losses
                       INTEGER,
                       ppg
                       REAL,
                       apg
                       REAL,
                       rpg
                       REAL,
                       spg
                       REAL,
                       bpg
                       REAL,
                       awards_json
                       TEXT,
                       payout_earned
                       INTEGER
                   )
                   """)
    conn.commit()
    conn.close()


def create_player(name, position, jersey, weight, wingspan):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO player_profile (name, position, jersey_number, weight, wingspan, total_xp, overall_rating, current_season) VALUES (?, ?, ?, ?, ?, 0, 60, 1)",
        (name, position, jersey, weight, wingspan))
    player_id = cursor.lastrowid

    attrs = [
        (player_id, 'Offense', 'Driving Layup', 55, 99, 1), (player_id, 'Offense', 'Post Fade', 40, 99, 2),
        (player_id, 'Offense', 'Post Hook', 40, 99, 2), (player_id, 'Offense', 'Post Control', 40, 99, 1),
        (player_id, 'Offense', 'Draw Foul', 50, 99, 1), (player_id, 'Offense', 'Close Shot', 55, 99, 1),
        (player_id, 'Offense', 'Standing Dunk', 40, 99, 1), (player_id, 'Offense', 'Driving Dunk', 55, 99, 2),
        (player_id, 'Offense', 'Mid-Range Shot', 40, 99, 2), (player_id, 'Offense', 'Three-Point Shot', 25, 99, 3),
        (player_id, 'Offense', 'Free Throw', 60, 99, 1),
        (player_id, 'Playmaking', 'Ball Handle', 45, 99, 2), (player_id, 'Playmaking', 'Pass IQ', 50, 99, 1),
        (player_id, 'Playmaking', 'Pass Accuracy', 50, 99, 2), (player_id, 'Playmaking', 'Shot IQ', 50, 99, 1),
        (player_id, 'Playmaking', 'Pass Vision', 50, 99, 1), (player_id, 'Playmaking', 'Hands', 50, 99, 1),
        (player_id, 'Defense', 'Interior Defense', 45, 99, 2), (player_id, 'Defense', 'Perimeter Defense', 45, 99, 2),
        (player_id, 'Defense', 'Block', 45, 99, 2), (player_id, 'Defense', 'Steal', 45, 99, 2),
        (player_id, 'Rebounding', 'Offensive Rebound', 45, 99, 2),
        (player_id, 'Rebounding', 'Defensive Rebound', 45, 99, 2),
        (player_id, 'Athleticism', 'Speed', 55, 99, 3), (player_id, 'Athleticism', 'Speed With Ball', 55, 99, 2),
        (player_id, 'Athleticism', 'Vertical', 55, 99, 2), (player_id, 'Athleticism', 'Strength', 50, 99, 1),
        (player_id, 'Athleticism', 'Stamina', 65, 99, 1), (player_id, 'Athleticism', 'Hustle', 60, 99, 1),
        (player_id, 'Athleticism', 'Agility', 55, 99, 2), (player_id, 'Mental', 'Pass Perception', 50, 99, 1),
        (player_id, 'Mental', 'Defensive Consistency', 50, 99, 1), (player_id, 'Mental', 'Help Defense IQ', 50, 99, 1),
        (player_id, 'Mental', 'Offensive Consistency', 50, 99, 1)
    ]
    cursor.executemany("INSERT INTO player_attributes VALUES (?, ?, ?, ?, ?, ?)", attrs)

    attr_dict = {a[2]: a[3] for a in attrs}
    starting_ovr = calculate_ovr(position, attr_dict)
    cursor.execute("UPDATE player_profile SET overall_rating = ? WHERE id = ?", (starting_ovr, player_id))

    badges = [
        (player_id, 'Finishing', 'Float Game', 0), (player_id, 'Finishing', 'Posterizer', 0),
        (player_id, 'Finishing', 'Rise Up', 0), (player_id, 'Finishing', 'Aerial Wizard', 0),
        (player_id, 'Finishing', 'Hook Specialist', 0), (player_id, 'Finishing', 'Layup Mixmaster', 0),
        (player_id, 'Finishing', 'Paint Prodigy', 0), (player_id, 'Finishing', 'Physical Finisher', 0),
        (player_id, 'Finishing', 'Post Powerhouse', 0), (player_id, 'Finishing', 'Post-Up Poet', 0),
        (player_id, 'Shooting', 'Post Fade Phenom', 0), (player_id, 'Shooting', 'Deadeye', 0),
        (player_id, 'Shooting', 'Limitless Range', 0), (player_id, 'Shooting', 'Slippery Off-Ball', 0),
        (player_id, 'Shooting', 'Mini Marksman', 0), (player_id, 'Shooting', 'Set Shot Specialist', 0),
        (player_id, 'Shooting', 'Shifty Shooter', 0),
        (player_id, 'Playmaking', 'Bail Out', 0), (player_id, 'Playmaking', 'Break Starter', 0),
        (player_id, 'Playmaking', 'Dimer', 0), (player_id, 'Playmaking', 'Handles for Days', 0),
        (player_id, 'Playmaking', 'Unpluckable', 0), (player_id, 'Playmaking', 'Versatile Visionary', 0),
        (player_id, 'Playmaking', 'Ankle Assassin', 0), (player_id, 'Playmaking', 'Lightning Launch', 0),
        (player_id, 'Playmaking', 'Strong Handle', 0),
        (player_id, 'Defense', 'Post Lockdown', 0), (player_id, 'Defense', 'Challenger', 0),
        (player_id, 'Defense', 'Off-Ball Pest', 0), (player_id, 'Defense', 'Pick Dodger', 0),
        (player_id, 'Defense', 'Glove', 0), (player_id, 'Defense', 'Interceptor', 0),
        (player_id, 'Defense', 'Pogo Stick', 0), (player_id, 'Defense', 'On-Ball Menace', 0),
        (player_id, 'Defense', 'High-Flying Denier', 0), (player_id, 'Defense', 'Paint Patroller', 0),
        (player_id, 'Athleticism', 'Brick Wall', 0), (player_id, 'Athleticism', 'Immovable Enforcer', 0),
        (player_id, 'Rebounding', 'Boxout Beast', 0), (player_id, 'Rebounding', 'Rebound Chaser', 0)
    ]
    cursor.executemany("INSERT INTO badges VALUES (?, ?, ?, ?)", badges)

    endorsements = [
        (player_id, 'Shoe Deal: The 40-Bomb', 'Score 40+ points in a single game.', 10000, 0),
        (player_id, 'National TV: 50-Point Game', 'Score 50+ points in a single game.', 25000, 0),
        (player_id, 'Energy Drink: Triple Double', 'Record double digits in 3 stat categories.', 15000, 0),
        (player_id, 'Cereal Box: Rainmaker', 'Make 10+ Three-Pointers in a single game.', 10000, 0),
        (player_id, 'Apparel Sponsor: Defensive Menace', 'Record 5+ Steals and 5+ Blocks in a single game.', 12000, 0),
        (player_id, 'State Farm: The Playmaker', 'Record 20+ Assists in a single game.', 15000, 0),
        (player_id, 'Gatorade: Board Man Gets Paid', 'Grab 25+ Rebounds in a single game.', 15000, 0),
        (player_id, 'Local Hero: 10 Games Played', 'Complete 10 career games.', 5000, 0)
    ]
    cursor.executemany("INSERT INTO endorsements VALUES (?, ?, ?, ?, ?)", endorsements)

    conn.commit()
    conn.close()
    return player_id


def delete_player(player_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM player_profile WHERE id = ?", (player_id,))
    cursor.execute("DELETE FROM player_attributes WHERE player_id = ?", (player_id,))
    cursor.execute("DELETE FROM badges WHERE player_id = ?", (player_id,))
    cursor.execute("DELETE FROM games WHERE player_id = ?", (player_id,))
    cursor.execute("DELETE FROM endorsements WHERE player_id = ?", (player_id,))
    cursor.execute("DELETE FROM season_records WHERE player_id = ?", (player_id,))
    conn.commit()
    conn.close()


def insert_game(player_id, season_number, stats, xp_earned):
    conn = get_connection()
    cursor = conn.cursor()
    cols = ', '.join(stats.keys())
    placeholders = ', '.join('?' * len(stats))
    query = f"INSERT INTO games (player_id, season_number, {cols}, xp_earned) VALUES (?, ?, {placeholders}, ?)"
    cursor.execute(query, (player_id, season_number, *stats.values(), xp_earned))
    cursor.execute("UPDATE player_profile SET total_xp = total_xp + ? WHERE id = ?", (xp_earned, player_id))
    conn.commit()
    conn.close()


def complete_endorsement(player_id, name, payout):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE endorsements SET completed = 1 WHERE player_id = ? AND endorsement_name = ?",
                   (player_id, name))
    cursor.execute("UPDATE player_profile SET total_xp = total_xp + ? WHERE id = ?", (payout, player_id))
    conn.commit()
    conn.close()


def fetch_df(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def commit_batch_attribute_upgrades(player_id, upgrades_dict, total_cost, new_ovr):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for attr_name, new_level in upgrades_dict.items():
            cursor.execute("UPDATE player_attributes SET current_level = ? WHERE attribute_name = ? AND player_id = ?",
                           (int(new_level), attr_name, player_id))
        cursor.execute("UPDATE player_profile SET total_xp = total_xp - ?, overall_rating = ? WHERE id = ?",
                       (total_cost, new_ovr, player_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def commit_batch_badge_upgrades(player_id, badge_upgrades_dict, total_cost):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for badge_name, new_level in badge_upgrades_dict.items():
            cursor.execute("UPDATE badges SET level = ? WHERE badge_name = ? AND player_id = ?",
                           (int(new_level), badge_name, player_id))
        cursor.execute("UPDATE player_profile SET total_xp = total_xp - ? WHERE id = ?", (total_cost, player_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def process_season_end(player_id, current_season, stats_summary, awards_won, xp_payout):
    """Logs the historical season, pays out awards, and advances to the next season."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        awards_json = json.dumps(awards_won)

        # Log the historical record
        cursor.execute("""
                       INSERT INTO season_records (player_id, season_number, games_played, wins, losses, ppg, apg, rpg,
                                                   spg, bpg, awards_json, payout_earned)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       """,
                       (player_id, current_season, stats_summary['gp'], stats_summary['wins'], stats_summary['losses'],
                        stats_summary['ppg'], stats_summary['apg'], stats_summary['rpg'], stats_summary['spg'],
                        stats_summary['bpg'],
                        awards_json, xp_payout))

        # Payout XP and increment the current season
        cursor.execute(
            "UPDATE player_profile SET total_xp = total_xp + ?, current_season = current_season + 1 WHERE id = ?",
            (xp_payout, player_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()