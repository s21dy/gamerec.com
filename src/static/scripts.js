const input = document.getElementById("game");
const suggestionsBox = document.getElementById("suggestions");

// Fetch the games from the backend API
let games = [];
fetch("/get-games")
    .then(response => response.json())
    .then(data => {
        games = data; // Store the retrieved games list
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