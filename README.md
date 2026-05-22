# NBA 2K MyPlayer Career Tracker

This app was made for fun because I really wanted an actual system for my MyNBA Player Career playthroughs. It was inspired by Synergy2K, who were making apps like this for the older versions of 2K. I needed something like it for 2K26, so I made my own with the help of AI, of course.

This project is a custom career-tracking tool for NBA 2K MyNBA/MyPlayer-style saves. Instead of just imagining progression, this app gives your created player a full RPG-like system with XP, attributes, badges, game logs, awards, milestones, team history, and career progression.

It is built with **Python**, **Streamlit**, **SQLite**, and **Pandas**.

---

## Features

### Player Creation

Create a custom MyPlayer-style career with:

- Player name
- Position
- Archetype / takeover style
- Jersey number
- Height
- Weight
- Wingspan
- Editable player bio
- Career identity details such as nickname, handedness, age, college/country, draft info, current team, and personality type

---

### Archetype System

Players can be assigned an archetype that affects their career identity and progression style.

Examples include:

- Balanced Star
- Sharpshooter
- Lockdown Defender
- Slashing Playmaker
- Playmaking Shot Creator
- Two-Way Finisher
- Rim Protector
- Glass Cleaner
- Inside-Out Scorer

Each archetype can influence things like:

- XP bonuses
- Attribute upgrade discounts
- Coach challenge types
- Player tendencies
- Career playstyle

---

### Game Logging

Log individual games with detailed stats such as:

- Points
- Rebounds
- Assists
- Steals
- Blocks
- Field goals
- Three-pointers
- Free throws
- Turnovers
- Fouls
- Dunks
- Win/loss result

The app calculates XP based on performance and adds it to your player's career progression.

---

### Game Context System

Not every game should feel the same, so the app includes high-stakes game types with XP multipliers:

| Game Type | XP Multiplier |
|---|---:|
| Regular Season | 1.0x |
| Prime-Time / Rivalry | 1.2x |
| Playoffs | 1.5x |
| Elimination Game | 2.0x |

This makes playoff games, rivalry games, and elimination games feel more important.

---

### Matchup Details

Game logs can include more realistic context, such as:

- Opponent team
- Your team score
- Opponent score
- Home / away / neutral game
- Playoff game indicator
- Game type

Example game log:

```text
W vs Lakers, 112-104
42 PTS | 8 REB | 11 AST | +2,340 XP
```

---

### Coach's Challenges

The app can generate short-term game objectives based on your player's archetype.

Example:

```text
Coach's Challenge:
We need ball movement tonight.
Get 12+ assists for a 2,500 XP bonus.
```

These challenges add game-to-game variety and encourage different playstyles instead of always chasing the same stats.

---

### XP and Progression

Players earn XP from:

- Game performance
- Winning games
- High-impact stat lines
- Takeover-style bonuses
- Coach challenges
- Endorsements
- Season awards
- Career achievements

XP can be spent on:

- Attribute upgrades
- Badge upgrades
- Career progression

---

### Attribute System

The app includes a custom attribute system inspired by NBA 2K.

Attributes are grouped into categories such as:

- Finishing
- Shooting
- Playmaking
- Defense
- Physicals
- Rebounding

The app calculates an overall rating based on position-specific attribute weights.

---

### Badge System

Badges can be upgraded using XP.

The badge system supports multiple badge levels and allows the player to progress over time, similar to an RPG or 2K-style build system.

---

### Tendencies

The app includes a tendency system inspired by NBA 2K/MyNBA simulation logic.

Tendencies can affect the player's simulated playstyle, such as:

- Shot frequency
- Three-point tendency
- Driving tendency
- Dunk tendency
- Passing tendency
- Post tendency
- Defensive aggression
- Contest shot tendency
- Steal/block tendency

This helps make each player feel more unique beyond just attributes.

---

### Endorsements

Endorsements act as long-term goals that reward XP when completed.

They are designed to give the career mode more structure and long-term objectives.

---

### Season System

At the end of each season, the app can record:

- Season averages
- Games played
- Awards won
- XP bonuses
- Career progression
- Historical season records

Awards can include:

- NBA Champion
- Finals MVP
- MVP
- Defensive Player of the Year
- Rookie of the Year
- All-Rookie Team
- Most Improved Player
- Clutch Player of the Year
- Sixth Man of the Year
- All-NBA Team
- All-Defensive Team
- Dunk Contest Winner
- 3PT Contest Winner

Rookie-specific awards are only meant to be available during the player's first season.

---

### Team History

Track your player's career journey across teams.

Example:

```text
Season 1 — Drafted by the Orlando Magic
Season 2 — Signed with the Miami Heat
Season 3 — Won MVP with the Los Angeles Lakers
```

Team history can include:

- Season number
- Team name
- Role or story description
- Contract length
- Salary

This helps make the career feel more like a real MyNBA storyline.

---

### Milestones and Records

The app includes a milestone system for legacy moments.

Examples:

- First 30-point game
- First 50-point game
- First triple-double
- First 10-assist game
- First 5x5 game
- First 10-threes game
- First 20-rebound game
- First 99 overall
- First Legend badge
- First MVP
- First championship

These milestones help build a long-term career story.

---

### Analytics

The analytics page gives a deeper look at your player's career.

Stats can include:

- Career highs
- Season progression
- Game log history
- FG%
- 3P%
- FT%
- True Shooting %
- Points per shot
- Assist-to-turnover ratio
- Last 5 games averages
- Last 10 games averages
- Win percentage
- Average XP per game
- Best season
- Most improved stat

The goal is to make the app feel closer to a Basketball Reference / NBA 2K career dashboard.

---

### GOAT Meter and Trophy Cabinet

The app includes a legacy-style system that tracks your player's greatness over time.

The GOAT Meter considers things like:

- Career stats
- Championships
- MVPs
- Finals MVPs
- Defensive awards
- All-NBA selections
- Other achievements

The Trophy Cabinet gives a visual summary of major awards and accomplishments.

---

## Tech Stack

This project uses:

- Python
- Streamlit
- SQLite
- Pandas

---

## Installation

Clone the repository:

```bash
git clone https://github.com/IshBiz/2kTracker.git
cd 2kTracker
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment:

### Windows PowerShell

```bash
.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install streamlit pandas
```

If a `requirements.txt` file is included, you can use:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app.py
```

---

## Running on Another Computer on the Same Network

You can host the app from one computer and access it from another device on the same Wi-Fi.

Run:

```bash
streamlit run app.py --server.address 0.0.0.0
```

Then find your local IP address:

```bash
ipconfig
```

Open this on the other computer:

```text
http://YOUR_LOCAL_IP:8501
```

Example:

```text
http://192.168.1.45:8501
```

---

## Database

The app uses a local SQLite database file:

```text
nba2k_career.db
```

This file stores:

- Player profiles
- Attributes
- Badges
- Game logs
- Endorsements
- Season records
- Team history
- Milestones
- Tendencies

If you want to move your save to another computer, copy this database file along with the project.

---

## Project Structure

```text
2kTracker/
├── app.py
├── database.py
├── nba2k_career.db
├── requirements.txt
└── README.md
```

---

## Current Status

This is a personal/fun project and is still being improved.

The goal is not to perfectly recreate NBA 2K's official progression formula, since those exact systems are not publicly documented. Instead, this app uses a custom 2K-inspired progression system designed to make MyNBA Player Career saves more immersive, structured, and fun.

---

## Future Ideas

Possible future improvements:

- Edit/delete previous games
- Undo last action
- More detailed playoff tracking
- Player comparison tools
- Shot chart system
- Contract negotiation system
- Draft combine system
- Injury system
- Hall of Fame tracker
- More advanced simulation logic
- Export career reports
- Better mobile layout
- Online deployment

---

## Credits

Inspired by:

- NBA 2K MyNBA / MyCareer-style progression
- Synergy2K-style tools for older 2K games
- Basketball Reference-style stat tracking
- RPG progression systems

Built for fun by someone who wanted a better way to track custom NBA 2K26 player career saves.

Created with the help of AI.
