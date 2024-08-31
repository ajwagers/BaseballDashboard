import streamlit as st
import pandas as pd
import plotly.express as px
from pybaseball import standings, team_batting, team_pitching, batting_stats_bref, pitching_stats_bref
import statsapi

# Dictionary of team abbreviations and team names
mlb_teams = {
    "ARI": "Arizona Diamondbacks",
    "ATL": "Atlanta Braves",
    "BAL": "Baltimore Orioles",
    "BOS": "Boston Red Sox",
    "CHC": "Chicago Cubs",
    "CWS": "Chicago White Sox",
    "CIN": "Cincinnati Reds",
    "CLE": "Cleveland Guardians",
    "COL": "Colorado Rockies",
    "DET": "Detroit Tigers",
    "HOU": "Houston Astros",
    "KCR": "Kansas City Royals",
    "LAA": "Los Angeles Angels",
    "LAD": "Los Angeles Dodgers",
    "MIA": "Miami Marlins",
    "MIL": "Milwaukee Brewers",
    "MIN": "Minnesota Twins",
    "NYM": "New York Mets",
    "NYY": "New York Yankees",
    "OAK": "Oakland Athletics",
    "PHI": "Philadelphia Phillies",
    "PIT": "Pittsburgh Pirates",
    "SDP": "San Diego Padres",
    "SFG": "San Francisco Giants",
    "SEA": "Seattle Mariners",
    "STL": "St. Louis Cardinals",
    "TBR": "Tampa Bay Rays",
    "TEX": "Texas Rangers",
    "TOR": "Toronto Blue Jays",
    "WSN": "Washington Nationals"
}

# Function to get team data
def get_team_data(year):
    batting = team_batting(year).set_index('Team')
    pitching = team_pitching(year).set_index('Team')
    # Combine batting and pitching data, keeping only unique columns
    combined = pd.concat([batting, pitching], axis=1)
    return combined.loc[:, ~combined.columns.duplicated()]

# Function to get player data
def get_player_data(year):
    batting = batting_stats_bref(year)
    pitching = pitching_stats_bref(year)
    return batting, pitching

# Function to get standings
def get_standings(year):
    all_standings = standings(year)
    # Combine all divisions into a single DataFrame
    combined_standings = pd.concat(all_standings)
    # Reset index to make 'Tm' a column
    combined_standings = combined_standings.reset_index(drop=True)
    return combined_standings


# Streamlit app
def main():
    # Set page config at the very beginning
    st.set_page_config(layout="wide", page_title="MLB Team Dashboard", page_icon="⚾")

    st.title("MLB Team Dashboard")

    # Set default team (e.g., to Chicago Cubs, if available)
    default_team = "Chicago Cubs" if "Chicago Cubs" in mlb_teams.values() else list(mlb_teams.values())[0]

    # Sidebar for team selection
    st.sidebar.title("MLB Team Dashboard")
    year = st.sidebar.selectbox("Select Year", range(2023, 2000, -1))
    selected_team = st.sidebar.selectbox("Select a Team", list(mlb_teams.values()), index=list(mlb_teams.values()).index(default_team))

    
    # Get data
    team_data = get_team_data(year)
    batting_data, pitching_data = get_player_data(year)
    standings_data = get_standings(year)

    # Team-level KPIs
    st.header(f"Team-level KPIs for {year}")

    # Find the row for the selected team
    team_row = standings_data[standings_data['Tm'] == selected_team]

       

    # Create three columns for metrics
    col1, col2, col3 = st.columns(3)

    with col1:
         st.metric("Wins", int(team_row['W'].values[0]))
#        st.metric("Run Differential", run_diff)
#        st.metric("Home Runs", hr)
#
    with col2:
        st.metric("Losses", int(team_row['L'].values[0]))
#       st.metric("ERA", f"{era:.2f}")
#       st.metric("RBI", rbi)
#
    with col3:
        st.metric("Win %", team_row['W-L%'].values[0])
#        st.metric("OPS", f"{ops:.3f}")
#        st.metric("Fielding %", f"{fielding_pct:.3f}")

    # Win-Loss Record
    st.subheader("Win-Loss Record")
    fig_wl = px.bar(standings_data, x='Tm', y=['W', 'L'], title="Win-Loss Record by Team")
    st.plotly_chart(fig_wl)

    # Team Batting
    st.subheader("Team Batting")
    if 'OPS' in team_data.columns and 'R' in team_data.columns and 'HR' in team_data.columns:
        fig_batting = px.scatter(team_data, x='OPS', y='R', hover_name=team_data.index, 
                                 size='HR', title="Team OPS vs Runs Scored")
        st.plotly_chart(fig_batting)
    else:
        st.write("Required batting data not available for the selected year.")

    # Team Pitching
    st.subheader("Team Pitching")
    if 'ERA' in team_data.columns and 'WHIP' in team_data.columns and 'SO' in team_data.columns:
        fig_pitching = px.scatter(team_data, x='ERA', y='WHIP', hover_name=team_data.index, 
                                  size='SO', title="Team ERA vs WHIP")
        st.plotly_chart(fig_pitching)
    else:
        st.write("Required pitching data not available for the selected year.")

    # Player-level KPIs
    st.header("Player-level KPIs")
    
    # Top Batters
    st.subheader("Top Batters by OPS")
    if 'OPS' in batting_data.columns:
        top_batters = batting_data.sort_values('OPS', ascending=False).head(10)
        fig_top_batters = px.bar(top_batters, x='Name', y='OPS', title="Top 10 Batters by OPS")
        st.plotly_chart(fig_top_batters)
    else:
        st.write("OPS data not available for the selected year.")

    # Top Pitchers
    st.subheader("Top Pitchers by ERA")
    if 'ERA' in pitching_data.columns and 'IP' in pitching_data.columns:
        top_pitchers = pitching_data[pitching_data['IP'] > 50].sort_values('ERA').head(10)
        fig_top_pitchers = px.bar(top_pitchers, x='Name', y='ERA', title="Top 10 Pitchers by ERA (min 50 IP)")
        st.plotly_chart(fig_top_pitchers)
    else:
        st.write("Required pitching data not available for the selected year.")

if __name__ == "__main__":
    main()
