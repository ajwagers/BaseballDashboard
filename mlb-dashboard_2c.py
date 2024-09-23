import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from pybaseball import standings, team_batting, team_pitching, batting_stats_bref, pitching_stats_bref, schedule_and_record
import statsapi
import numpy as np
from streamlit_extras.metric_cards import style_metric_cards
import requests
import json
import base64
from pathlib import Path
import datetime
import re
import math
from collections import Counter

#pybaseball scrapes data from:  https://www.baseball-reference.com/, https://baseballsavant.mlb.com/, and https://www.fangraphs.com/.

hide_streamlit_style = """
<style>
    #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 2.6rem;}
</style>
"""

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

bat_stat_dict = {
    "TG": "Total Games",
    "G": "Games Played",
    "AB": "At Bats",
    "PA": "Plate Appearances",
    "H": "Hits",
    "1B": "Singles",
    "2B": "Doubles",
    "3B": "Triples",
    "HR": "Home Run",
    "R": "Runs",
    "RBI": "Runs Batted In",
    "BB": "Walks",
    "IBB": "Intential Walks",
    "SO": "Strikeouts",
    "HBP": "Hit By Pitch",
    "SF": "Sacrifice Fly",
    "SH": "Sacrifice Hit",
    "GDP": "Ground to Double Play",
    "SB": "Stolen Bases",
    "CS": "Caught Stealing",
    "BB%": "Walk Percentage",
    "K%": "Strikeout Percentage",
    "BB/K": "Walk to Strikeout Ratio",
    "ISO": "Isolated Power (SLG-AVG)",
    "BAIP": "Batting Average on Balls in Play",
    "AVG": "Batting Average",
    "OBP": "On Base Percentage",
    "SLG": "Slugging Percentage",
    "OPS": "On Base + Slugging Percentage",
    "Spd": "Speed Score",
    "UBR": "Ultimate Base Running",
    "wGDP": "Ground to Double Play Abave Average",
    "XBR": "Statcast baserunning average",
    "wSB": "Stolen Base and Caught Stealing above average",
    "wOBA": "Weighted On Base Average",
    "wRC": "Runs Created in terms of wOBA",
    "wRAA": "Runs Above Average from  wOBA",
    "wRC+": "Runs per Plate Appearance where 100 is average",
    "GB/FB": "Ground Ball to Fly Ball Ratio",
    "LD%": "Line Drive Percentage",
    "GB%": "Ground Ball Percentage",
    "FB%": "Fly Ball Percentage",
    "IFFB%": "Infield Fly Ball Percentage",
    "HR/FB": "Home Run to Fly Ball Ratio",
    "IFH": "Infield Hits",
    "IFH%": "Infield Hit Percentage",
    "BUH": "Bunt Hits",
    "BUH%": "Bunt Hit Percentage",
    "Pull%": "Percentage of Balls Pulled into Play",
    "Cent%": "Percentage of Balls Hit to Centerfield",
    "Oppo%": "Percentage of Balls Hit to the Opposite Field",
    "Soft%": "Percentage of Balls Hit with a soft speed",
    "Med%": "Percentage of Balls Hit with a Medium Speed",
    "Hard%": "Percentage of Balls Hit with a Hard Speed",
    "WPA": "Win Probability Added",
    "-WPA": "Loss Advancement",
    "+WPA": "Win Advancement",
    "RE24": "Runs above average based on 24 run/out states",
    "REW": "Wins above average based on 24 run/out states",
    "pLI": "Average Leverage Index",
    "phLI": "Average Leverage Index while pinch hitting",
    "PH": "Pinch Hitting Opportunities",
    "WPA/LI": "Situational Wins",
    "Clutch": "Performance Under Pressure",
    "Batting": "Park adjusted runs above average based on wOBA",
    "Base Running": "Base Running Runs Above Average, includes SB and CS.",
    "Fielding": "Fielding Runs Above Average based on UZR",
    "Positional": "Positional Adjustments",
    "League": "League adjustment to zero out wins above average",
    "Replacement": "Replacement Runs",
    "BsR": "Base Running Runs Above Average",
    "Off": "Offense - Batting and Base Running Above Average",
    "Def": "Defebse - Fielding and Positional Adjustment",
    "RAR": "Runs Above Replacement",
    "WAR": "Wins Above Replacement",
    "Dollars": "WAR convert to dollars based on free agency",
    "Events": "Number of batted balls (PA - SO - BB - HBP)",
    "EV": "Exit Velocity (mph), speed as the ball comes off the bat",
    "maxEV": "maximum Exit Velocity",
    "LA": "Launch Angle",
    "Barrels": "Hit type that could lead to .500 batting average",
    "Barrels": "Percentage of hits that are Barrels",
    "HardHit": "Number of hits with an exit velocity of 95mph",
    "HardHit%": "Percentage of hits that are hard hits",
    "PPTV": "Pitcher Pitch Timer Violation",
    "CPTV": "Catcher Pitch Timer Violation",
    "DGV": "Disengagement Violation",
    "DSV": "Defensive Shift Violation",
    "BPTV": "Batter Pitch Timer Violation",
    "BTV": "Batter Timeout Violation",
    "EBV": "Total Balls by Violation",
    "ESV": "Total Strikes by Violation",
    "wTeamV": "Total Run Value of Violations Commited by the Player/Team",
    "wOppTeamV": "Total Run Value of Violations Commited by the Opposing Player/Team",
    "wNetPitV / wNetBatV": "Total Net Run Value for Player/Team"
}

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
        #print(pitching.columns)
        pitching = pitching.rename(columns={"R":"RA"})
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
    #print(standings_data)

    # Regular expression to match each team's data
    team_pattern = re.compile(r'(\d+)\s+([\w\s.]+)\s+(\d+)\s+(\d+)\s+([-\d.]+)\s+(\d+)\s+(\d+)\s+([-\d.]+)\s+(\d+)')
    
    # Regular expression to match division names
    division_pattern = re.compile(r'(American|National) League (East|West|Central)')
    
    all_teams = []
    current_division = ""

    for line in standings_data.split('\n'):
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
        if math.isnan(recent_games.iloc[[-1]]['Streak']):
            streak = recent_games.iloc[[-2]]['Streak']
        else:
            streak = recent_games.iloc[[-1]]['Streak'] 
        print(streak)
        return wins, losses, streak
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

# Streamlit app
def main():
    # Set page config at the very beginning
    st.set_page_config(layout="wide", page_title="MLB Team Dashboard", page_icon="⚾", initial_sidebar_state="collapsed")

    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

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

    alt_main_colors = ['#D3D3D3' if color.lower() == '#ffffff' else color for color in main_colors]

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

    #col_names = team_data.columns 
    #for names in col_names:
    #    if names == 'RA':
    #        print(names)
    #print(team_data.head())

    # Team-level KPIs
    #st.header(f"{selected_team} KPIs for {year}")

    # Find the row for the selected team
    team_row = standings_data[standings_data['Tm'] == selected_team]
    team_abv = next(k for k, v in mlb_teams.items() if v == selected_team)
    #print(team_abv)
    #print(team_data.index)
    team_data_row = team_data[team_data.index == team_abv]

    # Create three columns for metrics
    col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns((2,2,2,2,2,2,2,2,2,2))

    with col1:
        st.header(f"{year}")

    with col2:
        st.metric("Wins", int(team_row['W'].values[0]), delta = int(last_week_data[0]), help="The delta is for the last 7 days.")
        
    with col3:
        st.metric("Losses", int(team_row['L'].values[0]), delta = int(last_week_data[1]), help="The delta is for the last 7 days.", delta_color = "inverse")
        #       st.metric("RBI", rbi)
#
    with col4:
        oldW = int(team_row['W'].values[0])-int(last_week_data[0])
        oldL = int(team_row['L'].values[0])-int(last_week_data[1])
        old_WLperc = (oldW)/(oldW+oldL)
        #print(old_WLperc, int(team_row['W'].values[0]), int(last_week_data[0]), int(team_row['L'].values[0]), int(last_week_data[1]))
        delta_WLperc = float(team_row['W-L%'].values[0]) - float(old_WLperc)
        print(old_WLperc, delta_WLperc)
        st.metric("Win %", team_row['W-L%'].values[0], delta = "{:.3f}".format(delta_WLperc), help="The delta is for the last 7 days.")
#        st.metric("Fielding %", f"{fielding_pct:.3f}")

    with col5:
        st.metric("Streak", last_week_data[2])
    
    with col6:
        st.metric("Games Behind", team_row['GB'].values[0], delta=None)

    with col7:
        if team_row['E#'].values[0] == 'E':
            elim_help="Team is Eliminated from Division Contention"
        elif team_row['E#'].values[0] == '☠':
            elim_help="Team is Eliminated from Playoff Contention"
        else:
            elim_help="Number of wins/loses to be eliminated."

        #print(team_row["E#"].values[0])
        st.metric("Elim. #", team_row['E#'].values[0], delta= None, help=elim_help)
        
    with col8:
        run_diff = team_data_row['R'] - team_data_row['RA']
        st.metric("Run Differential", run_diff, delta=None)

    with col9:
        st.metric("WAR", team_data_row['WAR'], delta=None)

    with col10:
        st.metric("Batting Ave.", team_data_row["AVG"], delta = None)



    style_metric_cards(background_color=main_colors[2],border_color=main_colors[0],border_left_color=main_colors[1],border_size_px=3)

    col1, col2, col3 = st.columns((1,1,1))

    with col1:
        # Win-Loss Record
        #st.subheader("Win-Loss Record")
        schedule_df = schedule_and_record(year,get_team_abbreviation(selected_team))
        schedule_df = convert_dates(schedule_df)
        # Find the index of the first row where the 'Date' matches today's date
        today_index = schedule_df[schedule_df['Date'].dt.date == datetime.datetime.now().date()].index[0]
        # Select rows from the first row to the row with today's date
        schedule_df = schedule_df.loc[:today_index]
        # First, let's create columns for wins and losses
        schedule_df['Win'] = np.where(schedule_df['W/L'] == 'W', 1, 0)
        schedule_df['Loss'] = np.where(schedule_df['W/L'] == 'L', 1, 0)
        # Now, let's create the cumulative columns
        schedule_df['Cumulative_Wins'] = schedule_df['Win'].cumsum()
        schedule_df['Cumulative_Losses'] = schedule_df['Loss'].cumsum()
        # Minimalist style settings
        sns.set(style="white", palette="muted")
        # Create a figure with 2 subplots arranged in a column
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
        # Plot Cumulative Wins and Losses on the first axis (ax1)
        sns.lineplot(x='Date', y='Cumulative_Wins', data=schedule_df, ax=ax1, label="Cumulative Wins", color=alt_main_colors[0])
        sns.lineplot(x='Date', y='Cumulative_Losses', data=schedule_df, ax=ax1, label="Cumulative Losses", color=alt_main_colors[1])
        # Remove unnecessary chart elements for a minimalist look
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.grid(False)  # Remove grid lines
        ax1.set_ylabel("Wins/Losses")
        ax1.set_title("Cumulative Wins & Losses Over Time")
        ax1.legend(loc="upper left")
        # Plot Attendance on the second axis (ax2)
        sns.lineplot(x='Date', y='Attendance', data=schedule_df, ax=ax2, label="Attendance", color=alt_main_colors[0])
        # Minimalist style for the second graph
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.grid(False)  # Remove grid lines
        ax2.set_ylabel("Attendance")    
        ax2.set_title("Attendance Over Time")
        # Adjust layout
        plt.tight_layout()
        # Display the plot
        plt.show()
        st.pyplot(fig)

    with col2:
        metrics = ['AVG', 'OBP', 'SLG']
        values = [team_data_row['AVG'].values[0], team_data_row['OBP'].values[0], team_data_row['SLG'].values[0]]        
        labels = ['AVG (' + str(team_data_row['AVG'].values[0]) + ')', 'OBP (' + str(team_data_row['OBP'].values[0]) +')', 'SLG ('+str(team_data_row['SLG'].values[0])+')']
        # Create a pie chart
        fig3, ax4 = plt.subplots()
        ax4.pie(values, labels=labels, startangle=90, colors = alt_main_colors)
        # Equal aspect ratio ensures the pie chart is circular.
        ax4.axis('equal')
        # Set the title
        plt.title('Batting Metrics Distribution (AVG, OBP, SLG)')
        # Show the plot
        plt.show()
        st.pyplot(fig3)

    with col3:
        # Define the metrics and their values
        metrics = ['ERA', 'FIP', 'WHIP']
        values = [team_data_row['ERA'].values[0], team_data_row['FIP'].values[0], team_data_row['WHIP'].values[0]]        
        labels = ['ERA (' + str(team_data_row['ERA'].values[0]) + ')', 'FIP (' + str(team_data_row['FIP'].values[0]) +')', 'WHIP ('+str(team_data_row['WHIP'].values[0])+')']
        # Create a pie chart
        fig2, ax3 = plt.subplots()
        ax3.pie(values, labels=labels, startangle=90, colors = alt_main_colors)
        # Equal aspect ratio ensures the pie chart is circular.
        ax3.axis('equal')
        # Set the title
        plt.title('Pitching Metrics Distribution (ERA, FIP, WHIP)')
        # Show the plot
        plt.show()
        st.pyplot(fig2)

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
