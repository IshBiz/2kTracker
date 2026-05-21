import sqlite3
import pandas as pd

DB_NAME = "nba2k_career.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Games Table (Added player_id)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS games
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       player_id
                       INTEGER,
                       fgm
                       INTEGER
                       DEFAULT
                       0,
                       fga
                       INTEGER
                       DEFAULT
                       0,
                       tpm
                       INTEGER
                       DEFAULT
                       0,
                       tpa
                       INTEGER
                       DEFAULT
                       0,
                       ftm
                       INTEGER
                       DEFAULT
                       0,
                       fta
                       INTEGER
                       DEFAULT
                       0,
                       ast
                       INTEGER
                       DEFAULT
                       0,
                       to_val
                       INTEGER
                       DEFAULT
                       0,
                       dreb
                       INTEGER
                       DEFAULT
                       0,
                       oreb
                       INTEGER
                       DEFAULT
                       0,
                       stl
                       INTEGER
                       DEFAULT
                       0,
                       fls
                       INTEGER
                       DEFAULT
                       0,
                       dunks
                       INTEGER
                       DEFAULT
                       0,
                       blk
                       INTEGER
                       DEFAULT
                       0,
                       win
                       INTEGER
                       DEFAULT
                       0,
                       xp_earned
                       INTEGER
                       DEFAULT
                       0
                   )
                   """)

    # Attributes Table (Added player_id)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS player_attributes
                   (
                       player_id
                       INTEGER,
                       category
                       TEXT,
                       attribute_name
                       TEXT,
                       current_level
                       INTEGER
                       DEFAULT
                       60,
                       max_level
                       INTEGER
                       DEFAULT
                       99,
                       cost_multiplier
                       INTEGER
                       DEFAULT
                       1,
                       PRIMARY
                       KEY
                   (
                       player_id,
                       attribute_name
                   )
                       )
                   """)

    # Badges Table (Added player_id)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS badges
                   (
                       player_id
                       INTEGER,
                       badge_name
                       TEXT,
                       tier
                       TEXT
                       DEFAULT
                       'Bronze',
                       cost
                       INTEGER
                       DEFAULT
                       2000,
                       unlocked
                       INTEGER
                       DEFAULT
                       0,
                       PRIMARY
                       KEY
                   (
                       player_id,
                       badge_name
                   )
                       )
                   """)

    # Player Profile (Expanded with custom stats)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS player_profile
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT,
                       position
                       TEXT,
                       jersey_number
                       INTEGER,
                       weight
                       INTEGER,
                       wingspan
                       INTEGER,
                       total_xp
                       INTEGER
                       DEFAULT
                       0,
                       overall_rating
                       INTEGER
                       DEFAULT
                       60
                   )
                   """)

    conn.commit()
    conn.close()


def create_player(name, position, jersey, weight, wingspan):
    """Creates a new player profile and seeds their initial attributes and badges."""
    conn = get_connection()
    cursor = conn.cursor()

    # Insert new profile
    cursor.execute("""
                   INSERT INTO player_profile (name, position, jersey_number, weight, wingspan, total_xp)
                   VALUES (?, ?, ?, ?, ?, 0)
                   """, (name, position, jersey, weight, wingspan))

    player_id = cursor.lastrowid

    # Seed base attributes
    attrs = [
        (player_id, 'Outside Scoring', 'Shot 3pt', 25, 99, 2), (player_id, 'Outside Scoring', 'Shot Mid', 25, 99, 2),
        (player_id, 'Inside Scoring', 'Driving Layup', 60, 99, 1),
        (player_id, 'Inside Scoring', 'Driving Dunk', 65, 99, 2),
        (player_id, 'Defending', 'Interior Defense', 80, 99, 3),
        (player_id, 'Defending', 'Perimeter Defense', 50, 99, 2),
        (player_id, 'Athleticism', 'Speed', 55, 99, 1), (player_id, 'Athleticism', 'Vertical', 70, 99, 1),
        (player_id, 'Playmaking', 'Speed With Ball', 45, 99, 2), (player_id, 'Playmaking', 'Ball Handling', 40, 99, 2),
        (player_id, 'Rebounding', 'Offensive Rebound', 90, 99, 3),
        (player_id, 'Rebounding', 'Defensive Rebound', 75, 99, 3)
    ]
    cursor.executemany("INSERT INTO player_attributes VALUES (?, ?, ?, ?, ?, ?)", attrs)

    # Seed base badges
    badges = [
        (player_id, 'Immovable Enforcer', 'Bronze', 5000, 0),
        (player_id, 'Brick Wall', 'Bronze', 5000, 0),
        (player_id, 'Rise Up', 'Bronze', 2000, 0)
    ]
    cursor.executemany("INSERT INTO badges VALUES (?, ?, ?, ?, ?)", badges)

    conn.commit()
    conn.close()
    return player_id


def insert_game(player_id, stats, xp_earned):
    conn = get_connection()
    cursor = conn.cursor()
    cols = ', '.join(stats.keys())
    placeholders = ', '.join('?' * len(stats))
    query = f"INSERT INTO games (player_id, {cols}, xp_earned) VALUES (?, {placeholders}, ?)"
    cursor.execute(query, (player_id, *stats.values(), xp_earned))
    cursor.execute("UPDATE player_profile SET total_xp = total_xp + ? WHERE id = ?", (xp_earned, player_id))
    conn.commit()
    conn.close()


def fetch_df(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def commit_attribute_upgrade(player_id, attribute_name, new_level, cost):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE player_attributes SET current_level = ? WHERE attribute_name = ? AND player_id = ?",
                       (int(new_level), attribute_name, player_id))
        cursor.execute("UPDATE player_profile SET total_xp = total_xp - ? WHERE id = ?", (cost, player_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def commit_badge_update(player_id, badge_name, unlocked_state, cost):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE badges SET unlocked = ? WHERE badge_name = ? AND player_id = ?",
                       (unlocked_state, badge_name, player_id))
        if unlocked_state == 1:
            cursor.execute("UPDATE player_profile SET total_xp = total_xp - ? WHERE id = ?", (cost, player_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()