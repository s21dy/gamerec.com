import { initializeApp } from "https://www.gstatic.com/firebasejs/9.17.1/firebase-app.js";
import { getAuth, signInWithPopup, GoogleAuthProvider } from "https://www.gstatic.com/firebasejs/9.17.1/firebase-auth.js";

const firebaseConfig = {
    apiKey: "AIzaSyCLGh3nmJ1TgcGF-NciBSFCfZrLP7jWHZ4",
    authDomain: "gamerec-4907d.firebaseapp.com",
    projectId: "gamerec-4907d",
    storageBucket: "gamerec-4907d.firebasestorage.app",
    messagingSenderId: "819519893750",
    appId: "1:819519893750:web:27fcf57714fbe3d62bfcd7",
    measurementId: "G-1F0WZXXZSF"
  };

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

document.addEventListener("DOMContentLoaded", function () {
    const userId = localStorage.getItem("userId"); 

    // Function to update the UI based on user login status
    function updateUIForUser(userId) {
        const loginBtn = document.getElementById("login-btn");
        const userIcon = document.getElementById("user-icon");
        const userName = document.getElementById("user-name");
        const userInfo = document.getElementById("user-info");

        if (userId) {
            // User is signed in, hide login button and show user info
            loginBtn.style.display = "none";
            userIcon.src = localStorage.getItem("userPhotoURL") || ""; 
            userName.textContent = localStorage.getItem("userName") || ""; 
            userInfo.style.display = "flex";
        } else {
            // User is not signed in, show login button and hide user info
            loginBtn.style.display = "block";
            userInfo.style.display = "none";
        }
    }

    // Call updateUIForUser on page load
    updateUIForUser(userId);

    // Handle Google Sign-In
    document.getElementById("login-btn").addEventListener("click", () => {
        signInWithPopup(auth, provider)
            .then((result) => {
                const user = result.user;

                // Save user data in localStorage
                localStorage.setItem("userId", user.uid);
                localStorage.setItem("userName", user.displayName);
                localStorage.setItem("userPhotoURL", user.photoURL);

                // Update the UI after sign-in
                updateUIForUser(user.uid);
            })
            .catch((error) => {
                console.error("Error during sign-in:", error);
            });
    });
});
