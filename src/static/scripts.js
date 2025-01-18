const input = document.getElementById("game");
const suggestionsBox = document.getElementById("suggestions");

// Fetch the games from the backend API
let games = [];
fetch("/get-games")
    .then(response => response.json())
    .then(data => {
        games = data; // Store the retrieved games list
        console.log("Fetched games success")
    })
    .catch(error => {
        console.error("Error fetching games:", error);
    });

input.addEventListener("input", function() {
    const query = this.value.toLowerCase();
    suggestionsBox.innerHTML = ""; // Clear previous suggestions

    if (query) {
        const filteredGames = games.filter(game => game.toLowerCase().includes(query));
        filteredGames.forEach(game => {
            const item = document.createElement("div");
            item.classList.add("suggestion-item");
            item.textContent = game;

            // Add click event to select the suggestion
            item.addEventListener("click", function() {
                input.value = game; // Set the input value
                suggestionsBox.innerHTML = ""; // Clear suggestions
            });
            suggestionsBox.appendChild(item);
        });
    }
});


// Function to fetch and display game details
function fetchGameDetails(gameId) {
    fetch(`/get-game-details?id=${gameId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to fetch game details");
            }
            return response.json();
        })
        .then(data => {
            // Example: Update the game details section dynamically
            const gameTitle = document.getElementById("game-title");
            const gameDescription = document.getElementById("game-description");
            const mediaContainer = document.getElementById("media-container");

            gameTitle.textContent = data.name;
            gameDescription.innerHTML = data.detailed_description;
            mediaData = data.media
            mediaData.forEach((media) => {
                const mediaItem = document.createElement("div");
                mediaItem.className = "media-item";
          
                if (media.type === "video") {
                  // Video
                  mediaItem.innerHTML = `
                    <a href="${media.video_link}" target="_blank">
                      <img src="${media.image_link}" alt="Video Thumbnail">
                    </a>
                    <p>Watch Video</p>
                  `;
                } else if (media.type === "screenshot") {
                  // Screenshot
                  mediaItem.innerHTML = `
                    <a href="${media.image_link}" target="_blank">
                      <img src="${media.image_link}" alt="Screenshot">
                    </a>
                    <p>View Screenshot</p>
                  `;
                }
            mediaContainer.appendChild(mediaItem);
            });

            // Make the details section visible
            const gameDetails = document.getElementById("game-details");
            gameDetails.classList.remove("hidden");
        })
        .catch(error => {
            console.error("Error fetching game details:", error);
        });
}

// Add a click event listener to recommendation items
document.querySelectorAll('.recommendation-item').forEach(item => {
    item.addEventListener('click', function () {
        const gameId = this.querySelector('a').href.split('/').pop(); // Extract game ID
        fetchGameDetails(gameId); 
    });
});
