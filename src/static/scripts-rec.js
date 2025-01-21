const recommendationList = document.getElementById("recommendation-list");
const searchBtn = document.getElementById("search-btn");

searchBtn.addEventListener("click", function () {
    fetchRecommendations(document.getElementById("game").value);
})   


function fetchRecommendations(selectedGame) {
    fetch(`/get-recommendations?game=${encodeURIComponent(selectedGame)}`)
        .then(response => {
            if (!response.ok) throw new Error("Failed to fetch recommendations");
            return response.json();
        })
        .then(data => {
            recommendationList.innerHTML = ""; // Clear old recommendations

            data.forEach(item => {
                const recommendationItem = document.createElement("div");
                recommendationItem.classList.add("recommendation-item");

                recommendationItem.innerHTML = `
                    <a href="https://store.steampowered.com/app/${item.id}" target="_blank" data-game-id="${item.id}">
                        <img src="https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/${item.id}/header.jpg" alt="${item.name}">
                        <p>${item.name}</p>
                    </a>
                `;
                // Attach event listener to the recommendation item
                recommendationItem.querySelector("img").addEventListener("click", function (e) {
                    e.preventDefault();
                    loadGameDetails(item.id); // Load the details of the clicked game
                });

                recommendationList.appendChild(recommendationItem);
            });
        })
        .catch(error => {
            console.error("Error fetching recommendations:", error);
            recommendationList.innerHTML = `<p>Error fetching recommendations</p>`;
        });
}

function loadGameDetails(gameId) {
    const gameDetails = document.getElementById("game-details");
    const gameTitle = document.getElementById("game-title");
    const gameDescription = document.getElementById("game-description");
    const mediaContainer = document.getElementById("media-container");
    const likeContainer = document.getElementById("like-container");

    // Clear previous details
    gameTitle.textContent = "";
    gameDescription.innerHTML = "";
    mediaContainer.innerHTML = "";
    likeContainer.innerHTML = "";

    fetch(`/get-game-details?id=${gameId}`)
        .then(response => {
            if (!response.ok) throw new Error(`Failed to fetch game details for gameId: ${gameId}`);
            return response.json();
        })
        .then(data => {
            // Update game details
            gameTitle.textContent = data.name;
            gameDescription.innerHTML = data.detailed_description;

            // Add media items
            data.media.forEach(media => {
                const mediaItem = createMediaElement(media);
                mediaContainer.appendChild(mediaItem);
            });

            // Handle like button logic
            const userId = localStorage.getItem("userId");
            if (userId) {
                attachLikeButtonListeners(gameId);
            } else {
                likeContainer.innerHTML = "<p>Sign in to save this game.</p>";
            }
            gameDetails.classList.remove("hidden");

        })
        .catch(error => console.error("Error loading game details:", error));
}


const createMediaElement = (media) => {
    const mediaItem = document.createElement("div");
    mediaItem.className = "media-item";

    if (media.type === "video") {
        const videoElement = document.createElement("video");
        videoElement.src = media.video_link;
        videoElement.autoplay = true;
        videoElement.muted = true;
        videoElement.controls = true;
        mediaItem.appendChild(videoElement);
    } else if (media.type === "screenshot") {
        const imgElement = document.createElement("img");
        imgElement.src = media.image_link;
        imgElement.alt = "Screenshot";
        mediaItem.appendChild(imgElement);
    }
    return mediaItem;
};

const updateCenterState = (mediaItems, currentIndex) => {
    mediaItems.forEach((item, index) => {
        const video = item.querySelector("video");
        if (index === currentIndex) {
            item.classList.add("centered");
        } else {
            item.classList.remove("centered");
        }
    });
};
const setupInfiniteSlider = (mediaItems) => {
    const items = [...mediaItems]; // Spread operator to convert NodeList to an array

    // Clone the first and last items for seamless looping
    const firstClones = items.map(cloneMediaItem);
    const lastClones = items.map(cloneMediaItem);

    // Append clones to the start and end
    firstClones.forEach(clone => mediaContainer.appendChild(clone));
    lastClones.reverse().forEach(clone => mediaContainer.insertBefore(clone, mediaContainer.firstChild));

    // Center the first real item instantly
    const realItemsStartIndex = lastClones.length;
    mediaContainer.scrollLeft = realItemsStartIndex * items[0].offsetWidth;

    return { realItemsStartIndex, realItemsEndIndex: realItemsStartIndex + items.length - 1 };
};

// Helper function to clone media items (repeated code abstraction)
const cloneMediaItem = (item) => {
    const clone = item.cloneNode(true);
    const video = clone.querySelector("video");
    if (video) {
        video.muted = true;  // Ensure videos in clones are muted
        video.setAttribute("muted", ""); // For consistency in attributes
    }
    return clone;
};

// Optimized sliding to the next media item
const slideToNext = (mediaItems, currentIndex, realItemsStartIndex, realItemsEndIndex) => {
    const totalItems = mediaItems.length;
    currentIndex = (currentIndex + 1) % totalItems;

    // Scroll into view the next item
    mediaItems[currentIndex].scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });

    // Reset scroll position when looping back to clones
    if (currentIndex === 0) {
        setTimeout(() => {
            mediaContainer.scrollLeft = realItemsStartIndex * mediaItems[0].offsetWidth;
            currentIndex = realItemsStartIndex;
        }, 300); // Allow smooth scrolling to finish
    } else if (currentIndex === totalItems - 1) {
        setTimeout(() => {
            mediaContainer.scrollLeft = realItemsEndIndex * mediaItems[0].offsetWidth;
            currentIndex = realItemsEndIndex;
        }, 300);
    }

    updateCenterState(mediaItems, currentIndex);
    return currentIndex;
};

function attachLikeButtonListeners(gameId) {
    const userId = localStorage.getItem("userId");

    if (!userId) {
        console.warn("User not signed in. Redirecting to Google Sign-In...");
        document.getElementById("login-btn").click();
        return;
    }

    // Update the button based on the latest cache
    updateLikeButton(gameId, userId);
}

function updateLikeButton(gameId, userId) {
    const likeContainer = document.querySelector(".like-container");

    // Fetch the latest likedGames from localStorage
    const likedGames = JSON.parse(localStorage.getItem("likedGames")) || [];

    // Clear the container's content
    likeContainer.innerHTML = "";

    // Create the like button
    const likeButton = document.createElement("button");
    likeButton.classList.add("like-btn");
    likeButton.dataset.gameId = gameId;
    
    // Check if the game is liked
    const isLiked = likedGames.includes(gameId.toString());
    likeButton.textContent = isLiked ? "❤️ Already in your list" : "❤️ Like";
    likeButton.dataset.liked = isLiked.toString();

    // Attach click listener for toggling like/unlike
    likeButton.addEventListener("click", (event) => {
        const currentState = event.target.dataset.liked === "true";

        toggleLikeState(currentState, userId, gameId)
            .then(() => {
                // Refresh the button dynamically after toggling the state
                updateLikeButton(gameId, userId);
            })
            .catch((error) => console.error("Error toggling like state:", error));
    });

    likeContainer.appendChild(likeButton);
}

function toggleLikeState(isLiked, userId, gameId) {
    const endpoint = isLiked ? "/api/remove-game" : "/api/add-game";
    const method = isLiked ? "DELETE" : "POST";

    return fetch(endpoint, {
        method: method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uid: userId, game_id: gameId }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.message) {
                const likedGames = JSON.parse(localStorage.getItem("likedGames")) || [];
                if (isLiked) {
                    // Remove the game from likedGames
                    console.log("Remove: ", gameId)
                    const index = likedGames.indexOf(gameId.toString());
                    if (index !== -1) likedGames.splice(index, 1);
                } else {
                    // Add the game to likedGames
                    console.log("Add: ", gameId)
                    likedGames.push(gameId.toString());
                }
                localStorage.setItem("likedGames", JSON.stringify(likedGames));
            } else {
                console.error(data.error);
                throw new Error(data.error);
            }
        });
}
