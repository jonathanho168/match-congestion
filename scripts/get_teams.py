import pandas as pd

# read CSV file
df = pd.read_csv('results/focal_results.csv')

# get unique teams from both columns
unique_teams = pd.unique(df[['HomeTeam', 'AwayTeam']].values.ravel())

# convert to df
teams_df = pd.DataFrame(unique_teams, columns=['Team'])

# save to CSV
teams_df.to_csv('results/unique_teams.csv', index=False)
