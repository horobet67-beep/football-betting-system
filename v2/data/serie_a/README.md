# Serie A Data Setup

## Download Instructions

1. Go to: https://www.football-data.co.uk/italym.php

2. Download the following CSV files:
   - Season 2021-22: Click "Data" for I1 (Serie A)
   - Season 2022-23: Click "Data" for I1 (Serie A)
   - Season 2023-24: Click "Data" for I1 (Serie A)
   - Season 2024-25: Click "Data" for I1 (Serie A)

3. Save the files in this directory with these names:
   ```
   I1_2021-22.csv
   I1_2022-23.csv
   I1_2023-24.csv
   I1_2024-25.csv
   ```

## Quick Download (using curl)

```bash
cd /Users/iuliuscezar/VisualStudioProjects/SOCCER\ MLL/v2/data/serie_a

# Download last 4 seasons
curl -o I1_2021-22.csv "https://www.football-data.co.uk/mmz4281/2122/I1.csv"
curl -o I1_2022-23.csv "https://www.football-data.co.uk/mmz4281/2223/I1.csv"
curl -o I1_2023-24.csv "https://www.football-data.co.uk/mmz4281/2324/I1.csv"
curl -o I1_2024-25.csv "https://www.football-data.co.uk/mmz4281/2425/I1.csv"
```

## Data Format

The CSV files contain:
- Match results (FTHG, FTAG, FTR)
- Team names (HomeTeam, AwayTeam)
- Statistics: Corners (HC, AC), Cards (HY, AY, HR, AR)
- Betting odds from various bookmakers

## Testing

After downloading, test the adapter:
```bash
cd /Users/iuliuscezar/VisualStudioProjects/SOCCER\ MLL/v2
python3 data/serie_a_adapter.py
```

Test the predictor:
```bash
python3 simple_serie_a_predictor.py
```

## Serie A Characteristics

- **Defensive league:** Lower goals than other top leagues
- **Tactical fouls:** Many yellow cards (90%+ matches have cards)
- **Strong home advantage:** Home wins common
- **Under 2.5 goals:** Very profitable pattern
- **Cards patterns:** Most predictable in Serie A
