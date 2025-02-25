# GameRec.com 🎮🔍

**GameRec.com** is an advanced game recommendation platform that helps users discover new games based on their unique preferences. Unlike Steam’s built-in recommendation system, which primarily relies on game tags and popularity, GameRec.com leverages a Machine Learning model powered by a **Compressed Sparse Row (CSR) matrix** to analyze deep relationships between games. This approach efficiently handles large-scale game-player interaction data, capturing nuanced similarities beyond traditional tag-based filtering. By applying collaborative filtering and content-based learning, GameRec.com delivers more personalized, data-driven recommendations, helping users find hidden gems that align with their gaming interests. The platform integrates with Steam API to fetch game details, provides an intuitive UI for seamless exploration, and allows users to sign in with Google to save and track their favorite games.

## 🌟 Features

- 🔍 **Search for games** and receive recommendations dynamically.
- 🎮 **Steam API Integration** – Fetch real-time game details.
- 🛠️ **Recommendation System** – Get personalized game suggestions.
- 🚀 **Interactive UI** – Seamless navigation and dynamic game listing.
- 🔐 **Google Authentication** – Save favorite games to your account.
- ❤️ **Like & Save Games** – Keep track of your favorite games.

## 📂 Project Structure

```php
GameRec/
├── auth.py               # Handles authentication (Firebase)
├── fetch_detail.py       # Retrieves game details
├── recommendation.py     # Game recommendation logic
├── youtube_call.py       # Fetches YouTube-related game content
├── main.py               # Main backend script (Flask API)
├── firebase-service-account.json  # Firebase credentials (DO NOT EXPOSE)
│
│── templates/
│   ├── index.html            # Main UI layout
│── statics/
│   ├── front-end.js          # Handles UI interactions
│   ├── scripts.js            # Handles game search & suggestions
│   ├── scripts-rec.js        # Manages recommendations
│   ├── signin.js             # Google Sign-In logic
│   ├── static/               # CSS & other assets
│
│── README.md                 # Project documentation
│── requirements.txt           # Python dependencies
│── .gitignore                 # Git ignored files (e.g., secrets, cache)
```

## 🚀 Getting Started

### 1️⃣ Clone the Repository
```sh
git clone https://github.com/s21dy/gamerec.com.git
cd gamerec.com
```

### 2️⃣ Backend Setup (Python)
Ensure you have Python 3.x installed, then set up a virtual environment:
```sh
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

### 3️⃣ API Keys & Firebase Setup
Steam API: Obtain a Steam API key from Steam Developer Portal and add it to your environment variables.
Firebase Authentication: Set up Firebase in your Firebase Console.
Store your Firebase credentials in `firebase-service-account.json` (Ensure this file is NOT committed to GitHub).

### 4️⃣ Run the Backend Server
``` sh
python main.py
```

### 5️⃣ Frontend Setup (HTML + JavaScript)
Simply open `index.html` in your browser, or serve it using a local server:
python -m http.server 8000

Then, visit `http://localhost:8000` in your browser.

📌 How It Works
1. User searches for a game ➝ The app queries Steam API.
2. Recommendations are fetched based on similar game tags.
3. User clicks a recommended game ➝ Loads detailed game info.
4. Sign in with Google to save liked games for future reference.

🔧 Dependencies
- Backend (Python & Flask)
  - Flask
  - Firebase Admin SDK
  - Requests
- Frontend (HTML, JavaScript)
  - Firebase Authentication
  - Steam API

Install dependencies using:
```sh
pip install -r requirements.txt
```

🛡 Security Notes
🚨 DO NOT expose your ```firebase-service-account.json``` or Steam API key publicly. Use `.gitignore` to exclude sensitive files.

📜 License
MIT License © 2025 Sandy Yang


