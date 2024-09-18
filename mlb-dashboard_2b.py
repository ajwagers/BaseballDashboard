import streamlit as st
import pandas as pd
import plotly.express as px
from pybaseball import standings, team_batting, team_pitching, batting_stats_bref, pitching_stats_bref, schedule_and_record
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

#def load_bootstrap():
#    return st.markdown('<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">', unsafe_allow_html=True)

def get_team_abbreviation(team_name):
    for abbr, name in mlb_teams.items():
        if name.lower() == team_name.lower():
            return abbr
    return None  # Return None if the team name is not found

# Function to get team data
def get_team_data(year):
    try:
        batting = team_batting(year).set_index('Team')
        pitching = team_pitching(year).set_index('Team')
        # Combine batting and pitching data, keeping only unique columns
        combined = pd.concat([batting, pitching], axis=1)
        return combined.loc[:, ~combined.columns.duplicated()]
    except Exception as e:
        print(f"Error fetching team data from pybaseball: {e}")
        return get_team_data_statsapi(year)
    
def get_team_data_statsapi(year):
    teams = statsapi.get('teams', {'sportId': 1, 'season': year})['teams']
    team_data = []
    for team in teams:
        team_id = team['id']
        batting_stats = statsapi.team_stats(team_id, group='hitting', type='season', season=year)
        pitching_stats = statsapi.team_stats(team_id, group='pitching', type='season', season=year)
        combined_stats = {**batting_stats, **pitching_stats, 'Team': team['name']}
        team_data.append(combined_stats)
    return pd.DataFrame(team_data).set_index('Team')

# Function to get player data
def get_player_data(year):
    try:
        batting = batting_stats_bref(year)
        pitching = pitching_stats_bref(year)
        return batting, pitching
    except Exception as e:
        print(f"Error fetching player data from pybaseball: {e}")
        return get_player_data_statsapi(year)
    
def get_player_data_statsapi(year):
    batting = []
    pitching = []
    teams = statsapi.get('teams', {'sportId': 1, 'season': year})['teams']
    for team in teams:
        team_id = team['id']
        roster = statsapi.get('team_roster', {'teamId': team_id})['roster']
        for player in roster:
            player_id = player['person']['id']
            player_stats = statsapi.player_stats(player_id, 'hitting', 'season')
            if player_stats:
                stats = player_stats[0]['stats'][0]['splits'][0]['stat']
                stats['Name'] = player['person']['fullName']
                stats['Team'] = team['name']
                batting.append(stats)
            
            player_stats = statsapi.player_stats(player_id, 'pitching', 'season')
            if player_stats:
                stats = player_stats[0]['stats'][0]['splits'][0]['stat']
                stats['Name'] = player['person']['fullName']
                stats['Team'] = team['name']
                pitching.append(stats)
    
    return pd.DataFrame(batting), pd.DataFrame(pitching)

# Function to get standings
def get_standings(year):
    try:
        all_standings = standings(year)
        # Combine all divisions into a single DataFrame
        combined_standings = pd.concat(all_standings)
        # Reset index to make 'Tm' a column
        return combined_standings.reset_index(drop=True)
    except Exception as e:
        print(f"Error fetching standings from pybaseball: {e}")
        return get_standings_statsapi(year)
    
def get_standings_statsapi(year):
    standings_data = statsapi.standings(season=year)
    print(standings_data)

    # Regular expression to match each team's data
    team_pattern = re.compile(r'(\d+)\s+([\w\s.]+)\s+(\d+)\s+(\d+)\s+([-\d.]+)\s+(\d+)\s+(\d+)\s+([-\d.]+)\s+(\d+)')
    
    # Regular expression to match division names
    division_pattern = re.compile(r'(American|National) League (East|West|Central)')
    
    all_teams = []
    current_division = ""

    for line in standings_string.split('\n'):
        division_match = division_pattern.search(line)
        if division_match:
            current_division = division_match.group(0)
        else:
            team_match = team_pattern.search(line)
            if team_match:
                rank, team, w, l, gb, _, wc_rank, wc_gb, _ = team_match.groups()
                team_data = {
                    'Tm': team.strip(),
                    'W': int(w),
                    'L': int(l),
                    'W-L%': round(int(w) / (int(w) + int(l)), 3),
                    'GB': 0.0 if gb == '-' else float(gb),
                    'Division': current_division,
                    'Rank': int(rank),
                    'WC Rank': int(wc_rank),
                    'WC GB': 0.0 if wc_gb == '-' else float(wc_gb)
                }
                all_teams.append(team_data)
    
    return pd.DataFrame(all_teams)

def get_team_json_data():
    response = requests.get('https://statsapi.mlb.com/api/v1/teams/')
    try:
        data_dict = response.json()
        teams_lookup = {team["name"]: team for team in data_dict.get("teams", [])}
        return teams_lookup
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

def convert_dates(df):
    # Get the current year
    current_year = datetime.datetime.now().year

    # Function to add year and convert to ISO format
    def add_year_and_convert(date_str):
        try:
            # Remove any content in parentheses and trim whitespace
            date_str = re.sub(r'\s*\([^)]*\)', '', date_str).strip()

            # Parse the date string
            date_obj = datetime.datetime.strptime(date_str, "%A, %b %d")
            
            # Add the current year
            date_with_year = date_obj.replace(year=current_year)
            
            # If the resulting date is in the future, subtract a year
            if date_with_year > datetime.datetime.now():
                date_with_year = date_with_year.replace(year=current_year - 1)
            
            # Convert to ISO format
            return date_with_year.date().isoformat()
        except ValueError:
            # Return original string if parsing fails
            return date_str

    # Apply the conversion to the 'Date' column
    df['Date'] = df['Date'].apply(add_year_and_convert)
    
    # Convert the 'Date' column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    return df

def get_last_week(year,team):
    try:
        df = schedule_and_record(year,get_team_abbreviation(team))

        # Convert the 'Date' column to datetime
        df = convert_dates(df)
        #df['Date'] = pd.to_datetime(df['Date'], format='%A, %b %d')

        # Get today's date
        today = datetime.datetime.now().date()
        if today.year != year:
            print("you have chosen a year that isn't the current season, try again")
            exit()

        # Check if there are any dates after today
        future_dates = df[df['Date'].dt.date > today]

        if not future_dates.empty:
            print(f"There are {len(future_dates)} games scheduled after today.")

        # Find games in the last 7 days
        seven_days_ago = today - datetime.timedelta(days=7)
        recent_games = df[(df['Date'].dt.date <= today) & (df['Date'].dt.date > seven_days_ago)]

        # Count W's and L's
        wins = recent_games['W/L'].str.startswith('W').sum()
        losses = recent_games['W/L'].str.startswith('L').sum()

        return wins, losses
    except Exception as e:
        print(f"Error fetching schedule from pybaseball: {e}")
        return get_last_week_statsapi(year, team)
    
def get_last_week_statsapi(year, team):
    team_id = statsapi.lookup_team(team)[0]['id']
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=7)
    schedule = statsapi.schedule(start_date=start_date, end_date=end_date, team=team_id)
    wins = sum(1 for game in schedule if game['status'] == 'Final' and game['away_name'] == team and game['away_score'] > game['home_score'] or game['home_name'] == team and game['home_score'] > game['away_score'])
    losses = sum(1 for game in schedule if game['status'] == 'Final' and game['away_name'] == team and game['away_score'] < game['home_score'] or game['home_name'] == team and game['home_score'] < game['away_score'])
    return wins, losses

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
    #print(color_counts)
    
    # Get the top 3 most common colors
    main_colors = [color for color, _ in color_counts.most_common(3)]
    #print(len(main_colors), main_colors)
    
    # If we have fewer than 3 colors, add white or black
    if len(main_colors) < 2:
        main_colors.append("#000000")
        main_colors.append("#FFFFFF")
    if len(main_colors) < 3:
        if "#FFFFFF" not in main_colors:
            main_colors.append("#FFFFFF")  # white
        elif "#000000" not in main_colors:
            main_colors.append("#000000")  # black
        else:
            main_colors = ["#000000","#777777","#FFFFFF"]
    
    #print(main_colors)
    return main_colors[:3]

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

#def set_streamlit_colors(colors):
    #primary_color = colors[0]
    #secondary_color = colors[1]
    #background_color = colors[2]
    #print(colors)
    
    #st.markdown(f"""
    #<style>
    #.stApp {{
    #    background-color: {background_color};
    #}}
    #.stButton>button {{
    #    color: {secondary_color};
    #    background-color: {primary_color};
    #}}
    #.stTextInput>div>div>input {{
    #    color: {primary_color};
    #}}
    #/* Metric card styling */
    #div.css-1r6slb0.e1tzin5v2 {{
    #    background-color: {primary_color};
    #    border: 1px solid {primary_color};
    #    border-left: 0.5rem solid rgba(99, 99, 99, 0.2) !important;
    #    box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important;
    #    color: {background_color};
    #}}
    #div.css-1r6slb0.e1tzin5v2 {{
    #    border-left: 0.5rem solid rgba(99, 99, 99, 0.2) !important;
    #}}
    #label.css-mkogse.e16fv1kl2 {{
    #    color: {background_color} !important;
    #}}
    #div.css-1xarl3l.e16fv1kl1 {{
    #    color: {background_color};
    #}}
    #
    #div.css-1ht1j8u.e16fv1kl0 {{
    #    color: {secondary_color};
    #}}
    #</style>
    #""", unsafe_allow_html=True)

# Streamlit app
def main():
    # Set page config at the very beginning
    st.set_page_config(layout="wide", page_title="MLB Team Dashboard", page_icon="⚾", initial_sidebar_state="expanded")

    #load_bootstrap()

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
    #print(selected_team, selected_team_id)

    # Extract colors from the team logo SVG
    logo_url = f"https://www.mlbstatic.com/team-logos/team-cap-on-light/{selected_team_id}.svg"
    response = requests.get(logo_url)
    main_colors = []
    if response.status_code == 200:
        svg_content = response.text
        main_colors = extract_colors_from_svg(svg_content)
        if main_colors:
            pass
            #set_streamlit_colors(main_colors)
        else:
            main_colors = ['#777777','#000000','#FFFFFF']
            #set_streamlit_colors(main_colors)
    else:
        st.error(f"Failed to fetch logo: HTTP {response.status_code}")

    col1, col2 = st.columns((1,3))
    with col2:
        st.title(f"{selected_team} Team Dashboard")
    with col1:
        st.markdown(f"<img src={logo_url} height='100'>", unsafe_allow_html=True)
    

    # Get data
    team_data = get_team_data(year)
    #batting_data, pitching_data = get_player_data(year)
    standings_data = get_standings(year)
    last_week_data = get_last_week(year,selected_team)

    # Team-level KPIs
    #st.header(f"{selected_team} KPIs for {year}")

    # Find the row for the selected team
    team_row = standings_data[standings_data['Tm'] == selected_team]

    # Create three columns for metrics
    col1, col2, col3, col4 = st.columns((1,2,2,2))

    with col1:
        st.header(f"{year}")

    with col2:
         st.metric("Wins", int(team_row['W'].values[0]), delta = int(last_week_data[0]), help="The delta is for the last 7 days.")
#        st.metric("Run Differential", run_diff)
#        st.metric("Home Runs", hr)
#
    with col3:
        st.metric("Losses", int(team_row['L'].values[0]), delta = int(last_week_data[1]), help="The delta is for the last 7 days.", delta_color = "inverse")
#       st.metric("ERA", f"{era:.2f}")
#       st.metric("RBI", rbi)
#
    with col4:
        oldW = int(team_row['W'].values[0])-int(last_week_data[0])
        oldL = int(team_row['L'].values[0])-int(last_week_data[1])
        old_WLperc = (oldW)/(oldW+oldL)
        print(old_WLperc, int(team_row['W'].values[0]), int(last_week_data[0]), int(team_row['L'].values[0]), int(last_week_data[1]))
        delta_WLperc = float(team_row['W-L%'].values[0]) - float(old_WLperc)
        #print(old_WLperc, delta_WLperc)
        st.metric("Win %", team_row['W-L%'].values[0], delta = delta_WLperc, help="The delta is for the last 7 days.")
#        st.metric("OPS", f"{ops:.3f}")
#        st.metric("Fielding %", f"{fielding_pct:.3f}")

    style_metric_cards(background_color=main_colors[2],border_color=main_colors[0],border_left_color=main_colors[1],border_size_px=3)

    # Win-Loss Record
    st.subheader("Win-Loss Record")
    fig_wl = px.bar(standings_data, x='Tm', y=['W', 'L'], title="Win-Loss Record by Team",color_discrete_sequence=main_colors)
    st.plotly_chart(fig_wl)

    # Team Batting
    #st.subheader("Team Batting")
    #if 'OPS' in team_data.columns and 'R' in team_data.columns and 'HR' in team_data.columns:
    #    fig_batting = px.scatter(team_data, x='OPS', y='R', hover_name=team_data.index, 
    #                             size='HR', title="Team OPS vs Runs Scored")
    #    st.plotly_chart(fig_batting)
    #else:
    #    st.write("Required batting data not available for the selected year.")

    # Team Pitching
    #st.subheader("Team Pitching")
    #if 'ERA' in team_data.columns and 'WHIP' in team_data.columns and 'SO' in team_data.columns:
    #    fig_pitching = px.scatter(team_data, x='ERA', y='WHIP', hover_name=team_data.index, 
    #                              size='SO', title="Team ERA vs WHIP")
    #    st.plotly_chart(fig_pitching)
    #else:
    #    st.write("Required pitching data not available for the selected year.")

    # Player-level KPIs
    #st.header("Player-level KPIs")
    
    # Top Batters
    #st.subheader("Top Batters by OPS")
    #if 'OPS' in batting_data.columns:
    #    top_batters = batting_data.sort_values('OPS', ascending=False).head(10)
    #    fig_top_batters = px.bar(top_batters, x='Name', y='OPS', title="Top 10 Batters by OPS")
    #    st.plotly_chart(fig_top_batters)
    #else:
    #    st.write("OPS data not available for the selected year.")

    # Top Pitchers
    #st.subheader("Top Pitchers by ERA")
    #if 'ERA' in pitching_data.columns and 'IP' in pitching_data.columns:
    #    top_pitchers = pitching_data[pitching_data['IP'] > 50].sort_values('ERA').head(10)
    #    fig_top_pitchers = px.bar(top_pitchers, x='Name', y='ERA', title="Top 10 Pitchers by ERA (min 50 IP)")
    #    st.plotly_chart(fig_top_pitchers)
    #else:
    #    st.write("Required pitching data not available for the selected year.")

if __name__ == "__main__":
    main()
