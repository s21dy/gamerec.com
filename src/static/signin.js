import { initializeApp, getApps, getApp } from "https://www.gstatic.com/firebasejs/9.17.1/firebase-app.js";
import { getAuth, signInWithPopup, GoogleAuthProvider, signOut } from "https://www.gstatic.com/firebasejs/9.17.1/firebase-auth.js";

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyCLGh3nmJ1TgcGF-NciBSFCfZrLP7jWHZ4",
    authDomain: "gamerec-4907d.firebaseapp.com",
    projectId: "gamerec-4907d",
    storageBucket: "gamerec-4907d.firebasestorage.app",
    messagingSenderId: "819519893750",
    appId: "1:819519893750:web:27fcf57714fbe3d62bfcd7",
    measurementId: "G-1F0WZXXZSF"
};

// Initialize Firebase app (singleton pattern)
const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

// Utility functions for localStorage
const storage = {
    set: (key, value) => localStorage.setItem(key, JSON.stringify(value)),
    get: (key) => {
        const value = localStorage.getItem(key);
        try {
            return JSON.parse(value); // Try parsing as JSON
        } catch {
            return value; // Return as a string if parsing fails
        }
    },
    remove: (key) => localStorage.removeItem(key),
};

// Update UI based on login status
function updateUI(userId) {
    const loginBtn = document.getElementById("login-btn");
    const userInfo = document.getElementById("user-info");
    const userIcon = document.getElementById("user-icon");
    const userName = document.getElementById("user-name");

    if (userId) {
        loginBtn.style.display = "none";
        userInfo.style.display = "flex";
        userIcon.src = storage.get("userPhotoURL") || "";
        userName.textContent = storage.get("userName") || "";
    } else {
        loginBtn.style.display = "block";
        userInfo.style.display = "none";
    }
}

function resetLikeButtons() {
    const likeButtons = document.querySelectorAll(".like-btn");

    likeButtons.forEach((button) => {
        button.textContent = "❤️ Like"; // Default "unlike" text
        button.dataset.liked = "false"; // Update dataset to reflect "unlike" state
    });
}

// Fetch liked games from server
async function fetchLikedGames(userId) {
    try {
        const response = await fetch(`/api/get-saved-games?uid="${userId}"`);
        const data = await response.json();
        if (data.saved_games) {
            const uniqueGames = Array.from(new Set(data.saved_games));
            return uniqueGames;
        }
        return [];
    } catch (error) {
        console.error("Error fetching liked games:", error);
        return [];
    }
}

// Handle sign-in
async function handleSignIn() {
    try {
        const result = await signInWithPopup(auth, provider);
        const user = result.user;

        // Save user data to localStorage
        storage.set("userId", user.uid);
        storage.set("userName", user.displayName);
        storage.set("userPhotoURL", user.photoURL);

        const likedGames = await fetchLikedGames(user.uid);
        storage.set("likedGames", likedGames);
        console.log("Liked games synchronized:", likedGames);

        updateUI(user.uid);
    } catch (error) {
        console.error("Error during sign-in:", error);
    }
}

// Handle sign-out
async function handleSignOut() {
    try {
        await signOut(auth);

        // Clear user data from localStorage
        ["userId", "userName", "userPhotoURL", "likedGames"].forEach(storage.remove);

        updateUI(null);
        resetLikeButtons();
    } catch (error) {
        console.error("Error logging out:", error);
    }
}

// Initialize app
document.addEventListener("DOMContentLoaded", () => {
    const userId = storage.get("userId");
    updateUI(userId);

    // Event listeners for login and logout
    document.getElementById("login-btn").addEventListener("click", handleSignIn);
    document.getElementById("logout-btn").addEventListener("click", handleSignOut);
});
