// Event Listener for Recommendation List section
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
