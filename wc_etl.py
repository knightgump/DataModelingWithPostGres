import os
import glob
import psycopg2
import pandas as pd
from wc_sql_queries import (
    teams_table_insert, players_table_insert, matches_table_insert,
    group_standings_table_insert, predictions_table_insert,
    team_id_select
)


def get_team_id(cur, fifa_code):
    cur.execute(team_id_select, (fifa_code,))
    result = cur.fetchone()
    return result[0] if result else None


def determine_winner_id(cur, home_code, away_code, home_goals, away_goals):
    if home_goals is None or away_goals is None:
        return None
    if home_goals > away_goals:
        return get_team_id(cur, home_code)
    if away_goals > home_goals:
        return get_team_id(cur, away_code)
    return None  # draw


def process_teams_file(cur, conn, filepath):
    df = pd.read_csv(filepath)
    for _, row in df.iterrows():
        cur.execute(teams_table_insert, (
            row['name'], row['fifa_code'], row['group_name'],
            row['region'], int(row['ranking'])
        ))
    conn.commit()
    print(f"Teams loaded from {os.path.basename(filepath)}")


def process_players_file(cur, conn, filepath):
    df = pd.read_csv(filepath)
    for _, row in df.iterrows():
        team_id = get_team_id(cur, row['team_code'])
        if team_id is None:
            print(f"  Warning: team code {row['team_code']} not found, skipping {row['name']}")
            continue
        cur.execute(players_table_insert, (
            team_id, row['name'], row['position'],
            int(row['age']), int(row['caps']), int(row['goals'])
        ))
    conn.commit()
    print(f"Players loaded from {os.path.basename(filepath)}")


def process_matches_file(cur, conn, filepath):
    df = pd.read_csv(filepath)
    inserted = 0
    for _, row in df.iterrows():
        home_id = get_team_id(cur, row['home_code'])
        away_id = get_team_id(cur, row['away_code'])
        if home_id is None or away_id is None:
            print(f"  Warning: unknown team code in match {row['home_code']} vs {row['away_code']}")
            continue

        home_goals = int(row['home_goals']) if not pd.isna(row['home_goals']) else None
        away_goals = int(row['away_goals']) if not pd.isna(row['away_goals']) else None
        winner_id = determine_winner_id(cur, row['home_code'], row['away_code'], home_goals, away_goals)

        cur.execute(matches_table_insert, (
            row['stage'], row['match_date'], home_id, away_id,
            home_goals, away_goals, winner_id
        ))
        inserted += 1
    conn.commit()
    print(f"{inserted} matches loaded from {os.path.basename(filepath)}")


def compute_group_standings(cur, conn):
    """Derive group standings from group stage match results."""
    cur.execute("SELECT team_id, group_name FROM teams")
    teams = cur.fetchall()

    for team_id, group_name in teams:
        cur.execute("""
            SELECT
                COUNT(*) AS played,
                SUM(CASE WHEN winner_id = %s THEN 1 ELSE 0 END) AS won,
                SUM(CASE WHEN winner_id IS NULL
                          AND (home_team_id = %s OR away_team_id = %s) THEN 1 ELSE 0 END) AS drawn,
                SUM(CASE WHEN winner_id IS NOT NULL AND winner_id != %s
                          AND (home_team_id = %s OR away_team_id = %s) THEN 1 ELSE 0 END) AS lost,
                SUM(CASE WHEN home_team_id = %s THEN home_goals
                         WHEN away_team_id = %s THEN away_goals ELSE 0 END) AS goals_for,
                SUM(CASE WHEN home_team_id = %s THEN away_goals
                         WHEN away_team_id = %s THEN home_goals ELSE 0 END) AS goals_against
            FROM matches
            WHERE stage = 'Group Stage'
              AND (home_team_id = %s OR away_team_id = %s)
        """, (
            team_id,
            team_id, team_id,
            team_id, team_id, team_id,
            team_id, team_id,
            team_id, team_id,
            team_id, team_id
        ))
        row = cur.fetchone()
        played, won, drawn, lost, goals_for, goals_against = row
        points = won * 3 + drawn

        cur.execute(group_standings_table_insert, (
            team_id, group_name, played, won, drawn, lost,
            goals_for, goals_against, points
        ))

    conn.commit()
    print("Group standings computed and inserted.")


def generate_predictions(cur, conn):
    """
    Simple ranking-based prediction model.
    Uses FIFA ranking (lower = better) to estimate win probabilities.
    """
    cur.execute("""
        SELECT m.match_id, t_h.ranking, t_a.ranking
        FROM matches m
        JOIN teams t_h ON m.home_team_id = t_h.team_id
        JOIN teams t_a ON m.away_team_id = t_a.team_id
        WHERE m.home_goals IS NOT NULL
    """)
    matches = cur.fetchall()

    for match_id, home_rank, away_rank in matches:
        home_rank = home_rank or 50
        away_rank = away_rank or 50

        # Invert rankings so better-ranked team gets higher raw score
        home_strength = 1.0 / home_rank
        away_strength = 1.0 / away_rank
        home_advantage = 1.1  # slight home/first-listed bias

        home_raw = home_strength * home_advantage
        away_raw = away_strength
        draw_raw = (home_raw + away_raw) * 0.3

        total = home_raw + away_raw + draw_raw
        home_prob = round(home_raw / total, 4)
        away_prob = round(away_raw / total, 4)
        draw_prob = round(1.0 - home_prob - away_prob, 4)

        if home_prob > draw_prob and home_prob > away_prob:
            cur.execute("SELECT home_team_id FROM matches WHERE match_id = %s", (match_id,))
        elif away_prob > home_prob and away_prob > draw_prob:
            cur.execute("SELECT away_team_id FROM matches WHERE match_id = %s", (match_id,))
        else:
            cur.execute("SELECT NULL")
        result = cur.fetchone()
        predicted_winner = result[0] if result else None

        cur.execute(predictions_table_insert, (
            match_id, predicted_winner, home_prob, draw_prob, away_prob, "v1.0-ranking"
        ))

    conn.commit()
    print(f"Predictions generated for {len(matches)} matches.")


def process_data(cur, conn, directory, pattern, func):
    files = glob.glob(os.path.join(directory, pattern))
    print(f"{len(files)} file(s) found in {directory}")
    for f in sorted(files):
        func(cur, conn, f)


def main():
    conn = psycopg2.connect("host=127.0.0.1 dbname=worldcupdb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, 'data/teams',   '*.csv', process_teams_file)
    process_data(cur, conn, 'data/players', '*.csv', process_players_file)
    process_data(cur, conn, 'data/matches', '*.csv', process_matches_file)
    compute_group_standings(cur, conn)
    generate_predictions(cur, conn)

    conn.close()
    print("ETL complete.")


if __name__ == "__main__":
    main()
