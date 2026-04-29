// main.js
// Handles: favorites toggle, toast notification.

// Saves individual user properties to the browser's storage
var saveUserToLocalStorage = function (user) {
    // If no user is provided, we use our clear function to wipe the old data
    if (user === null || typeof user === "undefined") {
        clearUserLocalStorage();
        return;
    }

    // If we have a user, we overwrite the "separated indexes" (keys)
    // localStorage.setItem always replaces old data with new data
    if (typeof Storage !== "undefined") {
        // We remove the old legacy key if it exists to keep storage clean
        // This prevents "ghost" data from the old version of our app
        localStorage.removeItem("aqar_user");

        // We save each piece of data into its own separate bucket in the browser
        localStorage.setItem("aqar_user_id", String(user.user_id));
        localStorage.setItem("aqar_user_name", user.name);
        localStorage.setItem("aqar_user_email", user.email);
        
        // Since favorites is a list, we must turn it into a string first
        var favoritesString = JSON.stringify(user.favorites);
        localStorage.setItem("aqar_user_favorites", favoritesString);
    }
};

// Retrieves the user object from the browser's storage by combining individual items
var loadUserFromLocalStorage = function () {
    // Check if localStorage is available
    if (typeof Storage === "undefined") {
        return null;
    }

    // Retrieve each user property individually
    var userIdRaw = localStorage.getItem("aqar_user_id");
    var userNameRaw = localStorage.getItem("aqar_user_name");
    var userEmailRaw = localStorage.getItem("aqar_user_email");
    var userFavoritesRaw = localStorage.getItem("aqar_user_favorites");

    // If any essential part of the user data is missing, assume no user is logged in
    if (userIdRaw === null || userNameRaw === null || userEmailRaw === null || userFavoritesRaw === null) {
        return null;
    }

    // Parse the retrieved string values back into their original types
    var userId = parseInt(userIdRaw, 10); // Convert user ID string back to a number
    var userName = userNameRaw;
    var userEmail = userEmailRaw;
    
    var userFavorites = [];
    try {
        // Parse the favorites JSON string back into an array
        var parsedFavorites = JSON.parse(userFavoritesRaw);
        // Ensure the parsed result is indeed an array
        if (Array.isArray(parsedFavorites)) {
            userFavorites = parsedFavorites;
        }
    } catch (error) {
        // If parsing fails, treat favorites as an empty array to prevent errors
        console.error("Error parsing user favorites from localStorage:", error);
        userFavorites = [];
    }

    // Reconstruct the user object from the individual pieces
    var userObject = {
        user_id: userId,
        name: userName,
        email: userEmail,
        favorites: userFavorites
    };
    return userObject;
};

// Adds or removes a property ID from the stored favorites list
// This function now directly updates the 'aqar_user_favorites' key
var updateLocalStorageFavorites = function (propId, isNowFavorited) {
    // Check if localStorage is available
    if (typeof Storage === "undefined") {
        return;
    }

    // Get the current favorites list from localStorage
    var userFavoritesRaw = localStorage.getItem("aqar_user_favorites");
    var favoritesList = [];

    // Attempt to parse the existing favorites list
    if (userFavoritesRaw !== null) {
        try {
            var parsedFavorites = JSON.parse(userFavoritesRaw);
            if (Array.isArray(parsedFavorites)) {
                favoritesList = parsedFavorites;
            }
        } catch (error) {
            console.error("Error parsing user favorites for update:", error);
            favoritesList = []; // Reset if parsing fails
        }
    }
    
    var foundIndex = -1;
    // Loop through the favorites list to find the property ID
    for (var i = 0; i < favoritesList.length; i++) {
        if (favoritesList[i] === propId) {
            foundIndex = i;
            break; // Stop searching once found
        }
    }

    // Add or remove the property ID based on the 'isNowFavorited' flag
    if (isNowFavorited === true) {
        // If it's not already in the list, add it
        if (foundIndex === -1) {
            favoritesList.push(propId);
        }
    } else {
        // If it was found, remove it
        if (foundIndex !== -1) {
            favoritesList.splice(foundIndex, 1);
        }
    }

    // Save the updated favorites list back to localStorage as a JSON string
    localStorage.setItem("aqar_user_favorites", JSON.stringify(favoritesList));
};

// Deletes all user-related data from storage (used on logout)
var clearUserLocalStorage = function () {
    if (typeof Storage !== "undefined") {
        // Make sure we also delete the old combined key
        localStorage.removeItem("aqar_user");

        localStorage.removeItem("aqar_user_id");
        localStorage.removeItem("aqar_user_name");
        localStorage.removeItem("aqar_user_email");
        localStorage.removeItem("aqar_user_favorites");
    }
};

document.addEventListener("DOMContentLoaded", function () {
    if (typeof window.AQAR_USER !== "undefined") {
        saveUserToLocalStorage(window.AQAR_USER);
    } else {
        clearUserLocalStorage();
    }

    var logoutLink = document.querySelector('a[href="/logout"]');
    if (logoutLink) {
        logoutLink.addEventListener("click", function () {
            clearUserLocalStorage();
        });
    }

});


// Sends a request to the server to favorite/unfavorite and updates the UI
var toggleFav = async function (btn, propId) {

    try {
        // Send POST request to Flask
        var response = await fetch("/api/favorite/" + propId, { method: "POST" });

        // If server redirected to /login, the user is not logged in
        if (response.redirected) {
            showToast("Please login to save properties");
            return;
        }

        if (!response.ok) {
            throw new Error("Server error");
        }

        // Read the JSON response — { favorited: true } or { favorited: false }
        var data = await response.json();

        // Update every heart button on the page that has this prop_id
        var all_buttons = document.querySelectorAll("[data-prop-id=\"" + propId + "\"]");

        for (var i = 0; i < all_buttons.length; i++) {
            var button = all_buttons[i];

            if (data.favorited) {
                button.classList.add("active");
                button.textContent = "❤️";
            } else {
                button.classList.remove("active");
                button.textContent = "🤍";
            }
        }

        // Also update the large fav button on the property detail page if present
        var detail_button = document.getElementById("detailFavBtn");

        if (detail_button) {
            if (data.favorited) {
                detail_button.classList.add("active");
                detail_button.innerHTML = "❤️ Saved";
            } else {
                detail_button.classList.remove("active");
                detail_button.innerHTML = "🤍 Save Property";
            }
        }

        // Keep localStorage in sync with the current logged-in user
        updateLocalStorageFavorites(propId, data.favorited);

        // Show feedback message at the bottom of the screen
        if (data.favorited) {
            showToast("Property saved ❤️");
        } else {
            showToast("Removed from saved");
        }

    } catch (error) {
        showToast("Something went wrong. Please try again.");
    }

};


// notification
var showToast = function (message) {

    // Remove any existing toast first
    var existing_toast = document.getElementById("toastMsg");
    if (existing_toast) {
        existing_toast.remove();
    }

    // Create a new toast element
    var toast = document.createElement("div");
    toast.id = "toastMsg";
    toast.className = "toast";
    toast.textContent = message;

    // Add it to the page
    document.body.appendChild(toast);

    // After 2.5 seconds, fade it out and remove it
    setTimeout(function () {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.3s";

        setTimeout(function () {
            toast.remove();
        }, 300);

    }, 2500);

};