import streamlit as st
import pandas as pd
import plotly.express as px
from pybaseball import standings, team_batting, team_pitching, batting_stats_bref, pitching_stats_bref
import statsapi
from streamlit_extras.metric_cards import style_metric_cards
import requests
import json
import base64
from pathlib import Path
import datetime
import re
from collections import Counter

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

def load_bootstrap():
    return st.markdown('<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">', unsafe_allow_html=True)

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

def get_team_json_data():
    response = requests.get('https://statsapi.mlb.com/api/v1/teams/')
    try:
        data_dict = response.json()
        teams_lookup = {team["name"]: team for team in data_dict.get("teams", [])}
        return teams_lookup
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

def img_to_bytes(img_path):
      response = requests.get(img_path)
      img_bytes = response.content
      encoded = base64.b64encode(img_bytes).decode()
      return encoded

def img_to_html(img_path):
      img_html = "<img src='data:image/png;base64,{}' class='img-fluid' >".format(
        img_to_bytes(img_path)
      )
      return img_html

def extract_colors_from_svg(svg_content):
    # Regular expression to find color values in SVG
    color_pattern = re.compile(r'(?:fill|stroke)="(#[0-9A-Fa-f]{6})"')
    colors = color_pattern.findall(svg_content)
    
    # Count occurrences of each color
    color_counts = Counter(colors)
    
    # Get the top 3 most common colors
    main_colors = [color for color, _ in color_counts.most_common(3)]
    
    # If we have fewer than 3 colors, add white or black
    while len(main_colors) < 3:
        if "#FFFFFF" not in main_colors:
            main_colors.append("#FFFFFF")  # white
        elif "#000000" not in main_colors:
            main_colors.append("#000000")  # black
    
    return main_colors[:3]

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def set_streamlit_colors(colors):
    primary_color = colors[0]
    secondary_color = colors[1]
    background_color = colors[2]
    
    st.markdown(f"""
    <style>
    .stApp {{
        background-color: {background_color};
    }}
    .stButton>button {{
        color: {secondary_color};
        background-color: {primary_color};
    }}
    .stTextInput>div>div>input {{
        color: {primary_color};
    }}
    /* Metric card styling */
    div.css-1r6slb0.e1tzin5v2 {{
        background-color: {primary_color};
        border: 1px solid {primary_color};
        border-left: 0.5rem solid {primary_color} !important;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important;
        color: {background_color};
    }}
    div.css-1r6slb0.e1tzin5v2 {{
        border-left: 0.5rem solid {primary_color} !important;
    }}
    label.css-mkogse.e16fv1kl2 {{
        color: {background_color} !important;
    }}
    div.css-1xarl3l.e16fv1kl1 {{
        color: {background_color};
    }}
    
    div.css-1ht1j8u.e16fv1kl0 {{
        color: {secondary_color};
    }}
    </style>
    """, unsafe_allow_html=True)

# Streamlit app
def main():
    # Set page config at the very beginning
    st.set_page_config(layout="wide", page_title="MLB Team Dashboard", page_icon="⚾", initial_sidebar_state="expanded")

    load_bootstrap()

    # Call style.css
    #with open('style.css') as f:
    #    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    team_json_data = get_team_json_data()
    
    # Set default team (e.g., to Chicago Cubs, if available)
    default_team = "Chicago Cubs" if "Chicago Cubs" in mlb_teams.values() else list(mlb_teams.values())[0]
    selected_team_id = team_json_data[default_team]['id']


    # Sidebar for team selection
    st.sidebar.title("MLB Team Dashboard")
    year = st.sidebar.selectbox("Select Year", range(datetime.datetime.now().year, 2000, -1))
    selected_team = st.sidebar.selectbox("Select a Team", list(mlb_teams.values()), index=list(mlb_teams.values()).index(default_team))
    selected_team_id = team_json_data[selected_team]['id']

    # Extract colors from the team logo SVG
    logo_url = f"https://www.mlbstatic.com/team-logos/team-cap-on-light/{selected_team_id}.svg"
    response = requests.get(logo_url)
    if response.status_code == 200:
        svg_content = response.text
        main_colors = extract_colors_from_svg(svg_content)
        set_streamlit_colors(main_colors)
    else:
        st.error(f"Failed to fetch logo: HTTP {response.status_code}")

    col1, col2 = st.columns((1,3))
    with col2:
        st.title(f"{selected_team} Team Dashboard")
    with col1:
        st.markdown(f"<img src={logo_url} height='100'>", unsafe_allow_html=True)
    

    # Get data
    team_data = get_team_data(year)
    batting_data, pitching_data = get_player_data(year)
    standings_data = get_standings(year)

    # Team-level KPIs
    #st.header(f"{selected_team} KPIs for {year}")

    # Find the row for the selected team
    team_row = standings_data[standings_data['Tm'] == selected_team]

       

    # Create three columns for metrics
    col1, col2, col3, col4 = st.columns((1,2,2,2))

    with col1:
        st.header(f"{year}")

    with col2:
         st.metric("Wins", int(team_row['W'].values[0]))
#        st.metric("Run Differential", run_diff)
#        st.metric("Home Runs", hr)
#
    with col3:
        st.metric("Losses", int(team_row['L'].values[0]))
#       st.metric("ERA", f"{era:.2f}")
#       st.metric("RBI", rbi)
#
    with col4:
        st.metric("Win %", team_row['W-L%'].values[0])
#        st.metric("OPS", f"{ops:.3f}")
#        st.metric("Fielding %", f"{fielding_pct:.3f}")

    style_metric_cards()

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
