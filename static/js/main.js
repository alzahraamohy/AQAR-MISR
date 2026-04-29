// main.js
// favorites toggle, toast notification.
var saveUserToLocalStorage = function (user) {
    // If no user is provided, we use our clear function to wipe the old data
    if (user === null || typeof user === "undefined") {
        clearUserLocalStorage();
        return;
    }

    if (typeof Storage !== "undefined") {
        localStorage.removeItem("aqar_user");

        localStorage.setItem("aqar_user_id", String(user.user_id));
        localStorage.setItem("aqar_user_name", user.name);
        localStorage.setItem("aqar_user_email", user.email);
        
        var favoritesString = JSON.stringify(user.favorites);
        localStorage.setItem("aqar_user_favorites", favoritesString);
    }
};

var loadUserFromLocalStorage = function () {
    if (typeof Storage === "undefined") {
        return null;
    }

    var userIdRaw = localStorage.getItem("aqar_user_id");
    var userNameRaw = localStorage.getItem("aqar_user_name");
    var userEmailRaw = localStorage.getItem("aqar_user_email");
    var userFavoritesRaw = localStorage.getItem("aqar_user_favorites");

    if (userIdRaw === null || userNameRaw === null || userEmailRaw === null || userFavoritesRaw === null) {
        return null;
    }

    var userId = parseInt(userIdRaw, 10); 
    var userName = userNameRaw;
    var userEmail = userEmailRaw;
    
    var userFavorites = [];
    try {
        var parsedFavorites = JSON.parse(userFavoritesRaw);
        if (Array.isArray(parsedFavorites)) {
            userFavorites = parsedFavorites;
        }
    } catch (error) {
        console.error("Error parsing user favorites from localStorage:", error);
        userFavorites = [];
    }

    let userObject = {
        user_id: userId,
        name: userName,
        email: userEmail,
        favorites: userFavorites
    };
    return userObject;
};

let updateLocalStorageFavorites = function (propId, isNowFavorited) {
    if (typeof Storage === "undefined") {
        return;
    }

    let userFavoritesRaw = localStorage.getItem("aqar_user_favorites");
    let favoritesList = [];

    if (userFavoritesRaw !== null) {
        try {
            let parsedFavorites = JSON.parse(userFavoritesRaw);
            if (Array.isArray(parsedFavorites)) {
                favoritesList = parsedFavorites;
            }
        } catch (error) {
            console.error("Error parsing user favorites for update:", error);
            favoritesList = []; 
        }
    }
    
    let foundIndex = -1;
    for (let i = 0; i < favoritesList.length; i++) {
        if (favoritesList[i] === propId) {
            foundIndex = i;
            break; // Stop searching once found
        }
    }

    if (isNowFavorited === true) {
        // If it's not already in the list, add it
        if (foundIndex === -1) {
            favoritesList.push(propId);
        }
    } else {
        if (foundIndex !== -1) {
            favoritesList.splice(foundIndex, 1);
        }
    }

    localStorage.setItem("aqar_user_favorites", JSON.stringify(favoritesList));
};

let clearUserLocalStorage = function () {
    if (typeof Storage !== "undefined") {
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

    let logoutLink = document.querySelector('a[href="/logout"]');
    if (logoutLink) {
        logoutLink.addEventListener("click", function () {
            clearUserLocalStorage();
        });
    }

});


let toggleFav = async function (btn, propId) {

    try {
        let response = await fetch("/api/favorite/" + propId, { method: "POST" });

        if (response.redirected) {
            showToast("Please login to save properties");
            return;
        }

        if (response.ok === false) {
            throw new Error("Server error: " + response.status);
        }

        let data = await response.json();

        let all_buttons = document.querySelectorAll("[data-prop-id=\"" + propId + "\"]");

        for (let i = 0; i < all_buttons.length; i++) {
            let button = all_buttons[i];

            if (data.favorited === true) {
                button.classList.add("active");
                button.textContent = "❤️";
            } else {
                button.classList.remove("active");
                button.textContent = "🤍";
            }
        }

        let detail_button = document.getElementById("detailFavBtn");

        if (detail_button) {
            if (data.favorited === true) {
                detail_button.classList.add("active");
                detail_button.innerHTML = "❤️ Saved";
            } else {
                detail_button.classList.remove("active");
                detail_button.innerHTML = "🤍 Save Property";
            }
        }

        updateLocalStorageFavorites(propId, data.favorited);

        if (data.favorited === true) {
            showToast("Property saved ❤️");
        } else {
            showToast("Removed from saved");
        }

    } catch (error) {
        showToast("Something went wrong. Please try again.");
        console.error("Error toggling favorite:", error);
    }

};


let showToast = function (message) {

    let existing_toast = document.getElementById("toastMsg");
    if (existing_toast) {
        existing_toast.remove();
    }

    let toast = document.createElement("div");
    toast.id = "toastMsg";
    toast.className = "toast";
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(function () {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.3s";

        setTimeout(function () {
            toast.remove();
        }, 300);

    }, 2500);

};