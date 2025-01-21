import os
from flask import Flask, render_template, request, jsonify
from recommendation import GameRecommender
from fetch_detail import scrape_game_details
from auth import verify_token, save_user_to_database
from sqlalchemy import create_engine
from flask_caching import Cache
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DB_PATH = os.path.join(BASE_DIR, "../data/processed/user.db")
os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)

GAMES_DB_PATH = os.getenv(
    "GAMES_DB_PATH", 
    "postgresql://game_ztiv_user:0dclW2K3zpb80TNxSuF85nBEi0YpdRxV@dpg-cu6qj3ogph6c73c97n6g-a.oregon-postgres.render.com/game_ztiv"
    )
game_engine = create_engine(GAMES_DB_PATH, pool_size=1000, max_overflow=20)

SIMILARITY_MATRIX_PATH = "../data/processed/similarity_matrix.npz"
os.makedirs(os.path.dirname(SIMILARITY_MATRIX_PATH), exist_ok=True)

# Flask app and caching
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

cache = Cache(app, config={"CACHE_TYPE": "simple"})

# Global recommender
recommender = None

def get_recommender():
    global recommender
    if recommender is None:
        logger.info("Initializing GameRecommender...")
        recommender = GameRecommender(
            db_engine=game_engine,
            similarity_matrix_path=SIMILARITY_MATRIX_PATH,
            top_k=30,
            n_components=200
        )
    if recommender.dataset is None:
        logger.info("Loading dataset...")
        recommender.load_dataset()  # Load when first accessed
    if recommender.similarity_matrix is None:
        logger.info("Loading similarity matrix...")
        recommender.load_similarity_matrix()  # Load when first accessed
    return recommender

@app.route("/", methods=["GET", "POST"])
@cache.cached(timeout=300)
def home():
    recommender = get_recommender()
    game_list = recommender.dataset['name'].unique().tolist()
    return render_template("index.html", games=game_list)

@app.route("/get-recommendations", methods=["GET"])
@cache.cached(timeout=300, query_string=True)
def get_recommendations():
    recommender = get_recommender()
    selected_game = request.args.get("game")
    if not selected_game:
        return jsonify({"error": "Game is required"}), 400
    
    items = recommender.get_recommendations(selected_game, top_n=15)
    if items.empty:
        return jsonify({"error": "No recommendations found"}), 404

    return jsonify(items.to_dict(orient="records"))

@app.route("/get-games", methods=["GET"])
@cache.cached(timeout=300)
def get_games():
    recommender = get_recommender()
    games = recommender.dataset['name'].unique().tolist()
    return jsonify(games)

@app.route("/get-game-details", methods=["GET"])
def get_game_details():
    game_id = request.args.get("id", "").strip()
    if not game_id:
        return jsonify({"error": "Game ID is required"}), 400

    try:
        game_data = scrape_game_details(game_id)
        return jsonify(game_data)
    except IndexError:
        return jsonify({"error": "Game not found"}), 404

@app.route("/api/verify-user", methods=["POST"])
def verify_user():
    data = request.json
    id_token = data.get("idToken")

    if not id_token:
        return jsonify({"error": "ID token is required"}), 400

    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired token"}), 401

    uid = decoded_token["uid"]
    email = decoded_token.get("email")
    save_user_to_database(uid, email)

    return jsonify({
        "message": "User verified successfully",
        "user": {"uid": uid, "email": email},
    })

def handle_sqlite_query(query, params=(), fetch_all=True):
    """
    Utility function to handle SQLite queries.
    """
    try:
        with sqlite3.connect(USER_DB_PATH) as conn:
            cursor = conn.execute(query, params)
            if fetch_all:
                return cursor.fetchall()
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        raise

@app.route("/api/add-game", methods=["POST"])
def add_game():
    data = request.json
    uid = data.get("uid")
    game_id = data.get("game_id")

    if not uid or not game_id:
        return jsonify({"error": "UID and game ID are required"}), 400

    try:
        handle_sqlite_query("INSERT INTO saved_games (uid, game_id) VALUES (?, ?)", (uid, game_id), fetch_all=False)
        return jsonify({"message": "Game saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Database error: {e}"}), 500

@app.route("/api/get-saved-games", methods=["GET"])
def get_saved_games():
    uid = request.args.get("uid")

    if not uid:
        return jsonify({"error": "UID is required"}), 400

    try:
        games = handle_sqlite_query("SELECT game_id FROM saved_games WHERE uid = ?", (uid,))
        return jsonify({"saved_games": [game[0] for game in games]}), 200
    except Exception as e:
        return jsonify({"error": f"Database error: {e}"}), 500

@app.route("/api/remove-game", methods=["DELETE"])
def remove_liked_game():
    data = request.json
    uid = data.get("uid")
    game_id = data.get("game_id")

    if not uid or not game_id:
        return jsonify({"error": "UID and game ID are required"}), 400

    try:
        handle_sqlite_query("DELETE FROM saved_games WHERE uid = ? AND game_id = ?", (uid, game_id), fetch_all=False)
        return jsonify({"message": "Game unliked successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Database error: {e}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000)) # remember to change to 5000 when push
    app.run(host="0.0.0.0", port=port)