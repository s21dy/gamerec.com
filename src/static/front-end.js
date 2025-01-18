document.addEventListener("DOMContentLoaded", function () {
    const container = document.querySelector('.recommendation-list');

    function scrollLeft() {
        if (container) {
            container.scrollBy({
                top: 0,
                left: -300, // Adjust scroll amount
                behavior: 'smooth',
            });
        } else {
            console.error("Recommendation container not found.");
        }
    }
    function scrollRight() {
        if (container) {
            container.scrollBy({
                top: 0,
                left: 300, // Adjust scroll amount
                behavior: 'smooth',
            });
        } else {
            console.error("Recommendation container not found.");
        }
    }

    // Attach these functions to your buttons
    document.querySelector('.nav.left').addEventListener('click', scrollLeft);
    document.querySelector('.nav.right').addEventListener('click', scrollRight);
});


//Event Listener for game detail section
document.addEventListener("DOMContentLoaded", () => {
    const gameDetails = document.getElementById("game-details");
    const gameTitle = document.getElementById("game-title");
    const gameDescription = document.getElementById("game-description");
    const mediaContainer = document.getElementById("media-container");

    let autoSlideInterval;

    // Helper function to create media elements
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

    // Function to update the centered state and video autoplay
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

    // Optimized setup for infinite slider
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

    // Optimized function to load game details and media content
    const loadGameDetails = (gameId) => {
        gameTitle.textContent = "";
        gameDescription.innerHTML = "";
        mediaContainer.innerHTML = ""; // Clear previous media content

        mediaContainer.style.visibility = "hidden"; // Hide the slider temporarily

        fetch(`/get-game-details?id=${gameId}`)
            .then((response) => response.json())
            .then((data) => {
                // Update game details
                gameTitle.textContent = data.name;
                gameDescription.innerHTML = data.detailed_description;

                // Populate media content
                data.media.forEach((media) => {
                    const mediaItem = createMediaElement(media);
                    mediaContainer.appendChild(mediaItem);
                });

                // Setup infinite slider
                const mediaItems = [...document.querySelectorAll(".media-item")];
                const { realItemsStartIndex, realItemsEndIndex } = setupInfiniteSlider(mediaItems);
                let currentIndex = realItemsStartIndex;

                updateCenterState(mediaItems, currentIndex); // Center the first real item

                // Show the slider after centering
                mediaContainer.style.visibility = "visible";

                const slideToNextWrapper = () => {
                    currentIndex = slideToNext(mediaItems, currentIndex, realItemsStartIndex, realItemsEndIndex);
                };

                clearInterval(autoSlideInterval); // Clear any previous interval
                autoSlideInterval = setInterval(slideToNextWrapper, 30000); // Auto-slide every 7 seconds

                gameDetails.classList.remove("hidden");
            })
            .catch((error) => console.error("Error fetching game details:", error));
    };

    // Attach click event listeners to recommendation items
    document.querySelectorAll(".recommendation-item").forEach((item) => {
        item.addEventListener("click", () => {
            const gameId = item.querySelector("a").href.split("/").pop();
            loadGameDetails(gameId);
        });
    });
});
