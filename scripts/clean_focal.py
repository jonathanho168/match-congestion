import pandas as pd
import glob

# 1) get the files
files = [f for start_year in range(2014, 2019)
         for f in glob.glob(f"../premierleague/{start_year}{start_year+1}.csv")]


# 2) read each, parse the Date column (dd/mm/yy), select the five cols
dfs = []
for fn in files:
    df = pd.read_csv(fn, parse_dates=["Date"], dayfirst=True)
    # keep only La Liga (Div == "SP1") just in case:
    # df = df[df["Div"] == "SP1"]

    dfs.append(df[["Date","HomeTeam","AwayTeam","FTHG","FTAG"]])

# 3) concatenate and write out
all_games = pd.concat(dfs, ignore_index=True)
all_games.to_csv("../results/premierleague_focal.csv", index=False)
print(f"Wrote {len(all_games)} rows to results/premierleague_focal.csv")
