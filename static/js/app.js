document.addEventListener("DOMContentLoaded", function () {
    initIngredientRows();
    initStepRows();
    initStarRating();
    initFavoriteToggle();
    initMobileMenu();
    initDeleteConfirm();
});

// ============================================================
// Dynamic Ingredient Rows
// ============================================================
function initIngredientRows() {
    const addBtn = document.getElementById("add-ingredient-btn");
    if (!addBtn) return;

    addBtn.addEventListener("click", function () {
        const container = document.getElementById("ingredients-container");
        if (!container) return;

        const rows = container.querySelectorAll(".ingredient-row");
        const index = rows.length;

        const row = document.createElement("div");
        row.className = "ingredient-row flex items-center gap-2 mb-2";
        row.innerHTML =
            '<input type="text" name="ingredient_name_' + index + '" placeholder="Ingredient" ' +
            'class="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent" required>' +
            '<input type="text" name="ingredient_quantity_' + index + '" placeholder="Quantity" ' +
            'class="w-28 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent">' +
            '<input type="text" name="ingredient_unit_' + index + '" placeholder="Unit" ' +
            'class="w-24 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent">' +
            '<button type="button" class="remove-ingredient-btn text-red-500 hover:text-red-700 p-1" title="Remove ingredient">' +
            '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">' +
            '<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />' +
            '</svg></button>';

        container.appendChild(row);
        updateIngredientCount(container);
        bindRemoveIngredient(row);
    });

    var existingRows = document.querySelectorAll(".ingredient-row");
    existingRows.forEach(function (row) {
        bindRemoveIngredient(row);
    });
}

function bindRemoveIngredient(row) {
    var btn = row.querySelector(".remove-ingredient-btn");
    if (!btn) return;
    btn.addEventListener("click", function () {
        var container = row.parentElement;
        var rows = container.querySelectorAll(".ingredient-row");
        if (rows.length <= 1) return;
        row.remove();
        updateIngredientCount(container);
    });
}

function updateIngredientCount(container) {
    var countInput = document.getElementById("ingredient_count");
    if (countInput) {
        countInput.value = container.querySelectorAll(".ingredient-row").length;
    }
}

// ============================================================
// Dynamic Step Rows
// ============================================================
function initStepRows() {
    var addBtn = document.getElementById("add-step-btn");
    if (!addBtn) return;

    addBtn.addEventListener("click", function () {
        var container = document.getElementById("steps-container");
        if (!container) return;

        var rows = container.querySelectorAll(".step-row");
        var index = rows.length;
        var stepNumber = index + 1;

        var row = document.createElement("div");
        row.className = "step-row flex items-start gap-2 mb-2";
        row.innerHTML =
            '<span class="step-number inline-flex items-center justify-center w-8 h-8 rounded-full bg-orange-100 text-orange-700 font-semibold text-sm mt-1 flex-shrink-0">' +
            stepNumber + '</span>' +
            '<textarea name="step_' + index + '" rows="2" placeholder="Describe this step..." ' +
            'class="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent" required></textarea>' +
            '<button type="button" class="remove-step-btn text-red-500 hover:text-red-700 p-1 mt-1" title="Remove step">' +
            '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">' +
            '<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />' +
            '</svg></button>';

        container.appendChild(row);
        updateStepCount(container);
        renumberSteps(container);
        bindRemoveStep(row);
    });

    var existingRows = document.querySelectorAll(".step-row");
    existingRows.forEach(function (row) {
        bindRemoveStep(row);
    });
}

function bindRemoveStep(row) {
    var btn = row.querySelector(".remove-step-btn");
    if (!btn) return;
    btn.addEventListener("click", function () {
        var container = row.parentElement;
        var rows = container.querySelectorAll(".step-row");
        if (rows.length <= 1) return;
        row.remove();
        renumberSteps(container);
        updateStepCount(container);
    });
}

function renumberSteps(container) {
    var rows = container.querySelectorAll(".step-row");
    rows.forEach(function (row, i) {
        var numberEl = row.querySelector(".step-number");
        if (numberEl) {
            numberEl.textContent = i + 1;
        }
    });
}

function updateStepCount(container) {
    var countInput = document.getElementById("step_count");
    if (countInput) {
        countInput.value = container.querySelectorAll(".step-row").length;
    }
}

// ============================================================
// Star Rating Selector
// ============================================================
function initStarRating() {
    var ratingContainers = document.querySelectorAll(".star-rating");
    ratingContainers.forEach(function (container) {
        var stars = container.querySelectorAll(".star");
        var hiddenInput = container.querySelector('input[type="hidden"]');
        if (!stars.length || !hiddenInput) return;

        var currentRating = parseInt(hiddenInput.value, 10) || 0;
        highlightStars(stars, currentRating);

        stars.forEach(function (star, index) {
            var value = index + 1;

            star.addEventListener("mouseenter", function () {
                highlightStars(stars, value);
            });

            star.addEventListener("mouseleave", function () {
                highlightStars(stars, parseInt(hiddenInput.value, 10) || 0);
            });

            star.addEventListener("click", function () {
                hiddenInput.value = value;
                currentRating = value;
                highlightStars(stars, value);
            });
        });
    });
}

function highlightStars(stars, rating) {
    stars.forEach(function (star, index) {
        if (index < rating) {
            star.classList.add("text-yellow-400");
            star.classList.remove("text-gray-300");
        } else {
            star.classList.remove("text-yellow-400");
            star.classList.add("text-gray-300");
        }
    });
}

// ============================================================
// Favorite Heart Toggle (AJAX)
// ============================================================
function initFavoriteToggle() {
    var favoriteBtns = document.querySelectorAll(".favorite-btn");
    favoriteBtns.forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();

            var recipeId = btn.getAttribute("data-recipe-id");
            if (!recipeId) return;

            btn.disabled = true;

            fetch("/recipes/" + recipeId + "/favorite", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest"
                },
                credentials: "same-origin"
            })
                .then(function (response) {
                    if (response.status === 401) {
                        window.location.href = "/auth/login";
                        return null;
                    }
                    if (!response.ok) {
                        throw new Error("Failed to toggle favorite");
                    }
                    return response.json();
                })
                .then(function (data) {
                    if (!data) return;

                    var heartIcon = btn.querySelector(".heart-icon");
                    var countEl = btn.querySelector(".favorite-count");

                    if (data.is_favorited) {
                        btn.classList.add("text-red-500");
                        btn.classList.remove("text-gray-400");
                        if (heartIcon) {
                            heartIcon.setAttribute("fill", "currentColor");
                        }
                    } else {
                        btn.classList.remove("text-red-500");
                        btn.classList.add("text-gray-400");
                        if (heartIcon) {
                            heartIcon.setAttribute("fill", "none");
                        }
                    }

                    if (countEl && data.favorite_count !== undefined) {
                        countEl.textContent = data.favorite_count;
                    }
                })
                .catch(function (err) {
                    console.error("Favorite toggle error:", err);
                })
                .finally(function () {
                    btn.disabled = false;
                });
        });
    });
}

// ============================================================
// Mobile Hamburger Menu Toggle
// ============================================================
function initMobileMenu() {
    var menuToggle = document.getElementById("mobile-menu-toggle");
    var mobileMenu = document.getElementById("mobile-menu");
    if (!menuToggle || !mobileMenu) return;

    menuToggle.addEventListener("click", function () {
        var isHidden = mobileMenu.classList.contains("hidden");
        if (isHidden) {
            mobileMenu.classList.remove("hidden");
            menuToggle.setAttribute("aria-expanded", "true");
        } else {
            mobileMenu.classList.add("hidden");
            menuToggle.setAttribute("aria-expanded", "false");
        }
    });

    document.addEventListener("click", function (e) {
        if (!menuToggle.contains(e.target) && !mobileMenu.contains(e.target)) {
            mobileMenu.classList.add("hidden");
            menuToggle.setAttribute("aria-expanded", "false");
        }
    });
}

// ============================================================
// Confirm Dialogs for Delete Actions
// ============================================================
function initDeleteConfirm() {
    var deleteForms = document.querySelectorAll("form[data-confirm]");
    deleteForms.forEach(function (form) {
        form.addEventListener("submit", function (e) {
            var message = form.getAttribute("data-confirm") || "Are you sure you want to delete this? This action cannot be undone.";
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    var deleteLinks = document.querySelectorAll("a[data-confirm]");
    deleteLinks.forEach(function (link) {
        link.addEventListener("click", function (e) {
            var message = link.getAttribute("data-confirm") || "Are you sure you want to delete this? This action cannot be undone.";
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    var deleteBtns = document.querySelectorAll("button[data-confirm]");
    deleteBtns.forEach(function (btn) {
        if (btn.closest("form[data-confirm]")) return;
        btn.addEventListener("click", function (e) {
            var message = btn.getAttribute("data-confirm") || "Are you sure you want to delete this? This action cannot be undone.";
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}