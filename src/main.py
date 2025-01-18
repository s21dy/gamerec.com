import pandas as pd
from flask import Flask, render_template, request, jsonify
from recommendation import get_game_rec, p_data, similarity_matrix
from fetch_detail import scrape_game_details
from auth import verify_token, get_user_data, save_user_to_database

app = Flask(__name__, template_folder='/Users/sandyyang/my_data_science_project/src/templates',
            static_folder="/Users/sandyyang/my_data_science_project/src/static")

@app.route("/", methods=["GET", "POST"])
def home():
     selected_game = []
     items = pd.DataFrame()
     
     # Handle POST request when the user selects a game
     if request.method == "POST":
        selected_game = request.form.get("game") 
        items = get_game_rec(selected_game, p_data, similarity_matrix)

      # Get the game name from query parameters
     game_list = p_data['name'].unique().tolist()
     return render_template("index.html", 
                            games=game_list, 
                            items= items,
                            selected_game=selected_game)

@app.route("/get-games", methods=["GET"])
def get_games():
    games = p_data['name'].unique().tolist()
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


if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)