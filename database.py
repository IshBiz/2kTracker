import sqlite3
import pandas as pd
import math
import json

DB_NAME = "nba2k_career.db"

GLOBAL_ENDORSEMENTS = [
    ('Shoe Deal: The 40-Bomb', 'Score 40+ points in a single game.', 10000, 0),
    ('National TV: 50-Point Game', 'Score 50+ points in a single game.', 25000, 0),
    ('Energy Drink: Triple Double', 'Record double digits in 3 stat categories.', 15000, 0),
    ('Cereal Box: Rainmaker', 'Make 10+ Three-Pointers in a single game.', 10000, 0),
    ('Apparel Sponsor: Defensive Menace', 'Record 5+ Steals and 5+ Blocks in a single game.', 12000, 0),
    ('State Farm: The Playmaker', 'Record 20+ Assists in a single game.', 15000, 0),
    ('Gatorade: Board Man Gets Paid', 'Grab 25+ Rebounds in a single game.', 15000, 0),
    ('Local Hero: 10 Games Played', 'Complete 10 career games.', 5000, 0)
]

ARCHETYPES = {
    "balanced_star": {
        "name": "Balanced Star",
        "takeover": "Custom Takeover",
        "description": "No discount, but no weakness. A flexible build for all-around careers.",
        "discount_categories": [],
        "discount_attributes": [],
        "xp_bonus": "Standard XP rules.",
        "endorsements": []
    },
    "sharpshooter": {
        "name": "Sharpshooter",
        "takeover": "Shooting Takeover",
        "description": "Elite spacing and deep-range scoring.",
        "discount_categories": [],
        "discount_attributes": ["Three-Point Shot", "Mid-Range Shot", "Free Throw", "Post Fade", "Shot IQ",
                                "Offensive Consistency"],
        "xp_bonus": "Double XP impact for made threes.",
        "endorsements": [
            ('Foot Locker: Sniper Night', 'Make 12+ Three-Pointers in a single game.', 18000, 0),
            ('Splash Brothers Feature', 'Score 35+ points with 8+ made threes.', 20000, 0),
            ('Three-Point Crown Campaign', 'Win MVP as a Sharpshooter.', 30000, 0)
        ]
    },
    "lockdown_defender": {
        "name": "Lockdown Defender",
        "takeover": "Defense Takeover",
        "description": "Point-of-attack pressure, steals, blocks, and award-season defense.",
        "discount_categories": ["Defense"],
        "discount_attributes": ["Defensive Consistency", "Help Defense IQ", "Pass Perception"],
        "xp_bonus": "Double XP impact for steals and blocks.",
        "endorsements": [
            ('Jordan Brand: Clamp Session', 'Record 7+ steals in a single game.', 16000, 0),
            ('NBA Cares: No Fly Zone', 'Record 6+ blocks in a single game.', 16000, 0),
            ('Kia Defensive Legacy', 'Win Defensive Player of the Year.', 30000, 0)
        ]
    },
    "slashing_playmaker": {
        "name": "Slashing Playmaker",
        "takeover": "Finishing / Playmaking Takeover",
        "description": "Rim pressure with enough passing to punish every collapse.",
        "discount_categories": ["Playmaking"],
        "discount_attributes": ["Driving Layup", "Driving Dunk", "Draw Foul", "Speed With Ball"],
        "xp_bonus": "Bonus XP for assists and dunks.",
        "endorsements": [
            ('Sprite: Highlight Factory', 'Record 5+ dunks and 10+ assists in a single game.', 18000, 0),
            ('And1: Rim Pressure', 'Attempt 12+ free throws in a single game.', 14000, 0),
            ('Floor General Spotlight', 'Make All-NBA First Team as a Slashing Playmaker.', 22000, 0)
        ]
    },
    "playmaking_shot_creator": {
        "name": "Playmaking Shot Creator",
        "takeover": "Shot Creator / Playmaking Takeover",
        "description": "Self-created jumpers, handle packages, and table-setting offense.",
        "discount_categories": ["Playmaking"],
        "discount_attributes": ["Mid-Range Shot", "Three-Point Shot", "Ball Handle", "Speed With Ball"],
        "xp_bonus": "Bonus XP for assists and made shots.",
        "endorsements": [
            ('Tissot: Shot Clock Killer', 'Score 30+ points with 10+ assists in a single game.', 22000, 0),
            ('Ankle Tape Sponsor', 'Record 20+ assists in a single game.', 15000, 0),
            ('MVP Campaign: Creator Edition', 'Win MVP as a Playmaking Shot Creator.', 30000, 0)
        ]
    },
    "two_way_finisher": {
        "name": "Two-Way Finisher",
        "takeover": "Finishing / Defense Takeover",
        "description": "Contact finishes on one end and disruptive stops on the other.",
        "discount_categories": ["Defense"],
        "discount_attributes": ["Driving Layup", "Driving Dunk", "Standing Dunk", "Vertical", "Strength"],
        "xp_bonus": "Bonus XP for dunks, steals, and blocks.",
        "endorsements": [
            ('Above The Rim Mixtape', 'Record 8+ dunks in a single game.', 16000, 0),
            ('Two-Way Takeover Feature', 'Score 25+ points with 3+ steals and 3+ blocks.', 22000, 0),
            ('All-NBA Two-Way Bonus', 'Make All-NBA First Team as a Two-Way Finisher.', 22000, 0)
        ]
    },
    "rim_protector": {
        "name": "Rim Protector",
        "takeover": "Defense / Rebounding Takeover",
        "description": "Paint deterrence, block parties, and anchor-level defense.",
        "discount_categories": ["Defense", "Rebounding"],
        "discount_attributes": ["Strength", "Vertical", "Help Defense IQ"],
        "xp_bonus": "Double XP impact for blocks and bonus XP for rebounds.",
        "endorsements": [
            ('Block Party Broadcast', 'Record 8+ blocks in a single game.', 20000, 0),
            ('Paint Patrol Sponsor', 'Record 5+ blocks in a win.', 16000, 0),
            ('Anchor of the Year', 'Win Defensive Player of the Year as a Rim Protector.', 30000, 0)
        ]
    },
    "glass_cleaner": {
        "name": "Glass Cleaner",
        "takeover": "Rebounding Takeover",
        "description": "Board control, extra possessions, and interior dirty work.",
        "discount_categories": ["Rebounding"],
        "discount_attributes": ["Strength", "Vertical", "Hustle", "Boxout Beast", "Rebound Chaser"],
        "xp_bonus": "Double XP impact for rebounds.",
        "endorsements": [
            ('Board Man Elite', 'Grab 30+ rebounds in a single game.', 22000, 0),
            ('Second-Chance Sponsor', 'Grab 10+ offensive rebounds in a single game.', 16000, 0),
            ('Glass Work All-NBA Bonus', 'Make All-NBA First Team as a Glass Cleaner.', 22000, 0)
        ]
    },
    "inside_out_scorer": {
        "name": "Inside-Out Scorer",
        "takeover": "Finishing / Shooting Takeover",
        "description": "Three-level pressure: rim attacks, spot-up threes, and scoring bursts.",
        "discount_categories": [],
        "discount_attributes": ["Driving Layup", "Driving Dunk", "Three-Point Shot", "Mid-Range Shot",
                                "Close Shot", "Free Throw"],
        "xp_bonus": "Bonus XP for made threes and dunks.",
        "endorsements": [
            ('Three-Level Clinic', 'Score 40+ points with 4+ threes and 3+ dunks.', 22000, 0),
            ('Offensive Threat Feature', 'Score 55+ points in a single game.', 26000, 0),
            ('Scoring Champ MVP Push', 'Win MVP as an Inside-Out Scorer.', 30000, 0)
        ]
    }
}


def get_archetype(archetype_key):
    return ARCHETYPES.get(archetype_key or "balanced_star", ARCHETYPES["balanced_star"])


def get_endorsements_for_archetype(archetype_key):
    return GLOBAL_ENDORSEMENTS + get_archetype(archetype_key).get("endorsements", [])


def get_attribute_discount(archetype_key, category, attribute_name):
    archetype = get_archetype(archetype_key)
    if category in archetype["discount_categories"] or attribute_name in archetype["discount_attributes"]:
        return 0.8
    return 1.0


COACH_CHALLENGES = {
    "balanced_star": [
        {"name": "All-Around Impact", "description": "Record 20+ PTS, 5+ REB, and 5+ AST.", "bonus": 2500, "type": "balanced"},
        {"name": "Winning Basketball", "description": "Win the game and score 25+ PTS.", "bonus": 2200, "type": "win_pts"},
        {"name": "Stat Sheet Stuffing", "description": "Record 15+ PTS, 7+ REB, and 7+ AST.", "bonus": 2800, "type": "pts_reb_ast", "pts": 15, "reb": 7, "ast": 7},
        {"name": "Complete Game", "description": "Record 20+ PTS and 3+ stocks.", "bonus": 2600, "type": "pts_stocks", "pts": 20, "stocks": 3},
        {"name": "Winning Engine", "description": "Win the game with 8+ AST.", "bonus": 2400, "type": "ast_win", "ast": 8},
        {"name": "Efficient Star", "description": "Score 25+ PTS on 50%+ FG.", "bonus": 3000, "type": "pts_fg_pct", "pts": 25, "fg_pct": 0.50},
        {"name": "Do-It-All Night", "description": "Record 10+ PTS, 10+ REB, and 10+ AST.", "bonus": 3500, "type": "triple_double"},
        {"name": "No Weaknesses", "description": "Record 18+ PTS, 5+ REB, 5+ AST, and 2+ stocks.", "bonus": 3200, "type": "pts_reb_ast_stocks", "pts": 18, "reb": 5, "ast": 5, "stocks": 2},
    ],

    "sharpshooter": [
        {"name": "Green Light", "description": "Make 6+ threes.", "bonus": 2500, "type": "threes", "target": 6},
        {"name": "Spacing Gravity", "description": "Score 30+ PTS with 4+ threes.", "bonus": 3000, "type": "pts_threes", "pts": 30, "threes": 4},
        {"name": "Flamethrower", "description": "Make 8+ threes.", "bonus": 3500, "type": "threes", "target": 8},
        {"name": "Sniper Efficiency", "description": "Make 5+ threes while shooting 45%+ from three.", "bonus": 3200, "type": "threes_pct", "threes": 5, "three_pct": 0.45},
        {"name": "Catch-and-Shoot Clinic", "description": "Make 4+ threes and win the game.", "bonus": 2600, "type": "threes_win", "threes": 4},
        {"name": "Deep Range Takeover", "description": "Score 35+ PTS with 6+ threes.", "bonus": 3800, "type": "pts_threes", "pts": 35, "threes": 6},
        {"name": "No Hesitation", "description": "Attempt 10+ threes and make 40%+ of them.", "bonus": 3000, "type": "tpa_three_pct", "tpa": 10, "three_pct": 0.40},
        {"name": "Gravity Assist", "description": "Make 4+ threes and record 6+ AST.", "bonus": 2900, "type": "threes_ast", "threes": 4, "ast": 6},
    ],

    "lockdown_defender": [
        {"name": "Clamp Assignment", "description": "Record 3+ steals and hold a win.", "bonus": 2500, "type": "steals_win", "target": 3},
        {"name": "Defensive Chaos", "description": "Record 5 combined steals + blocks.", "bonus": 2800, "type": "stocks", "target": 5},
        {"name": "Pickpocket Night", "description": "Record 4+ steals.", "bonus": 2800, "type": "steals", "target": 4},
        {"name": "Two-Way Stopper", "description": "Record 15+ PTS and 3+ steals.", "bonus": 2700, "type": "pts_steals", "pts": 15, "stl": 3},
        {"name": "Defensive Statement", "description": "Win the game with 4+ stocks.", "bonus": 3000, "type": "stocks_win", "stocks": 4},
        {"name": "Transition Punisher", "description": "Record 3+ steals and 3+ dunks.", "bonus": 3000, "type": "steals_dunks", "stl": 3, "dunks": 3},
        {"name": "Disruptor", "description": "Record 2+ steals, 2+ blocks, and win.", "bonus": 3200, "type": "stl_blk_win", "stl": 2, "blk": 2},
        {"name": "Lockdown Triple Threat", "description": "Record 10+ PTS, 5+ REB, and 3+ stocks.", "bonus": 2900, "type": "pts_reb_stocks", "pts": 10, "reb": 5, "stocks": 3},
    ],

    "slashing_playmaker": [
        {"name": "Paint Touches", "description": "Get 10+ AST and 3+ dunks.", "bonus": 2800, "type": "ast_dunks", "ast": 10, "dunks": 3},
        {"name": "Rim Pressure", "description": "Attempt 8+ free throws and win.", "bonus": 2600, "type": "fta_win", "target": 8},
        {"name": "Drive-and-Dish", "description": "Record 12+ AST.", "bonus": 2800, "type": "assists", "target": 12},
        {"name": "Downhill Engine", "description": "Score 25+ PTS with 4+ dunks.", "bonus": 3200, "type": "pts_dunks", "pts": 25, "dunks": 4},
        {"name": "Contact Magnet", "description": "Attempt 10+ free throws.", "bonus": 2800, "type": "fta", "target": 10},
        {"name": "Paint Collapse", "description": "Record 20+ PTS and 10+ AST.", "bonus": 3300, "type": "pts_ast", "pts": 20, "ast": 10},
        {"name": "Above the Defense", "description": "Record 5+ dunks and win.", "bonus": 3100, "type": "dunks_win", "dunks": 5},
        {"name": "Triple Threat Slasher", "description": "Record 20+ PTS, 8+ AST, and 2+ dunks.", "bonus": 3400, "type": "pts_ast_dunks", "pts": 20, "ast": 8, "dunks": 2},
    ],

    "playmaking_shot_creator": [
        {"name": "Creator Night", "description": "Score 25+ PTS and get 10+ AST.", "bonus": 3000, "type": "pts_ast", "pts": 25, "ast": 10},
        {"name": "Shot Clock Killer", "description": "Make 10+ field goals and get 8+ AST.", "bonus": 2800, "type": "fgm_ast", "fgm": 10, "ast": 8},
        {"name": "Midrange Maestro", "description": "Score 30+ PTS with 50%+ FG.", "bonus": 3300, "type": "pts_fg_pct", "pts": 30, "fg_pct": 0.50},
        {"name": "Table Setter", "description": "Record 14+ AST.", "bonus": 3200, "type": "assists", "target": 14},
        {"name": "Shot Creation Clinic", "description": "Score 35+ PTS and record 6+ AST.", "bonus": 3600, "type": "pts_ast", "pts": 35, "ast": 6},
        {"name": "Low Turnover Lead Guard", "description": "Record 10+ AST with 2 or fewer turnovers.", "bonus": 3400, "type": "ast_low_to", "ast": 10, "to_max": 2},
        {"name": "Pull-Up Threat", "description": "Make 3+ threes and record 8+ AST.", "bonus": 3000, "type": "threes_ast", "threes": 3, "ast": 8},
        {"name": "Floor General Takeover", "description": "Win the game with 12+ AST.", "bonus": 3500, "type": "ast_win", "ast": 12},
    ],

    "two_way_finisher": [
        {"name": "Two-Way Pressure", "description": "Score 20+ PTS with 3+ stocks.", "bonus": 2700, "type": "pts_stocks", "pts": 20, "stocks": 3},
        {"name": "Above The Rim", "description": "Record 5+ dunks.", "bonus": 2500, "type": "dunks", "target": 5},
        {"name": "Rim Runner", "description": "Score 25+ PTS with 4+ dunks.", "bonus": 3000, "type": "pts_dunks", "pts": 25, "dunks": 4},
        {"name": "Defensive Finish", "description": "Record 3+ stocks and win.", "bonus": 2900, "type": "stocks_win", "stocks": 3},
        {"name": "Fastbreak Menace", "description": "Record 3+ steals and 3+ dunks.", "bonus": 3100, "type": "steals_dunks", "stl": 3, "dunks": 3},
        {"name": "Contact Finisher", "description": "Attempt 8+ free throws and score 20+ PTS.", "bonus": 3000, "type": "pts_fta", "pts": 20, "fta": 8},
        {"name": "Athletic Two-Way Night", "description": "Record 20+ PTS, 8+ REB, and 2+ stocks.", "bonus": 3200, "type": "pts_reb_stocks", "pts": 20, "reb": 8, "stocks": 2},
        {"name": "Poster Run", "description": "Record 6+ dunks.", "bonus": 3300, "type": "dunks", "target": 6},
    ],

    "rim_protector": [
        {"name": "No Fly Zone", "description": "Record 4+ blocks.", "bonus": 2700, "type": "blocks", "target": 4},
        {"name": "Paint Anchor", "description": "Record 12+ REB and 3+ BLK.", "bonus": 3000, "type": "reb_blk", "reb": 12, "blk": 3},
        {"name": "Interior Wall", "description": "Record 5+ blocks.", "bonus": 3300, "type": "blocks", "target": 5},
        {"name": "Glass and Swat", "description": "Record 15+ REB and 2+ BLK.", "bonus": 3200, "type": "reb_blk", "reb": 15, "blk": 2},
        {"name": "Defensive Big Win", "description": "Win the game with 4+ stocks.", "bonus": 3000, "type": "stocks_win", "stocks": 4},
        {"name": "Paint Double-Double", "description": "Record 10+ PTS, 10+ REB, and 2+ BLK.", "bonus": 3100, "type": "pts_reb_blk", "pts": 10, "reb": 10, "blk": 2},
        {"name": "Rim Deterrence", "description": "Record 3+ BLK and 8+ defensive rebounds.", "bonus": 2900, "type": "blk_dreb", "blk": 3, "dreb": 8},
        {"name": "Big Man Statement", "description": "Record 15+ PTS, 12+ REB, and 3+ BLK.", "bonus": 3600, "type": "pts_reb_blk", "pts": 15, "reb": 12, "blk": 3},
    ],

    "glass_cleaner": [
        {"name": "Board Man", "description": "Grab 15+ rebounds.", "bonus": 2600, "type": "rebounds", "target": 15},
        {"name": "Second Chances", "description": "Grab 5+ offensive rebounds.", "bonus": 2400, "type": "oreb", "target": 5},
        {"name": "Rebounding Takeover", "description": "Grab 20+ rebounds.", "bonus": 3400, "type": "rebounds", "target": 20},
        {"name": "Offensive Glass Work", "description": "Grab 7+ offensive rebounds.", "bonus": 3100, "type": "oreb", "target": 7},
        {"name": "Possession Battle", "description": "Record 12+ REB and win.", "bonus": 2800, "type": "reb_win", "reb": 12},
        {"name": "Dirty Work Double-Double", "description": "Record 10+ PTS and 15+ REB.", "bonus": 3200, "type": "pts_reb", "pts": 10, "reb": 15},
        {"name": "Glass Cleaner Plus", "description": "Record 18+ REB and 2+ BLK.", "bonus": 3500, "type": "reb_blk", "reb": 18, "blk": 2},
        {"name": "Extra Possessions", "description": "Grab 6+ offensive rebounds and win.", "bonus": 3300, "type": "oreb_win", "oreb": 6},
    ],

    "inside_out_scorer": [
        {"name": "Three-Level Scorer", "description": "Score 35+ PTS with 3+ threes and 2+ dunks.", "bonus": 3200, "type": "inside_out", "pts": 35, "threes": 3, "dunks": 2},
        {"name": "Pressure Package", "description": "Score 30+ PTS and attempt 8+ free throws.", "bonus": 2800, "type": "pts_fta", "pts": 30, "fta": 8},
        {"name": "Rim and Range", "description": "Score 25+ PTS with 3+ threes and 3+ dunks.", "bonus": 3300, "type": "inside_out", "pts": 25, "threes": 3, "dunks": 3},
        {"name": "Scoring Burst", "description": "Score 40+ PTS.", "bonus": 3600, "type": "points", "target": 40},
        {"name": "Efficient Threat", "description": "Score 30+ PTS on 50%+ FG.", "bonus": 3300, "type": "pts_fg_pct", "pts": 30, "fg_pct": 0.50},
        {"name": "Free Throw Pressure", "description": "Attempt 10+ free throws and score 25+ PTS.", "bonus": 3200, "type": "pts_fta", "pts": 25, "fta": 10},
        {"name": "Modern Scorer", "description": "Make 5+ threes and 3+ dunks.", "bonus": 3400, "type": "threes_dunks", "threes": 5, "dunks": 3},
        {"name": "Takeover Scorer", "description": "Score 35+ PTS and win.", "bonus": 3500, "type": "pts_win", "pts": 35},
    ],
}


def get_coach_challenge(archetype_key, games_played=0):
    import random

    pool = COACH_CHALLENGES.get(archetype_key, COACH_CHALLENGES["balanced_star"])

    if not pool:
        return None

    random.seed(f"{archetype_key}-{games_played}")
    return random.choice(pool)


def coach_challenge_completed(challenge, stats, pts, reb):
    ctype = challenge.get("type")

    fgm = stats.get("fgm", 0)
    fga = stats.get("fga", 0)
    tpm = stats.get("tpm", 0)
    tpa = stats.get("tpa", 0)
    ast = stats.get("ast", 0)
    stl = stats.get("stl", 0)
    blk = stats.get("blk", 0)
    dreb = stats.get("dreb", 0)
    oreb = stats.get("oreb", 0)
    dunks = stats.get("dunks", 0)
    fta = stats.get("fta", 0)
    to_val = stats.get("to_val", 0)
    win = stats.get("win", False)

    stocks = stl + blk
    fg_pct = (fgm / fga) if fga > 0 else 0
    three_pct = (tpm / tpa) if tpa > 0 else 0

    if ctype == "balanced":
        return pts >= 20 and reb >= 5 and ast >= 5

    if ctype == "win_pts":
        return win and pts >= 25

    if ctype == "threes":
        return tpm >= challenge["target"]

    if ctype == "pts_threes":
        return pts >= challenge["pts"] and tpm >= challenge["threes"]

    if ctype == "steals_win":
        return stl >= challenge["target"] and win

    if ctype == "stocks":
        return stocks >= challenge["target"]

    if ctype == "ast_dunks":
        return ast >= challenge["ast"] and dunks >= challenge["dunks"]

    if ctype == "fta_win":
        return fta >= challenge["target"] and win

    if ctype == "pts_ast":
        return pts >= challenge["pts"] and ast >= challenge["ast"]

    if ctype == "fgm_ast":
        return fgm >= challenge["fgm"] and ast >= challenge["ast"]

    if ctype == "pts_stocks":
        return pts >= challenge["pts"] and stocks >= challenge["stocks"]

    if ctype == "dunks":
        return dunks >= challenge["target"]

    if ctype == "blocks":
        return blk >= challenge["target"]

    if ctype == "reb_blk":
        return reb >= challenge["reb"] and blk >= challenge["blk"]

    if ctype == "rebounds":
        return reb >= challenge["target"]

    if ctype == "oreb":
        return oreb >= challenge["target"]

    if ctype == "inside_out":
        return pts >= challenge["pts"] and tpm >= challenge["threes"] and dunks >= challenge["dunks"]

    if ctype == "pts_fta":
        return pts >= challenge["pts"] and fta >= challenge["fta"]

    if ctype == "pts_reb_ast":
        return pts >= challenge["pts"] and reb >= challenge["reb"] and ast >= challenge["ast"]

    if ctype == "ast_win":
        return ast >= challenge["ast"] and win

    if ctype == "pts_fg_pct":
        return pts >= challenge["pts"] and fg_pct >= challenge["fg_pct"]

    if ctype == "triple_double":
        categories_10_plus = 0
        if pts >= 10:
            categories_10_plus += 1
        if reb >= 10:
            categories_10_plus += 1
        if ast >= 10:
            categories_10_plus += 1
        if stl >= 10:
            categories_10_plus += 1
        if blk >= 10:
            categories_10_plus += 1
        return categories_10_plus >= 3

    if ctype == "pts_reb_ast_stocks":
        return pts >= challenge["pts"] and reb >= challenge["reb"] and ast >= challenge["ast"] and stocks >= challenge["stocks"]

    if ctype == "threes_pct":
        return tpm >= challenge["threes"] and three_pct >= challenge["three_pct"]

    if ctype == "threes_win":
        return tpm >= challenge["threes"] and win

    if ctype == "tpa_three_pct":
        return tpa >= challenge["tpa"] and three_pct >= challenge["three_pct"]

    if ctype == "threes_ast":
        return tpm >= challenge["threes"] and ast >= challenge["ast"]

    if ctype == "steals":
        return stl >= challenge["target"]

    if ctype == "pts_steals":
        return pts >= challenge["pts"] and stl >= challenge["stl"]

    if ctype == "stocks_win":
        return stocks >= challenge["stocks"] and win

    if ctype == "steals_dunks":
        return stl >= challenge["stl"] and dunks >= challenge["dunks"]

    if ctype == "stl_blk_win":
        return stl >= challenge["stl"] and blk >= challenge["blk"] and win

    if ctype == "pts_reb_stocks":
        return pts >= challenge["pts"] and reb >= challenge["reb"] and stocks >= challenge["stocks"]

    if ctype == "assists":
        return ast >= challenge["target"]

    if ctype == "pts_dunks":
        return pts >= challenge["pts"] and dunks >= challenge["dunks"]

    if ctype == "fta":
        return fta >= challenge["target"]

    if ctype == "dunks_win":
        return dunks >= challenge["dunks"] and win

    if ctype == "pts_ast_dunks":
        return pts >= challenge["pts"] and ast >= challenge["ast"] and dunks >= challenge["dunks"]

    if ctype == "ast_low_to":
        return ast >= challenge["ast"] and to_val <= challenge["to_max"]

    if ctype == "pts_reb_blk":
        return pts >= challenge["pts"] and reb >= challenge["reb"] and blk >= challenge["blk"]

    if ctype == "blk_dreb":
        return blk >= challenge["blk"] and dreb >= challenge["dreb"]

    if ctype == "reb_win":
        return reb >= challenge["reb"] and win

    if ctype == "pts_reb":
        return pts >= challenge["pts"] and reb >= challenge["reb"]

    if ctype == "oreb_win":
        return oreb >= challenge["oreb"] and win

    if ctype == "points":
        return pts >= challenge["target"]

    if ctype == "threes_dunks":
        return tpm >= challenge["threes"] and dunks >= challenge["dunks"]

    if ctype == "pts_win":
        return pts >= challenge["pts"] and win

    return False

def add_team_history(player_id, season_number, team_name, role, contract_years, salary):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO team_history (player_id, season_number, team_name, role, contract_years, salary)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (player_id, season_number, team_name, role, contract_years, salary))
    conn.commit()
    conn.close()


def delete_team_history(history_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM team_history WHERE id = ?", (history_id,))
    conn.commit()
    conn.close()

TENDENCY_CATEGORIES = {
    "Jump Shooting": [
        "Step Through Shot", "Shot Under Basket", "Shot Close", "Shot Close Left", "Shot Close Middle", "Shot Close Right",
        "Shot Mid-Range", "Spot Up Shot Mid-Range", "Off Screen Shot Mid-Range", "Shot Mid Left", "Shot Mid Left-Center",
        "Shot Mid Center", "Shot Mid Right-Center", "Shot Mid Right", "Shot Three", "Spot Up Shot Three",
        "Off Screen Shot Three", "Shot Three Left", "Shot Three Left-Center", "Shot Three Center",
        "Shot Three Right-Center", "Shot Three Right", "Contested Jumper Three", "Contested Jumper Mid-Range",
        "Stepback Jumper Three", "Stepback Jumper Mid-Range", "Spin Jumper", "Transition Pull Up Three",
        "Drive Pull Up Three", "Drive Pull Up Mid-Range", "Use Glass"
    ],
    "Layups and Dunks": [
        "Driving Layup", "Standing Dunk", "Driving Dunk", "Flashy Dunk", "Alley-Oop", "Putback", "Crash",
        "Spin Layup", "Hop Step Layup", "Euro Step Layup", "Floater"
    ],
    "Drive Setup": [
        "Triple Threat Pump Fake", "Triple Threat Jab Step", "Triple Threat Idle", "Triple Threat Shoot",
        "Setup with sizeup", "Setup with hesitation", "No setup dribble"
    ],
    "Driving": [
        "Drive", "Spot Up Drive", "Off Screen Drive", "Drive Right", "Driving Crossover", "Driving Spin",
        "Driving Step Back", "Driving Half Spin", "Driving Double Crossover", "Driving Behind the Back",
        "Driving Dribble Hesitation", "Driving In and Out", "No Driving Dribble Moves", "Attack Strong on Drive"
    ],
    "Passing": ["Dish to Open Man", "Flashy Pass", "Alley-Oop Pass"],
    "Post Game": [
        "Post Up", "Post Shimmy Shot", "Post Face Up", "Post Back Down", "Post Aggressive Backdown",
        "Shoot From Post", "Post Hook Left", "Post Hook Right", "Post Fade Left", "Post Fade Right",
        "Post Up and Under", "Post Hop Shot", "Post Step Back Shot", "Post Drive", "Post Spin",
        "Post Drop Step", "Post Hop Step"
    ],
    "Freelance": [
        "Shot", "Touches", "Roll vs Pop", "Transition Spot Up", "Iso vs Elite Defender",
        "Iso vs Good Defender", "Iso vs Average Defender", "Iso vs Poor Defender", "Play Discipline"
    ],
    "Defense": [
        "Pass Interception", "Take Charge", "On-Ball Steal", "Contest Shot", "Block Shot", "Foul", "Hard Foul"
    ],
}

def default_tendency_value(archetype_key, tendency_name):
    name = tendency_name.lower()

    if archetype_key == "sharpshooter":
        if "three" in name or "jumper" in name or "spot up" in name:
            return 80
        if "dunk" in name or "post" in name:
            return 35
    elif archetype_key == "lockdown_defender":
        if name in ["pass interception", "on-ball steal", "contest shot", "block shot", "take charge"]:
            return 80
        if "shot" in name and "contest" not in name:
            return 45
    elif archetype_key == "slashing_playmaker":
        if "drive" in name or "layup" in name or "dunk" in name or "dish" in name:
            return 75
        if "three" in name:
            return 45
    elif archetype_key == "playmaking_shot_creator":
        if "stepback" in name or "pull up" in name or "mid" in name or "dish" in name or "crossover" in name:
            return 75
    elif archetype_key == "two_way_finisher":
        if "dunk" in name or "drive" in name or "layup" in name or "contest" in name or "steal" in name or "block" in name:
            return 75
    elif archetype_key == "rim_protector":
        if "block" in name or "contest" in name or "post" in name or "standing dunk" in name:
            return 80
        if "three" in name:
            return 20
    elif archetype_key == "glass_cleaner":
        if "putback" in name or "crash" in name or "standing dunk" in name or "post" in name:
            return 75
    elif archetype_key == "inside_out_scorer":
        if "three" in name or "drive" in name or "dunk" in name or "layup" in name:
            return 75

    return 50


def initialize_tendencies(player_id, archetype_key):
    conn = get_connection()
    cursor = conn.cursor()
    rows = []
    for category, tendencies in TENDENCY_CATEGORIES.items():
        for tendency in tendencies:
            rows.append((player_id, category, tendency, default_tendency_value(archetype_key, tendency)))
    cursor.executemany("INSERT OR IGNORE INTO tendencies VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()


def update_tendency(player_id, tendency_name, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tendencies SET value = ? WHERE player_id = ? AND tendency_name = ?",
        (int(value), player_id, tendency_name)
    )
    conn.commit()
    conn.close()
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


ATTRIBUTE_TEMPLATE = [
    ('Offense', 'Driving Layup', 55, 99, 1),
    ('Offense', 'Post Fade', 40, 99, 2),
    ('Offense', 'Post Hook', 40, 99, 2),
    ('Offense', 'Post Control', 40, 99, 1),
    ('Offense', 'Draw Foul', 50, 99, 1),
    ('Offense', 'Close Shot', 55, 99, 1),
    ('Offense', 'Standing Dunk', 40, 99, 1),
    ('Offense', 'Driving Dunk', 55, 99, 2),
    ('Offense', 'Mid-Range Shot', 40, 99, 2),
    ('Offense', 'Three-Point Shot', 25, 99, 3),
    ('Offense', 'Free Throw', 60, 99, 1),

    ('Playmaking', 'Ball Handle', 45, 99, 2),
    ('Playmaking', 'Pass IQ', 50, 99, 1),
    ('Playmaking', 'Pass Accuracy', 50, 99, 2),
    ('Playmaking', 'Shot IQ', 50, 99, 1),
    ('Playmaking', 'Pass Vision', 50, 99, 1),
    ('Playmaking', 'Hands', 50, 99, 1),

    ('Defense', 'Interior Defense', 45, 99, 2),
    ('Defense', 'Perimeter Defense', 45, 99, 2),
    ('Defense', 'Block', 45, 99, 2),
    ('Defense', 'Steal', 45, 99, 2),

    ('Rebounding', 'Offensive Rebound', 45, 99, 2),
    ('Rebounding', 'Defensive Rebound', 45, 99, 2),

    ('Athleticism', 'Speed', 55, 99, 3),
    ('Athleticism', 'Speed With Ball', 55, 99, 2),
    ('Athleticism', 'Vertical', 55, 99, 2),
    ('Athleticism', 'Strength', 50, 99, 1),
    ('Athleticism', 'Stamina', 65, 99, 1),
    ('Athleticism', 'Hustle', 60, 99, 1),
    ('Athleticism', 'Agility', 55, 99, 2),

    ('Mental', 'Pass Perception', 50, 99, 1),
    ('Mental', 'Defensive Consistency', 50, 99, 1),
    ('Mental', 'Help Defense IQ', 50, 99, 1),
    ('Mental', 'Offensive Consistency', 50, 99, 1),
]


ARCHETYPE_ATTRIBUTE_RULES = {
    "balanced_star": {
        "strong_categories": ["Offense", "Playmaking", "Defense", "Athleticism"],
        "weak_categories": [],
        "minimums": {},
    },

    "sharpshooter": {
        "strong_categories": ["Offense", "Mental"],
        "weak_categories": ["Rebounding", "Defense"],
        "minimums": {
            "Mid-Range Shot": 65,
            "Three-Point Shot": 75,
            "Free Throw": 70,
            "Shot IQ": 65,
            "Offensive Consistency": 65,
        },
    },

    "lockdown_defender": {
        "strong_categories": ["Defense", "Mental", "Athleticism"],
        "weak_categories": ["Offense"],
        "minimums": {
            "Perimeter Defense": 75,
            "Steal": 70,
            "Defensive Consistency": 70,
            "Pass Perception": 65,
            "Agility": 65,
        },
    },

    "slashing_playmaker": {
        "strong_categories": ["Offense", "Playmaking", "Athleticism"],
        "weak_categories": ["Rebounding"],
        "minimums": {
            "Driving Layup": 70,
            "Driving Dunk": 70,
            "Ball Handle": 65,
            "Pass Accuracy": 65,
            "Speed": 70,
            "Speed With Ball": 70,
        },
    },

    "playmaking_shot_creator": {
        "strong_categories": ["Offense", "Playmaking"],
        "weak_categories": ["Rebounding"],
        "minimums": {
            "Mid-Range Shot": 70,
            "Three-Point Shot": 65,
            "Ball Handle": 70,
            "Pass Accuracy": 65,
            "Speed With Ball": 65,
        },
    },

    "two_way_finisher": {
        "strong_categories": ["Offense", "Defense", "Athleticism"],
        "weak_categories": ["Rebounding"],
        "minimums": {
            "Driving Layup": 70,
            "Driving Dunk": 75,
            "Standing Dunk": 60,
            "Perimeter Defense": 65,
            "Steal": 60,
            "Vertical": 70,
        },
    },

    "rim_protector": {
        "strong_categories": ["Defense", "Rebounding", "Athleticism"],
        "weak_categories": ["Playmaking", "Offense"],
        "minimums": {
            "Interior Defense": 75,
            "Block": 75,
            "Defensive Rebound": 70,
            "Strength": 70,
            "Standing Dunk": 60,
        },
    },

    "glass_cleaner": {
        "strong_categories": ["Rebounding", "Athleticism", "Defense"],
        "weak_categories": ["Playmaking"],
        "minimums": {
            "Offensive Rebound": 75,
            "Defensive Rebound": 75,
            "Strength": 70,
            "Vertical": 65,
            "Hustle": 65,
        },
    },

    "inside_out_scorer": {
        "strong_categories": ["Offense", "Athleticism"],
        "weak_categories": ["Defense", "Rebounding"],
        "minimums": {
            "Driving Layup": 65,
            "Driving Dunk": 65,
            "Three-Point Shot": 65,
            "Mid-Range Shot": 65,
            "Close Shot": 60,
        },
    },
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


def generate_random_attributes_for_ovr(position, archetype_key, target_ovr):
    import random

    target_ovr = int(target_ovr)
    target_ovr = max(40, min(99, target_ovr))

    rules = ARCHETYPE_ATTRIBUTE_RULES.get(
        archetype_key,
        ARCHETYPE_ATTRIBUTE_RULES["balanced_star"]
    )

    strong_categories = rules.get("strong_categories", [])
    weak_categories = rules.get("weak_categories", [])
    minimums = rules.get("minimums", {})

    generated = {}

    # First random pass
    for category, attr_name, default_level, max_level, cost_multiplier in ATTRIBUTE_TEMPLATE:
        max_level = int(max_level)

        if category in strong_categories:
            low = max(45, target_ovr - 10)
            high = min(max_level, target_ovr + 14)
        elif category in weak_categories:
            low = 25
            high = min(max_level, max(40, target_ovr - 8))
        else:
            low = max(30, target_ovr - 18)
            high = min(max_level, target_ovr + 8)

        if attr_name in minimums:
            low = max(low, minimums[attr_name])

        low = max(25, min(low, max_level))
        high = max(low, min(high, max_level))

        generated[attr_name] = random.randint(low, high)

    # Fine-tune to target OVR
    best_generated = generated.copy()
    best_diff = abs(calculate_ovr(position, generated) - target_ovr)

    max_attempts = 5000

    for _ in range(max_attempts):
        current_ovr = calculate_ovr(position, generated)
        current_diff = abs(current_ovr - target_ovr)

        if current_diff < best_diff:
            best_generated = generated.copy()
            best_diff = current_diff

        if current_ovr == target_ovr:
            return generated

        if current_ovr < target_ovr:
            candidates = []

            for category, attr_name, default_level, max_level, cost_multiplier in ATTRIBUTE_TEMPLATE:
                if generated[attr_name] >= max_level:
                    continue

                weight = OVR_WEIGHTS.get(position, {}).get(attr_name, 0.1)

                priority = weight
                if category in strong_categories:
                    priority += 2.0
                if category in weak_categories:
                    priority -= 1.0

                candidates.append((priority, attr_name, max_level))

            if not candidates:
                break

            candidates.sort(reverse=True)
            top_candidates = candidates[:10]
            _, chosen_attr, max_level = random.choice(top_candidates)

            generated[chosen_attr] = min(max_level, generated[chosen_attr] + 1)

        else:
            candidates = []

            for category, attr_name, default_level, max_level, cost_multiplier in ATTRIBUTE_TEMPLATE:
                min_allowed = minimums.get(attr_name, 25)

                if generated[attr_name] <= min_allowed:
                    continue

                weight = OVR_WEIGHTS.get(position, {}).get(attr_name, 0.1)

                priority = -weight
                if category in weak_categories:
                    priority += 3.0
                if category in strong_categories:
                    priority -= 3.0

                candidates.append((priority, attr_name, min_allowed))

            if not candidates:
                break

            candidates.sort(reverse=True)
            top_candidates = candidates[:10]
            _, chosen_attr, min_allowed = random.choice(top_candidates)

            generated[chosen_attr] = max(min_allowed, generated[chosen_attr] - 1)

    return best_generated

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
        "CREATE TABLE IF NOT EXISTS player_profile (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, position TEXT, jersey_number INTEGER, weight INTEGER, wingspan REAL, total_xp INTEGER DEFAULT 0, overall_rating INTEGER DEFAULT 60, current_season INTEGER DEFAULT 1, archetype TEXT DEFAULT 'balanced_star')")
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
    cursor.execute("PRAGMA table_info(player_profile)")
    profile_columns = [row["name"] for row in cursor.fetchall()]
    if "archetype" not in profile_columns:
        cursor.execute("ALTER TABLE player_profile ADD COLUMN archetype TEXT DEFAULT 'balanced_star'")
    # Existing-save migrations for games table
    add_column_if_missing(cursor, "games", "opponent_team", "TEXT DEFAULT ''")
    add_column_if_missing(cursor, "games", "your_team_score", "INTEGER DEFAULT 0")
    add_column_if_missing(cursor, "games", "opponent_score", "INTEGER DEFAULT 0")
    add_column_if_missing(cursor, "games", "home_away", "TEXT DEFAULT 'Home'")
    add_column_if_missing(cursor, "games", "is_playoffs", "INTEGER DEFAULT 0")
    add_column_if_missing(cursor, "games", "game_type", "TEXT DEFAULT 'Regular Season'")
    add_column_if_missing(cursor, "games", "xp_multiplier", "REAL DEFAULT 1.0")
    add_column_if_missing(cursor, "games", "coach_challenge_name", "TEXT DEFAULT ''")
    add_column_if_missing(cursor, "games", "coach_challenge_completed", "INTEGER DEFAULT 0")
    add_column_if_missing(cursor, "games", "coach_challenge_bonus", "INTEGER DEFAULT 0")

    # Existing-save migrations for player profile / bio
    add_column_if_missing(cursor, "player_profile", "height", "TEXT DEFAULT ''")
    add_column_if_missing(cursor, "player_profile", "handedness", "TEXT DEFAULT 'Right'")
    add_column_if_missing(cursor, "player_profile", "college_country", "TEXT DEFAULT ''")
    add_column_if_missing(cursor, "player_profile", "draft_year", "INTEGER DEFAULT 0")
    add_column_if_missing(cursor, "player_profile", "draft_pick", "TEXT DEFAULT ''")
    add_column_if_missing(cursor, "player_profile", "current_team", "TEXT DEFAULT ''")
    add_column_if_missing(cursor, "player_profile", "nickname", "TEXT DEFAULT ''")
    add_column_if_missing(cursor, "player_profile", "age", "INTEGER DEFAULT 19")
    add_column_if_missing(cursor, "player_profile", "personality_type", "TEXT DEFAULT 'Balanced'")


    # Team history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            season_number INTEGER,
            team_name TEXT,
            role TEXT,
            contract_years INTEGER DEFAULT 1,
            salary INTEGER DEFAULT 0
        )
    """)

    # Milestones / records
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            milestone_name TEXT,
            description TEXT,
            game_id INTEGER,
            season_number INTEGER,
            unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(player_id, milestone_name)
        )
    """)

    # Tendencies
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tendencies (
            player_id INTEGER,
            category TEXT,
            tendency_name TEXT,
            value INTEGER DEFAULT 50,
            PRIMARY KEY (player_id, tendency_name)
        )
    """)

    conn.commit()
    conn.close()

def add_column_if_missing(cursor, table_name, column_name, column_definition):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row["name"] for row in cursor.fetchall()]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")

def create_player(name, position, jersey, weight, wingspan, archetype="balanced_star", height="", starting_ovr=60):
    conn = get_connection()
    cursor = conn.cursor()

    randomized_attributes = generate_random_attributes_for_ovr(
        position,
        archetype,
        starting_ovr
    )

    actual_ovr = calculate_ovr(position, randomized_attributes)

    cursor.execute(
        """
        INSERT INTO player_profile (
            name, position, jersey_number, weight, wingspan,
            total_xp, overall_rating, current_season, archetype, height
        )
        VALUES (?, ?, ?, ?, ?, 0, ?, 1, ?, ?)
        """,
        (name, position, jersey, weight, wingspan, int(actual_ovr), archetype, height)
    )

    player_id = cursor.lastrowid

    attribute_rows = []
    for category, attr_name, default_level, max_level, cost_multiplier in ATTRIBUTE_TEMPLATE:
        starting_level = randomized_attributes.get(attr_name, default_level)

        attribute_rows.append(
            (player_id, category, attr_name, int(starting_level), int(max_level), int(cost_multiplier))
        )

    cursor.executemany(
        "INSERT INTO player_attributes VALUES (?, ?, ?, ?, ?, ?)",
        attribute_rows
    )

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

    cursor.executemany(
        "INSERT INTO badges VALUES (?, ?, ?, ?)",
        badges
    )

    endorsements = [(player_id, *endorsement) for endorsement in get_endorsements_for_archetype(archetype)]

    cursor.executemany(
        "INSERT INTO endorsements VALUES (?, ?, ?, ?, ?)",
        endorsements
    )

    tendency_rows = []
    for category, tendencies in TENDENCY_CATEGORIES.items():
        for tendency in tendencies:
            tendency_rows.append(
                (player_id, category, tendency, default_tendency_value(archetype, tendency))
            )

    cursor.executemany(
        "INSERT OR IGNORE INTO tendencies VALUES (?, ?, ?, ?)",
        tendency_rows
    )

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

    # New feature tables
    cursor.execute("DELETE FROM team_history WHERE player_id = ?", (player_id,))
    cursor.execute("DELETE FROM milestones WHERE player_id = ?", (player_id,))
    cursor.execute("DELETE FROM tendencies WHERE player_id = ?", (player_id,))

    conn.commit()
    conn.close()


def set_player_archetype(player_id, archetype):
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE player_profile SET archetype = ? WHERE id = ?",
            (archetype, player_id)
        )

        endorsements = [(player_id, *endorsement) for endorsement in get_endorsements_for_archetype(archetype)]
        cursor.executemany(
            "INSERT OR IGNORE INTO endorsements VALUES (?, ?, ?, ?, ?)",
            endorsements
        )

        # Reset tendencies to match the new archetype
        cursor.execute("DELETE FROM tendencies WHERE player_id = ?", (player_id,))

        tendency_rows = []
        for category, tendencies in TENDENCY_CATEGORIES.items():
            for tendency in tendencies:
                tendency_rows.append(
                    (player_id, category, tendency, default_tendency_value(archetype, tendency))
                )

        cursor.executemany(
            "INSERT OR IGNORE INTO tendencies VALUES (?, ?, ?, ?)",
            tendency_rows
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        conn.close()


def insert_game(player_id, season_number, stats, xp_earned):
    conn = get_connection()
    cursor = conn.cursor()
    cols = ', '.join(stats.keys())
    placeholders = ', '.join('?' * len(stats))
    query = f"INSERT INTO games (player_id, season_number, {cols}, xp_earned) VALUES (?, ?, {placeholders}, ?)"
    cursor.execute(query, (player_id, season_number, *stats.values(), xp_earned))
    game_id = cursor.lastrowid
    cursor.execute("UPDATE player_profile SET total_xp = total_xp + ? WHERE id = ?", (xp_earned, player_id))
    conn.commit()
    conn.close()
    return game_id


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


def unlock_milestone(player_id, milestone_name, description, game_id, season_number):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO milestones (player_id, milestone_name, description, game_id, season_number)
        VALUES (?, ?, ?, ?, ?)
    """, (player_id, milestone_name, description, game_id, season_number))
    conn.commit()
    conn.close()


def check_game_milestones(player_id, game_id, season_number, stats, pts, reb):
    milestones = []

    if pts >= 30:
        milestones.append(("First 30-Point Game", "Scored 30+ points in a game."))
    if pts >= 50:
        milestones.append(("First 50-Point Game", "Scored 50+ points in a game."))
    if sum([pts >= 10, reb >= 10, stats["ast"] >= 10, stats["stl"] >= 10, stats["blk"] >= 10]) >= 3:
        milestones.append(("First Triple-Double", "Recorded double digits in three stat categories."))
    if stats["ast"] >= 10:
        milestones.append(("First 10-Assist Game", "Recorded 10+ assists in a game."))
    if pts >= 5 and reb >= 5 and stats["ast"] >= 5 and stats["stl"] >= 5 and stats["blk"] >= 5:
        milestones.append(("First 5x5 Game", "Recorded at least 5 in points, rebounds, assists, steals, and blocks."))
    if stats["tpm"] >= 10:
        milestones.append(("First 10-Threes Game", "Made 10+ three-pointers in a game."))
    if reb >= 20:
        milestones.append(("First 20-Rebound Game", "Grabbed 20+ rebounds in a game."))

    for name, desc in milestones:
        unlock_milestone(player_id, name, desc, game_id, season_number)