const venuesListEl = document.getElementById("venues-list");
const venueSelectEl = document.getElementById("venue-select");
const bookingsListEl = document.getElementById("bookings-list");
const bookingFormEl = document.getElementById("booking-form");
const feedbackEl = document.getElementById("feedback");

function showFeedback(message, type) {
  feedbackEl.textContent = message;
  feedbackEl.className = `feedback ${type}`;
}

function clearFeedback() {
  feedbackEl.className = "feedback hidden";
  feedbackEl.textContent = "";
}

async function loadVenues() {
  const res = await fetch("/api/venues");
  const venues = await res.json();

  venuesListEl.innerHTML = "";
  venueSelectEl.innerHTML = "";

  venues.forEach((v) => {
    const card = document.createElement("div");
    card.className = "venue-card";
    card.innerHTML = `
      <strong>${v.name}</strong>
      <div class="venue-meta">${v.location} &bull; Up to ${v.capacity} guests</div>
      <div class="venue-rate">KES ${Number(v.rate_per_day).toLocaleString()} / day</div>
    `;
    card.addEventListener("click", () => {
      venueSelectEl.value = v.id;
      document.getElementById("event-date").focus();
    });
    venuesListEl.appendChild(card);

    const opt = document.createElement("option");
    opt.value = v.id;
    opt.textContent = `${v.name} (${v.location})`;
    venueSelectEl.appendChild(opt);
  });
}

async function loadBookings() {
  const res = await fetch("/api/bookings");
  const bookings = await res.json();

  bookingsListEl.innerHTML = "";
  if (bookings.length === 0) {
    bookingsListEl.innerHTML = `<p class="venue-meta">No bookings yet.</p>`;
    return;
  }

  bookings.forEach((b) => {
    const row = document.createElement("div");
    row.className = "booking-item";
    row.innerHTML = `
      <div>
        <strong>${b.venue_name}</strong> &mdash; <span>${b.event_date}</span>
        <small>${b.client_name} (${b.client_phone})</small>
      </div>
      <button class="btn-cancel" data-id="${b.id}" type="button">Cancel</button>
    `;
    row.querySelector(".btn-cancel").addEventListener("click", async () => {
      await fetch(`/api/bookings/${b.id}`, { method: "DELETE" });
      loadBookings();
    });
    bookingsListEl.appendChild(row);
  });
}

bookingFormEl.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearFeedback();

  const payload = {
    venue_id: Number(venueSelectEl.value),
    event_date: document.getElementById("event-date").value,
    client_name: document.getElementById("client-name").value,
    client_phone: document.getElementById("client-phone").value,
  };

  const res = await fetch("/api/bookings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) {
    showFeedback(data.error || "Could not create booking.", "error");
    return;
  }

  showFeedback(`Booked ${data.venue_name} for ${data.event_date}.`, "ok");
  bookingFormEl.reset();
  venueSelectEl.value = payload.venue_id;
  loadBookings();
});

loadVenues().then(loadBookings);