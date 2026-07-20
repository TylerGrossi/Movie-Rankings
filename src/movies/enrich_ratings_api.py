"""
IMDb Ratings Enricher - FULL VERSION
====================================
Pulls data from BOTH OMDb and TMDB APIs for maximum features:

From OMDb:
- RT Score, Metascore, Box Office, Awards
- Actors, Director, Writer
- Plot, Rated, Language, Country

From TMDB:
- Keywords/Tags (revenge, twist ending, etc.)
- Production Companies (A24, Marvel, Pixar, etc.)
- Budget, Revenue
- TMDB Popularity, Vote Average, Vote Count

Requirements:
    pip install requests pandas openpyxl

Usage:
    1. Get OMDb API key: https://www.omdbapi.com/apikey.aspx
    2. Get TMDB API key: https://www.themoviedb.org/settings/api (free signup)
    3. Fill in keys below and run: python enrich_ratings_full.py
"""
import os
from dotenv import load_dotenv  # Add this import
from pathlib import Path
import re
import requests
import pandas as pd
import time

# Load variables from .env file
load_dotenv()

# Now we pull from the environment instead of typing them here
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

INPUT_CSV = "imdb_ratings.csv"
MOVIE_RANKS_FILE = "Movies Ranks.xlsm"
OUTPUT_CSV = "Ratings_Enriched.csv"
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(SCRIPT_DIR, INPUT_CSV)
MOVIE_RANKS_FILE = os.path.join(SCRIPT_DIR, MOVIE_RANKS_FILE)
OUTPUT_CSV = os.path.join(SCRIPT_DIR, OUTPUT_CSV)

# ============================================================
# OMDb API FUNCTIONS
# ============================================================

def get_omdb_data(imdb_id: str, api_key: str) -> dict:
    """Fetch movie data from OMDb API."""
    url = f"http://www.omdbapi.com/?i={imdb_id}&plot=full&apikey={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("Response") == "True":
            return data
        return None
    except Exception as e:
        print(f"    OMDb error: {e}")
        return None


def extract_rt_score(omdb_data: dict) -> str:
    if not omdb_data or "Ratings" not in omdb_data:
        return ""
    for rating in omdb_data["Ratings"]:
        if rating["Source"] == "Rotten Tomatoes":
            return rating["Value"].replace("%", "")
    return ""


def extract_metascore(omdb_data: dict) -> str:
    if not omdb_data:
        return ""
    score = omdb_data.get("Metascore", "")
    return "" if score == "N/A" else score


def extract_box_office(omdb_data: dict):
    if not omdb_data:
        return ""
    box = omdb_data.get("BoxOffice", "")
    if box == "N/A" or not box:
        return ""
    try:
        return int(box.replace("$", "").replace(",", ""))
    except:
        return ""


def extract_imdb_votes(omdb_data: dict):
    if not omdb_data:
        return ""
    votes = omdb_data.get("imdbVotes", "")
    if votes == "N/A" or not votes:
        return ""
    try:
        return int(votes.replace(",", ""))
    except:
        return ""


def extract_awards_info(omdb_data: dict) -> dict:
    result = {"oscar_wins": 0, "oscar_noms": 0, "total_wins": 0, "total_noms": 0}
    if not omdb_data:
        return result
    
    awards = omdb_data.get("Awards", "")
    if awards == "N/A" or not awards:
        return result
    
    oscar_win = re.search(r'Won (\d+) Oscar', awards)
    if oscar_win:
        result["oscar_wins"] = int(oscar_win.group(1))
    
    oscar_nom = re.search(r'Nominated for (\d+) Oscar', awards)
    if oscar_nom:
        result["oscar_noms"] = int(oscar_nom.group(1))
    
    wins = re.search(r'(\d+) win', awards)
    if wins:
        result["total_wins"] = int(wins.group(1))
    
    noms = re.search(r'(\d+) nomination', awards)
    if noms:
        result["total_noms"] = int(noms.group(1))
    
    return result


def extract_actors(omdb_data: dict) -> list:
    if not omdb_data or "Actors" not in omdb_data:
        return ["", "", "", ""]
    actors = omdb_data["Actors"]
    if actors == "N/A":
        return ["", "", "", ""]
    actor_list = [a.strip() for a in actors.split(",")]
    while len(actor_list) < 4:
        actor_list.append("")
    return actor_list[:4]


def extract_writers(omdb_data: dict) -> list:
    """Extract writers from OMDb data."""
    if not omdb_data or "Writer" not in omdb_data:
        return ["", ""]
    writers = omdb_data["Writer"]
    if writers == "N/A":
        return ["", ""]
    # Clean up writer names (remove parenthetical notes like "(screenplay)")
    writer_list = []
    for w in writers.split(","):
        # Remove anything in parentheses
        clean = re.sub(r'\([^)]*\)', '', w).strip()
        if clean:
            writer_list.append(clean)
    while len(writer_list) < 2:
        writer_list.append("")
    return writer_list[:2]


def extract_plot(omdb_data: dict) -> str:
    """Extract plot summary."""
    if not omdb_data:
        return ""
    plot = omdb_data.get("Plot", "")
    return "" if plot == "N/A" else plot


# ============================================================
# TMDB API FUNCTIONS
# ============================================================

def get_tmdb_id(imdb_id: str, api_key: str) -> int:
    """Convert IMDb ID to TMDB ID."""
    url = f"https://api.themoviedb.org/3/find/{imdb_id}?api_key={api_key}&external_source=imdb_id"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("movie_results"):
            return data["movie_results"][0]["id"]
        return None
    except:
        return None


def get_tmdb_data(tmdb_id: int, api_key: str) -> dict:
    """Fetch detailed movie data from TMDB."""
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}&append_to_response=keywords"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if "id" in data:
            return data
        return None
    except Exception as e:
        print(f"    TMDB error: {e}")
        return None


def extract_keywords(tmdb_data: dict) -> str:
    """Extract keywords/tags as comma-separated string."""
    if not tmdb_data or "keywords" not in tmdb_data:
        return ""
    keywords = tmdb_data["keywords"].get("keywords", [])
    keyword_names = [k["name"] for k in keywords[:10]]  # Top 10 keywords
    return ", ".join(keyword_names)


def extract_production_companies(tmdb_data: dict) -> list:
    """Extract production company names."""
    if not tmdb_data or "production_companies" not in tmdb_data:
        return ["", ""]
    companies = tmdb_data["production_companies"]
    company_names = [c["name"] for c in companies[:2]]  # Top 2 companies
    while len(company_names) < 2:
        company_names.append("")
    return company_names[:2]


def extract_tmdb_stats(tmdb_data: dict) -> dict:
    """Extract TMDB popularity, vote average, budget, revenue."""
    result = {
        "tmdb_popularity": "",
        "tmdb_vote_avg": "",
        "tmdb_vote_count": "",
        "budget": "",
        "revenue": ""
    }
    if not tmdb_data:
        return result
    
    result["tmdb_popularity"] = tmdb_data.get("popularity", "")
    result["tmdb_vote_avg"] = tmdb_data.get("vote_average", "")
    result["tmdb_vote_count"] = tmdb_data.get("vote_count", "")
    
    budget = tmdb_data.get("budget", 0)
    result["budget"] = budget if budget > 0 else ""
    
    revenue = tmdb_data.get("revenue", 0)
    result["revenue"] = revenue if revenue > 0 else ""
    
    return result


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def parse_genres(genre_string: str) -> list:
    if pd.isna(genre_string) or genre_string == "":
        return ["", "", ""]
    genres = [g.strip() for g in genre_string.split(",")]
    while len(genres) < 3:
        genres.append("")
    return genres[:3]


def get_first_director(directors: str) -> str:
    if pd.isna(directors) or directors == "":
        return ""
    return directors.split(",")[0].strip()


def normalize_title(title: str) -> str:
    t = str(title).strip().lower()
    if t.startswith("the "):
        t = t[4:]
    t = t.replace(" & ", " and ")
    t = t.replace("vol. ", "vol ")
    t = t.replace(".", "").replace(",", "").replace(":", "").replace("'", "")
    t = t.replace("  ", " ")
    return t.strip()


def load_movie_ranks(filepath: str) -> dict:
    print(f"Loading scores from {filepath}...")
    try:
        df = pd.read_excel(filepath, sheet_name="Movie Rankings")
        scores = {}
        for _, row in df.iterrows():
            title = str(row["Movie"]).strip().lower()
            score = row["Score"]
            scores[title] = score
            scores[normalize_title(title)] = score
        print(f"  Loaded {len(df)} movie scores")
        return scores
    except Exception as e:
        print(f"  Warning: Could not load Movie Rankings: {e}")
        return {}


# ============================================================
# MAIN ENRICHMENT FUNCTION
# ============================================================

def enrich_ratings(input_file: str, omdb_key: str, tmdb_key: str, ranks_file: str, output_file: str):
    """Main function to enrich ratings with OMDb + TMDB data."""
    
    my_scores = load_movie_ranks(ranks_file)
    
    # Check for existing output to resume
    existing_data = {}
    if Path(output_file).exists():
        print(f"\nFound existing {output_file} - resuming...")
        existing_df = pd.read_csv(output_file)
        for _, row in existing_df.iterrows():
            if pd.notna(row.get('RT')) and row.get('RT') != '':
                existing_data[row['IMDb_ID']] = row.to_dict()
        print(f"  Found {len(existing_data)} cached movies")
    
    print(f"\nReading {input_file}...")
    df = pd.read_csv(input_file)
    
    original_count = len(df)
    if "Title Type" in df.columns:
        df = df[df["Title Type"] == "Movie"].copy()
        print(f"Found {len(df)} movies (filtered {original_count - len(df)} TV)")
    
    # Initialize ALL columns
    new_cols = [
        "RT", "Metascore", "BoxOffice", "IMDb_Votes",
        "Oscar_Wins", "Oscar_Noms", "Total_Wins", "Total_Noms",
        "Rated", "Country", "Language",
        "Actor", "Actor 2", "Actor 3", "Actor 4",
        "Writer", "Writer 2", "Plot",
        "Keywords", "Prod_Company", "Prod_Company_2",
        "TMDB_Popularity", "TMDB_Vote_Avg", "TMDB_Vote_Count",
        "Budget", "Revenue", "My_Score"
    ]
    for col in new_cols:
        df[col] = ""
    
    # Set numeric defaults
    for col in ["Oscar_Wins", "Oscar_Noms", "Total_Wins", "Total_Noms"]:
        df[col] = 0
    
    total = len(df)
    skipped = 0
    omdb_failures = 0
    tmdb_failures = 0
    
    for idx, (i, row) in enumerate(df.iterrows()):
        imdb_id = row["Const"]
        title = row["Title"]
        
        # Check cache
        if imdb_id in existing_data:
            cached = existing_data[imdb_id]
            for col in new_cols:
                if col in cached:
                    df.at[i, col] = cached[col]
            skipped += 1
            print(f"[{idx + 1}/{total}] CACHED: {title}")
            continue
        
        print(f"[{idx + 1}/{total}] {title}...")
        
        # === OMDb API ===
        omdb_data = get_omdb_data(imdb_id, omdb_key)
        
        if omdb_data:
            df.at[i, "RT"] = extract_rt_score(omdb_data)
            df.at[i, "Metascore"] = extract_metascore(omdb_data)
            df.at[i, "BoxOffice"] = extract_box_office(omdb_data)
            df.at[i, "IMDb_Votes"] = extract_imdb_votes(omdb_data)
            
            awards = extract_awards_info(omdb_data)
            df.at[i, "Oscar_Wins"] = awards["oscar_wins"]
            df.at[i, "Oscar_Noms"] = awards["oscar_noms"]
            df.at[i, "Total_Wins"] = awards["total_wins"]
            df.at[i, "Total_Noms"] = awards["total_noms"]
            
            rated = omdb_data.get("Rated", "")
            df.at[i, "Rated"] = "" if rated == "N/A" else rated
            
            country = omdb_data.get("Country", "")
            df.at[i, "Country"] = "" if country == "N/A" else country.split(",")[0].strip()
            
            lang = omdb_data.get("Language", "")
            df.at[i, "Language"] = "" if lang == "N/A" else lang.split(",")[0].strip()
            
            actors = extract_actors(omdb_data)
            df.at[i, "Actor"] = actors[0]
            df.at[i, "Actor 2"] = actors[1]
            df.at[i, "Actor 3"] = actors[2]
            df.at[i, "Actor 4"] = actors[3]
            
            writers = extract_writers(omdb_data)
            df.at[i, "Writer"] = writers[0]
            df.at[i, "Writer 2"] = writers[1]
            
            df.at[i, "Plot"] = extract_plot(omdb_data)
            
            print(f"  OMDb ✓ RT:{df.at[i, 'RT']} Meta:{df.at[i, 'Metascore']}")
        else:
            omdb_failures += 1
            print(f"  OMDb ✗")
        
        # === TMDB API ===
        tmdb_id = get_tmdb_id(imdb_id, tmdb_key)
        
        if tmdb_id:
            tmdb_data = get_tmdb_data(tmdb_id, tmdb_key)
            
            if tmdb_data:
                df.at[i, "Keywords"] = extract_keywords(tmdb_data)
                
                companies = extract_production_companies(tmdb_data)
                df.at[i, "Prod_Company"] = companies[0]
                df.at[i, "Prod_Company_2"] = companies[1]
                
                stats = extract_tmdb_stats(tmdb_data)
                df.at[i, "TMDB_Popularity"] = stats["tmdb_popularity"]
                df.at[i, "TMDB_Vote_Avg"] = stats["tmdb_vote_avg"]
                df.at[i, "TMDB_Vote_Count"] = stats["tmdb_vote_count"]
                df.at[i, "Budget"] = stats["budget"]
                df.at[i, "Revenue"] = stats["revenue"]
                
                kw_preview = df.at[i, "Keywords"][:50] + "..." if len(str(df.at[i, "Keywords"])) > 50 else df.at[i, "Keywords"]
                print(f"  TMDB ✓ Keywords: {kw_preview}")
            else:
                tmdb_failures += 1
                print(f"  TMDB ✗ (no data)")
        else:
            tmdb_failures += 1
            print(f"  TMDB ✗ (no ID)")
        
        # Match personal score
        title_lower = title.strip().lower()
        title_normalized = normalize_title(title)
        
        if title_lower in my_scores:
            df.at[i, "My_Score"] = my_scores[title_lower]
            print(f"  ★ Score: {my_scores[title_lower]}")
        elif title_normalized in my_scores:
            df.at[i, "My_Score"] = my_scores[title_normalized]
            print(f"  ★ Score: {my_scores[title_normalized]}")
        
        # Small delay to respect rate limits
        time.sleep(0.15)
        
        # Save progress every 25 movies
        if (idx + 1) % 25 == 0:
            print(f"\n  [Saving progress... {idx + 1}/{total}]\n")
            _save_output(df, output_file)
    
    # Final save
    _save_output(df, output_file)
    
    print(f"\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"  Total movies: {len(df)}")
    print(f"  Cached (skipped): {skipped}")
    print(f"  OMDb failures: {omdb_failures}")
    print(f"  TMDB failures: {tmdb_failures}")
    print(f"  With RT scores: {(df['RT'] != '').sum()}")
    print(f"  With Keywords: {(df['Keywords'] != '').sum()}")
    print(f"  With your scores: {(df['My_Score'] != '').sum()}")


def _save_output(df, output_file):
    """Save current progress."""
    df["Genre1"] = df["Genres"].apply(lambda x: parse_genres(x)[0])
    df["Genre2"] = df["Genres"].apply(lambda x: parse_genres(x)[1])
    df["Genre3"] = df["Genres"].apply(lambda x: parse_genres(x)[2])
    df["Director"] = df["Directors"].apply(get_first_director)
    
    output_df = pd.DataFrame({
        "Movie": df["Title"],
        "IMDb": df["IMDb Rating"],
        "RT": df["RT"],
        "Metascore": df["Metascore"],
        "Runtime": df["Runtime (mins)"],
        "Year": df["Year"],
        "Genres": df["Genres"],
        "Genre1": df["Genre1"],
        "Genre2": df["Genre2"],
        "Genre3": df["Genre3"],
        "Director": df["Director"],
        "Actor": df["Actor"],
        "Actor 2": df["Actor 2"],
        "Actor 3": df["Actor 3"],
        "Actor 4": df["Actor 4"],
        "Writer": df["Writer"],
        "Writer 2": df["Writer 2"],
        "Plot": df["Plot"],
        "Rated": df["Rated"],
        "BoxOffice": df["BoxOffice"],
        "IMDb_Votes": df["IMDb_Votes"],
        "Oscar_Wins": df["Oscar_Wins"],
        "Oscar_Noms": df["Oscar_Noms"],
        "Total_Wins": df["Total_Wins"],
        "Total_Noms": df["Total_Noms"],
        "Country": df["Country"],
        "Language": df["Language"],
        "Keywords": df["Keywords"],
        "Prod_Company": df["Prod_Company"],
        "Prod_Company_2": df["Prod_Company_2"],
        "TMDB_Popularity": df["TMDB_Popularity"],
        "TMDB_Vote_Avg": df["TMDB_Vote_Avg"],
        "TMDB_Vote_Count": df["TMDB_Vote_Count"],
        "Budget": df["Budget"],
        "Revenue": df["Revenue"],
        "IMDb_ID": df["Const"],
        "My_Score": df["My_Score"]
    })
    
    output_df.to_csv(output_file, index=False)
    print(f"  ✓ Saved to: {output_file}")


if __name__ == "__main__":
    if OMDB_API_KEY == "YOUR_OMDB_KEY_HERE":
        print("ERROR: Set your OMDb API key!")
        exit(1)
    
    if TMDB_API_KEY == "YOUR_TMDB_KEY_HERE":
        print("ERROR: Set your TMDB API key!")
        print("Get one free at: https://www.themoviedb.org/settings/api")
        exit(1)
    
    if not Path(INPUT_CSV).exists():
        print(f"ERROR: {INPUT_CSV} not found")
        exit(1)
    
    enrich_ratings(INPUT_CSV, OMDB_API_KEY, TMDB_API_KEY, MOVIE_RANKS_FILE, OUTPUT_CSV)