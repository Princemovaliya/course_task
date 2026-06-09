(function () {
    const accessToken = sessionStorage.getItem("access_token");

    const tokenWarning = document.getElementById("token-warning");
    const formCard = document.getElementById("form-card");
    const form = document.getElementById("course-form");
    const submitButton = document.getElementById("submit-button");
    const formError = document.getElementById("form-error");
    const formSuccess = document.getElementById("form-success");

    const countrySelect = document.getElementById("country-select");
    const stateSelect = document.getElementById("state-select");
    const citySelect = document.getElementById("city-select");
    const startDatetimeInput = document.getElementById("start-datetime");

    const fieldNames = [
        "title",
        "description",
        "max_capacity",
        "start_datetime",
        "end_datetime",
        "country",
        "state",
        "city",
    ];

    function showElement(element, show) {
        element.hidden = !show;
    }

    function setMessage(element, message) {
        element.textContent = message;
        showElement(element, Boolean(message));
    }

    function resetMessages() {
        setMessage(formError, "");
        setMessage(formSuccess, "");
        fieldNames.forEach((fieldName) => {
            const errorElement = document.getElementById(`${fieldName}-error`);
            if (errorElement) {
                setMessage(errorElement, "");
            }
        });
    }

    function formatError(value) {
        if (Array.isArray(value)) {
            return value.map(formatError).join(" ");
        }
        if (value && typeof value === "object") {
            return Object.entries(value)
                .map(([key, nestedValue]) => `${key}: ${formatError(nestedValue)}`)
                .join(" ");
        }
        return String(value);
    }

    function showApiErrors(payload) {
        let usedFieldError = false;

        fieldNames.forEach((fieldName) => {
            if (payload && Object.prototype.hasOwnProperty.call(payload, fieldName)) {
                const errorElement = document.getElementById(`${fieldName}-error`);
                if (errorElement) {
                    setMessage(errorElement, formatError(payload[fieldName]));
                    usedFieldError = true;
                }
            }
        });

        const summary =
            payload?.detail ||
            payload?.non_field_errors ||
            payload?.error ||
            (!usedFieldError ? payload : "");
        setMessage(formError, summary ? formatError(summary) : "");
    }

    function formatDatetimeLocal(date) {
        const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
        return localDate.toISOString().slice(0, 16);
    }

    function setMinimumStartDatetime() {
        startDatetimeInput.min = formatDatetimeLocal(new Date());
    }

    function startDatetimeIsPast() {
        const selectedDate = new Date(startDatetimeInput.value);
        return (
            startDatetimeInput.value &&
            !Number.isNaN(selectedDate.getTime()) &&
            selectedDate < new Date()
        );
    }

    async function apiFetch(path, options = {}) {
        const response = await fetch(path, {
            ...options,
            headers: {
                Authorization: `Bearer ${accessToken}`,
                Accept: "application/json",
                ...(options.body ? { "Content-Type": "application/json" } : {}),
                ...options.headers,
            },
        });
        const body = await response.json().catch(() => ({}));

        if (!response.ok) {
            const error = new Error(body.detail || `Request failed (${response.status})`);
            error.payload = body;
            throw error;
        }

        return body;
    }

    function resetSelect(select, placeholder, disabled = true) {
        select.replaceChildren();
        const option = document.createElement("option");
        option.value = "";
        option.textContent = placeholder;
        select.appendChild(option);
        select.disabled = disabled;
    }

    function addOption(select, value, label) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        select.appendChild(option);
    }

    async function loadCountries() {
        resetSelect(countrySelect, "Loading countries...");
        const countries = await apiFetch("/api/location/countries/");
        resetSelect(countrySelect, "Select a country", false);
        countries
            .slice()
            .sort((a, b) => a.name.localeCompare(b.name))
            .forEach((country) => addOption(countrySelect, country.iso2, country.name));
    }

    async function loadStates(countryCode) {
        resetSelect(stateSelect, "Loading states...");
        resetSelect(citySelect, "Select a state first");

        const states = await apiFetch(
            `/api/location/states/?country=${encodeURIComponent(countryCode)}`
        );
        resetSelect(stateSelect, "Select a state", false);
        states
            .slice()
            .sort((a, b) => a.name.localeCompare(b.name))
            .forEach((state) => addOption(stateSelect, state.iso2 || state.state_code, state.name));
    }

    async function loadCities(countryCode, stateCode) {
        resetSelect(citySelect, "Loading cities...");

        const cities = await apiFetch(
            `/api/location/cities/?country=${encodeURIComponent(countryCode)}&state=${encodeURIComponent(stateCode)}`
        );
        resetSelect(citySelect, "Select a city", false);
        cities
            .slice()
            .sort((a, b) => a.name.localeCompare(b.name))
            .forEach((city) => addOption(citySelect, city.name, city.name));
    }

    function toIsoDatetime(inputValue) {
        const date = new Date(inputValue);
        return Number.isNaN(date.getTime()) ? "" : date.toISOString();
    }

    function buildPayload() {
        return {
            title: document.getElementById("title").value.trim(),
            description: document.getElementById("description").value.trim(),
            max_capacity: Number(document.getElementById("max-capacity").value),
            start_datetime: toIsoDatetime(document.getElementById("start-datetime").value),
            end_datetime: toIsoDatetime(document.getElementById("end-datetime").value),
            country: countrySelect.value,
            state: stateSelect.value,
            city: citySelect.value,
        };
    }

    async function init() {
        if (!accessToken) {
            showElement(tokenWarning, true);
            showElement(formCard, false);
            return;
        }

        showElement(tokenWarning, false);
        showElement(formCard, true);
        setMinimumStartDatetime();

        try {
            await loadCountries();
        } catch (error) {
            showApiErrors(error.payload || { detail: error.message });
        }
    }

    countrySelect.addEventListener("change", async () => {
        resetMessages();
        const countryCode = countrySelect.value;
        if (!countryCode) {
            resetSelect(stateSelect, "Select a country first");
            resetSelect(citySelect, "Select a state first");
            return;
        }

        try {
            await loadStates(countryCode);
        } catch (error) {
            resetSelect(stateSelect, "Could not load states");
            showApiErrors(error.payload || { detail: error.message });
        }
    });

    stateSelect.addEventListener("change", async () => {
        resetMessages();
        const stateCode = stateSelect.value;
        if (!stateCode) {
            resetSelect(citySelect, "Select a state first");
            return;
        }

        try {
            await loadCities(countrySelect.value, stateCode);
        } catch (error) {
            resetSelect(citySelect, "Could not load cities");
            showApiErrors(error.payload || { detail: error.message });
        }
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        resetMessages();
        setMinimumStartDatetime();

        if (startDatetimeIsPast()) {
            setMessage(
                document.getElementById("start_datetime-error"),
                "Course start datetime cannot be in the past."
            );
            return;
        }

        submitButton.disabled = true;
        submitButton.textContent = "Creating...";

        try {
            const course = await apiFetch("/api/courses/", {
                method: "POST",
                body: JSON.stringify(buildPayload()),
            });
            form.reset();
            resetSelect(stateSelect, "Select a country first");
            resetSelect(citySelect, "Select a state first");
            setMessage(
                formSuccess,
                `Course "${course.title}" created successfully for ${course.city}, ${course.state}, ${course.country}.`
            );
        } catch (error) {
            showApiErrors(error.payload || { detail: error.message });
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = "Create course";
        }
    });

    form.addEventListener("reset", () => {
        resetMessages();
        resetSelect(stateSelect, "Select a country first");
        resetSelect(citySelect, "Select a state first");
    });

    init();
})();
