import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
from recommendation import GameRecommender
from fetch_detail import scrape_game_details
from auth import verify_token, save_user_to_database
from sqlalchemy import create_engine, text


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

USER_DB_PATH = os.getenv(
    "USER_DB_PATH", 
    "postgresql://saved_games_user:0Dr4TmfmQCmCfWVUkJUiw7QHxhdgwAz7@dpg-cu7062l6l47c73c4moh0-a.oregon-postgres.render.com/saved_games"
    )
engine = create_engine(USER_DB_PATH, pool_size=10, max_overflow=20)

GAMES_DB_PATH = os.getenv(
    "GAMES_DB_PATH", 
    "postgresql://game_ztiv_user:0dclW2K3zpb80TNxSuF85nBEi0YpdRxV@dpg-cu6qj3ogph6c73c97n6g-a.oregon-postgres.render.com/game_ztiv"
    )
game_engine = create_engine(GAMES_DB_PATH, pool_size=1000, max_overflow=20)

SIMILARITY_MATRIX_PATH = "../data/processed/similarity_matrix.npz"
os.makedirs(os.path.dirname(SIMILARITY_MATRIX_PATH), exist_ok=True)


app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"),
             static_folder=os.path.join(BASE_DIR, "static"))

@app.route("/", methods=["GET", "POST"])
def home():
     game_list = recommender.load_dataset()['name'].unique().tolist()

     return render_template("index.html", games=game_list)

@app.route("/get-recommendations", methods=["GET"])
def get_recommendations():
    selected_game = request.args.get("game")
    if not selected_game:
        return jsonify({"error": "Game is required"}), 400
    
    items = recommender.get_recommendations(selected_game, top_n=15)
    if items.empty:
        return jsonify({"error": "No recommendations found"}), 404

    return jsonify(items.to_dict(orient="records"))

@app.route("/get-games", methods=["GET"])
def get_games():
    games = recommender.dataset['name'].unique().tolist()
    return jsonify(games)

@app.route("/get-game-details", methods=["GET"])
def get_game_details():
    # Get the game ID from the request arguments
    game_id = request.args.get("id").strip()
    if not game_id:
        return jsonify({"error": "Game ID is required"}), 400

    # Find the game details in your data
    try:
        game_data = scrape_game_details(game_id)
        return jsonify(game_data)
    except IndexError:
        return jsonify({"error": "Game not found"}), 404

@app.route("/api/verify-user", methods=["POST"])
def verify_user():
    """
    Verify the user's Firebase ID token and return user info.
    """
    data = request.json
    id_token = data.get("idToken")

    if not id_token:
        return jsonify({"error": "ID token is required"}), 400

    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired token"}), 401

    uid = decoded_token["uid"]
    email = decoded_token.get("email")
    
    # Optionally save user to database
    save_user_to_database(uid, email)

    return jsonify({
        "message": "User verified successfully",
        "user": {"uid": uid, "email": email},
    })

@app.route("/api/add-game", methods=["POST"])
def add_game():
    """
    Save a liked game for the signed-in user.
    """
    data = request.json
    uid = data.get("uid")
    game_id = data.get("game_id")

    if not uid or not game_id:
        return jsonify({"error": "UID {uid} and game ID {game_id} are required"}), 400

    try:
        query = text("INSERT INTO saved_games (uid, game_id) VALUES (:uid, :game_id)")
        with engine.connect() as conn:
            conn.execute(query, {"uid": uid, "game_id": game_id})
        return jsonify({"message": "Game saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Database error: {e}"}), 500

@app.route("/api/get-saved-games", methods=["GET"])
def get_saved_games():
    """
    Retrieve saved games for the signed-in user.
    """
    uid = request.args.get("uid")

    if not uid:
        return jsonify({"error": "UID is required"}), 400

    try:
        query = text("SELECT game_id FROM saved_games WHERE uid = :uid")
        with engine.connect() as conn:
            games = conn.execute(query, {"uid": uid}).fetchall()
        return jsonify({"saved_games": [game[0] for game in games]}), 200
    except Exception as e:
        return jsonify({"error": f"Database error: {e}"}), 500

@app.route("/api/remove-game", methods=["DELETE"])
def remove_liked_game():
    """
    Remove a liked game for the signed-in user.
    """
    data = request.json
    uid = data.get("uid")
    game_id = data.get("game_id")

    if not uid or not game_id:
        return jsonify({"error": "UID and game ID are required"}), 400

    try:
        query = text("DELETE FROM saved_games WHERE uid = :uid AND game_id = :game_id")
        with engine.connect() as conn:
            conn.execute(query, {"uid": uid, "game_id": game_id})
        return jsonify({"message": "Game unliked successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Database error: {e}"}), 500

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":  # Only initialize once
        recommender = GameRecommender(
            db_engine=game_engine,
            similarity_matrix_path=SIMILARITY_MATRIX_PATH,
            top_k=30,
            n_components=200
        )
        try:
            recommender.load_dataset()
            recommender.load_similarity_matrix()
        except Exception as e:
            print(f"Initialization failed: {e}")
            raise
    port = int(os.environ.get("PORT", 8001))  # Default to 5000
    app.run(host="0.0.0.0", port=port)