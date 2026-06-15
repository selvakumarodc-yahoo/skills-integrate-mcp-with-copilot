document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const authForms = document.getElementById("auth-forms");
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const logoutButton = document.getElementById("logout-button");
  const authMessageDiv = document.getElementById("auth-message");
  const authContainer = document.getElementById("auth-container");
  const signupContainer = document.getElementById("signup-container");

  let currentStudent = null;

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map((email) => {
                    const showUnregister = currentStudent && currentStudent.email === email;
                    return `<li><span class="participant-email">${email}</span>${
                      showUnregister
                        ? `<button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button>`
                        : ""
                    }</li>`;
                  })
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  async function fetchCurrentStudent() {
    try {
      const response = await fetch("/auth/me");
      if (!response.ok) {
        currentStudent = null;
        updateAuthUI();
        return;
      }
      currentStudent = await response.json();
      updateAuthUI();
    } catch (error) {
      console.error("Error fetching current student:", error);
      currentStudent = null;
      updateAuthUI();
    }
  }

  function updateAuthUI() {
    if (currentStudent) {
      authContainer.querySelector("h3").textContent =
        `Welcome, ${currentStudent.name}`;
      authForms.classList.add("hidden");
      logoutButton.classList.remove("hidden");
      signupContainer.classList.remove("hidden");
      authMessageDiv.textContent = `Logged in as ${currentStudent.email}`;
      authMessageDiv.className = "message info";
      authMessageDiv.classList.remove("hidden");
    } else {
      authContainer.querySelector("h3").textContent = "Student Login / Register";
      authForms.classList.remove("hidden");
      logoutButton.classList.add("hidden");
      signupContainer.classList.add("hidden");
      authMessageDiv.textContent = "Please log in or register to sign up for activities.";
      authMessageDiv.className = "message info";
      authMessageDiv.classList.remove("hidden");
    }
  }

  function showAuthMessage(message, type = "info") {
    authMessageDiv.textContent = message;
    authMessageDiv.className = `message ${type}`;
    authMessageDiv.classList.remove("hidden");
  }

  function showMessage(message, type = "success") {
    messageDiv.textContent = message;
    messageDiv.className = `message ${type}`;
    messageDiv.classList.remove("hidden");
    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/unregister`,
        {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const activity = activitySelect.value;
    if (!activity) {
      showMessage("Please select an activity.", "error");
      return;
    }

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const result = await response.json();
      if (response.ok) {
        currentStudent = result.student;
        updateAuthUI();
        fetchActivities();
      } else {
        showAuthMessage(result.detail || "Login failed", "error");
      }
    } catch (error) {
      showAuthMessage("Login request failed. Please try again.", "error");
      console.error("Error logging in:", error);
    }
  });

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const name = document.getElementById("register-name").value;
    const grade = document.getElementById("register-grade").value;
    const email = document.getElementById("register-email").value;
    const password = document.getElementById("register-password").value;

    try {
      const response = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, grade, email, password }),
      });

      const result = await response.json();
      if (response.ok) {
        currentStudent = result.student;
        updateAuthUI();
        fetchActivities();
      } else {
        showAuthMessage(result.detail || "Registration failed", "error");
      }
    } catch (error) {
      showAuthMessage("Registration request failed. Please try again.", "error");
      console.error("Error registering:", error);
    }
  });

  logoutButton.addEventListener("click", async () => {
    try {
      const response = await fetch("/auth/logout", {
        method: "POST",
      });
      if (response.ok) {
        currentStudent = null;
        updateAuthUI();
        fetchActivities();
      }
    } catch (error) {
      console.error("Error logging out:", error);
    }
  });

  fetchCurrentStudent();
  fetchActivities();
});
