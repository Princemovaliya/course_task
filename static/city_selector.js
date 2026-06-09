(function () {
    const STORAGE_KEY = "city_selector_location";

    const loginForm = document.getElementById("login-form");
    const authSection = document.getElementById("auth-section");
    const selectorSection = document.getElementById("selector-section");
    const authError = document.getElementById("auth-error");

    const countrySelect = document.getElementById("country-select");
    const stateSelect = document.getElementById("state-select");
    const citySelect = document.getElementById("city-select");
    const selectionDisplay = document.getElementById("selection-display");

    let accessToken = sessionStorage.getItem("access_token");

    function showError(message) {
        authError.textContent = message;
        authError.hidden = !message;
    }

    async function apiFetch(path) {
        const response = await fetch(path, {
            headers: {
                Authorization: `Bearer ${accessToken}`,
                Accept: "application/json",
            },
        });
        if (!response.ok) {
            const body = await response.json().catch(() => ({}));
            throw new Error(body.detail || `Request failed (${response.status})`);
        }
        return response.json();
    }

    function resetSelect(select, placeholder, disabled = true) {
        select.innerHTML = `<option value="">${placeholder}</option>`;
        select.disabled = disabled;
    }

    function storeSelection(country, state, city) {
        const payload = { country, state, city, savedAt: new Date().toISOString() };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
        return payload;
    }

    function displaySelection(countryLabel, stateLabel, cityLabel, codes) {
        document.getElementById("selected-country").textContent =
            `${countryLabel} (${codes.country})`;
        document.getElementById("selected-state").textContent =
            `${stateLabel} (${codes.state})`;
        document.getElementById("selected-city").textContent = cityLabel;
        selectionDisplay.hidden = false;
    }

    async function loadCountries() {
        resetSelect(countrySelect, "Select a country", true);
        const countries = await apiFetch("/api/location/countries/");
        resetSelect(countrySelect, "Select a country", false);
        countries
            .sort((a, b) => a.name.localeCompare(b.name))
            .forEach((country) => {
                const option = document.createElement("option");
                option.value = country.iso2;
                option.textContent = country.name;
                countrySelect.appendChild(option);
            });
    }

    async function loadStates(countryCode) {
        resetSelect(stateSelect, "Loading states...");
        resetSelect(citySelect, "Select a state first");
        selectionDisplay.hidden = true;

        const states = await apiFetch(`/api/location/states/?country=${encodeURIComponent(countryCode)}`);
        resetSelect(stateSelect, "Select a state", false);
        states
            .sort((a, b) => a.name.localeCompare(b.name))
            .forEach((state) => {
                const option = document.createElement("option");
                option.value = state.iso2 || state.state_code;
                option.textContent = state.name;
                stateSelect.appendChild(option);
            });
    }

    async function loadCities(countryCode, stateCode) {
        resetSelect(citySelect, "Loading cities...");
        selectionDisplay.hidden = true;

        const cities = await apiFetch(
            `/api/location/cities/?country=${encodeURIComponent(countryCode)}&state=${encodeURIComponent(stateCode)}`
        );
        resetSelect(citySelect, "Select a city", false);
        cities
            .sort((a, b) => a.name.localeCompare(b.name))
            .forEach((city) => {
                const option = document.createElement("option");
                option.value = city.name;
                option.textContent = city.name;
                citySelect.appendChild(option);
            });
    }

    async function initSelector() {
        authSection.hidden = true;
        selectorSection.hidden = false;
        await loadCountries();

        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            try {
                const data = JSON.parse(saved);
                if (data.country) {
                    countrySelect.value = data.country;
                    await loadStates(data.country);
                }
                if (data.state) {
                    stateSelect.value = data.state;
                    await loadCities(data.country, data.state);
                }
                if (data.city) {
                    citySelect.value = data.city;
                    const countryLabel = countrySelect.selectedOptions[0]?.textContent || data.country;
                    const stateLabel = stateSelect.selectedOptions[0]?.textContent || data.state;
                    displaySelection(countryLabel, stateLabel, data.city, data);
                }
            } catch (_) {
                localStorage.removeItem(STORAGE_KEY);
            }
        }
    }

    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        showError("");

        const email = document.getElementById("login-email").value;
        const password = document.getElementById("login-password").value;

        try {
            const response = await fetch("/api/auth/login/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || "Login failed.");
            }
            accessToken = data.access;
            sessionStorage.setItem("access_token", accessToken);
            await initSelector();
        } catch (error) {
            showError(error.message);
        }
    });

    countrySelect.addEventListener("change", async () => {
        const countryCode = countrySelect.value;
        if (!countryCode) {
            resetSelect(stateSelect, "Select a country first");
            resetSelect(citySelect, "Select a state first");
            selectionDisplay.hidden = true;
            return;
        }
        try {
            await loadStates(countryCode);
        } catch (error) {
            resetSelect(stateSelect, error.message);
        }
    });

    stateSelect.addEventListener("change", async () => {
        const countryCode = countrySelect.value;
        const stateCode = stateSelect.value;
        if (!stateCode) {
            resetSelect(citySelect, "Select a state first");
            selectionDisplay.hidden = true;
            return;
        }
        try {
            await loadCities(countryCode, stateCode);
        } catch (error) {
            resetSelect(citySelect, error.message);
        }
    });

    citySelect.addEventListener("change", () => {
        const countryCode = countrySelect.value;
        const stateCode = stateSelect.value;
        const cityName = citySelect.value;
        if (!cityName) {
            selectionDisplay.hidden = true;
            return;
        }
        const codes = storeSelection(countryCode, stateCode, cityName);
        const countryLabel = countrySelect.selectedOptions[0].textContent;
        const stateLabel = stateSelect.selectedOptions[0].textContent;
        displaySelection(countryLabel, stateLabel, cityName, codes);
    });

    if (accessToken) {
        initSelector().catch(() => {
            sessionStorage.removeItem("access_token");
            accessToken = null;
            authSection.hidden = false;
            selectorSection.hidden = true;
            showError("Session expired. Please sign in again.");
        });
    }
})();
