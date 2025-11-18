#!/bin/bash
# Download Serie A data for last 4 seasons

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DATA_DIR="$SCRIPT_DIR/data/serie_a"

echo "🇮🇹 Downloading Serie A data..."
echo "Target directory: $DATA_DIR"
echo ""

mkdir -p "$DATA_DIR"
cd "$DATA_DIR"

# Download each season
echo "📥 Downloading 2021-22 season..."
curl -f -o I1_2021-22.csv "https://www.football-data.co.uk/mmz4281/2122/I1.csv" 2>/dev/null || echo "  ⚠️  Failed to download 2021-22"

echo "📥 Downloading 2022-23 season..."
curl -f -o I1_2022-23.csv "https://www.football-data.co.uk/mmz4281/2223/I1.csv" 2>/dev/null || echo "  ⚠️  Failed to download 2022-23"

echo "📥 Downloading 2023-24 season..."
curl -f -o I1_2023-24.csv "https://www.football-data.co.uk/mmz4281/2324/I1.csv" 2>/dev/null || echo "  ⚠️  Failed to download 2023-24"

echo "📥 Downloading 2024-25 season..."
curl -f -o I1_2024-25.csv "https://www.football-data.co.uk/mmz4281/2425/I1.csv" 2>/dev/null || echo "  ⚠️  Failed to download 2024-25"

echo ""
echo "✅ Download complete!"
echo ""
echo "📁 Files downloaded:"
ls -lh *.csv 2>/dev/null || echo "  ⚠️  No CSV files found"

echo ""
echo "🧪 Testing data load..."
cd "$SCRIPT_DIR"
python3 data/serie_a_adapter.py

echo ""
echo "🎯 Testing predictor..."
python3 simple_serie_a_predictor.py

echo ""
echo "✨ Serie A is ready to use!"
