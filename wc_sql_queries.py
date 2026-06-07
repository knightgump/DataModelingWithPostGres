"""All SQL statements for the World Cup Predictor project."""

# DROP TABLES

predictions_table_drop = "DROP TABLE IF EXISTS predictions"
matches_table_drop = "DROP TABLE IF EXISTS matches"
group_standings_table_drop = "DROP TABLE IF EXISTS group_standings"
players_table_drop = "DROP TABLE IF EXISTS players"
teams_table_drop = "DROP TABLE IF EXISTS teams"

# CREATE TABLES

teams_table_create = """
CREATE TABLE IF NOT EXISTS teams (
    team_id   SERIAL PRIMARY KEY,
    name      VARCHAR NOT NULL UNIQUE,
    fifa_code VARCHAR(3) NOT NULL UNIQUE,
    group_name VARCHAR(1) NOT NULL,
    region    VARCHAR,
    ranking   INT
);"""

players_table_create = """
CREATE TABLE IF NOT EXISTS players (
    player_id  SERIAL PRIMARY KEY,
    team_id    INT NOT NULL REFERENCES teams(team_id),
    name       VARCHAR NOT NULL,
    position   VARCHAR,
    age        INT,
    caps       INT DEFAULT 0,
    goals      INT DEFAULT 0
);"""

matches_table_create = """
CREATE TABLE IF NOT EXISTS matches (
    match_id      SERIAL PRIMARY KEY,
    stage         VARCHAR NOT NULL,
    match_date    DATE,
    home_team_id  INT NOT NULL REFERENCES teams(team_id),
    away_team_id  INT NOT NULL REFERENCES teams(team_id),
    home_goals    INT,
    away_goals    INT,
    winner_id     INT REFERENCES teams(team_id)
);"""

group_standings_table_create = """
CREATE TABLE IF NOT EXISTS group_standings (
    standing_id SERIAL PRIMARY KEY,
    team_id     INT NOT NULL REFERENCES teams(team_id),
    group_name  VARCHAR(1) NOT NULL,
    played      INT DEFAULT 0,
    won         INT DEFAULT 0,
    drawn       INT DEFAULT 0,
    lost        INT DEFAULT 0,
    goals_for   INT DEFAULT 0,
    goals_against INT DEFAULT 0,
    points      INT DEFAULT 0
);"""

predictions_table_create = """
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id SERIAL PRIMARY KEY,
    match_id      INT NOT NULL REFERENCES matches(match_id),
    predicted_winner_id INT REFERENCES teams(team_id),
    home_win_prob NUMERIC(5,4),
    draw_prob     NUMERIC(5,4),
    away_win_prob NUMERIC(5,4),
    model_version VARCHAR,
    created_at    TIMESTAMP DEFAULT NOW()
);"""

# INSERT RECORDS

teams_table_insert = """
INSERT INTO teams (name, fifa_code, group_name, region, ranking)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (fifa_code) DO UPDATE
    SET ranking = EXCLUDED.ranking;"""

players_table_insert = """
INSERT INTO players (team_id, name, position, age, caps, goals)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT DO NOTHING;"""

matches_table_insert = """
INSERT INTO matches (stage, match_date, home_team_id, away_team_id, home_goals, away_goals, winner_id)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT DO NOTHING
RETURNING match_id;"""

group_standings_table_insert = """
INSERT INTO group_standings (team_id, group_name, played, won, drawn, lost, goals_for, goals_against, points)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT DO NOTHING;"""

predictions_table_insert = """
INSERT INTO predictions (match_id, predicted_winner_id, home_win_prob, draw_prob, away_win_prob, model_version)
VALUES (%s, %s, %s, %s, %s, %s);"""

# FIND QUERIES

team_id_select = "SELECT team_id FROM teams WHERE fifa_code = %s;"

group_matches_select = """
SELECT
    t_home.name  AS home_team,
    t_away.name  AS away_team,
    m.home_goals,
    m.away_goals,
    t_win.name   AS winner
FROM matches m
JOIN teams t_home ON m.home_team_id = t_home.team_id
JOIN teams t_away ON m.away_team_id = t_away.team_id
LEFT JOIN teams t_win  ON m.winner_id  = t_win.team_id
WHERE m.stage = 'Group Stage'
ORDER BY m.match_date;"""

group_standings_select = """
SELECT
    t.name,
    gs.group_name,
    gs.played,
    gs.won,
    gs.drawn,
    gs.lost,
    gs.goals_for,
    gs.goals_against,
    gs.goals_for - gs.goals_against AS goal_diff,
    gs.points
FROM group_standings gs
JOIN teams t ON gs.team_id = t.team_id
ORDER BY gs.group_name, gs.points DESC, goal_diff DESC;"""

top_scorers_select = """
SELECT
    p.name,
    t.name AS team,
    p.goals
FROM players p
JOIN teams t ON p.team_id = t.team_id
WHERE p.goals > 0
ORDER BY p.goals DESC
LIMIT 10;"""

predictions_select = """
SELECT
    t_home.name AS home_team,
    t_away.name AS away_team,
    t_pred.name AS predicted_winner,
    pr.home_win_prob,
    pr.draw_prob,
    pr.away_win_prob
FROM predictions pr
JOIN matches m        ON pr.match_id = m.match_id
JOIN teams t_home     ON m.home_team_id = t_home.team_id
JOIN teams t_away     ON m.away_team_id = t_away.team_id
LEFT JOIN teams t_pred ON pr.predicted_winner_id = t_pred.team_id
ORDER BY m.match_date;"""

# QUERY LISTS

create_table_queries = [
    teams_table_create,
    players_table_create,
    matches_table_create,
    group_standings_table_create,
    predictions_table_create,
]

drop_table_queries = [
    predictions_table_drop,
    matches_table_drop,
    group_standings_table_drop,
    players_table_drop,
    teams_table_drop,
]
