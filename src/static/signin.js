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

// Handle Google Sign-In
document.getElementById("login-btn").addEventListener("click", () => {
    signInWithPopup(auth, provider)
        .then((result) => {
            const user = result.user;

            // Update the user icon and name
            const userIcon = document.getElementById("user-icon");
            const userName = document.getElementById("user-name");
            const userInfo = document.getElementById("user-info");

            // Make the user-info section visible
            userIcon.src = user.photoURL; 
            userName.textContent = user.displayName;
            userInfo.style.display = "flex";
            localStorage.setItem("userId", user.uid);
            //Hide the login button
            document.getElementById("login-btn").style.display = "none";
        })
        .catch((error) => {
            console.error("Error during sign-in:", error);
        });
});

