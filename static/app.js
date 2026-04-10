const datePicker = document.getElementById("date-picker");
const loading = document.getElementById("loading");
const noSlots = document.getElementById("no-slots");
const slotsSection = document.getElementById("slots-section");
const slotsTitle = document.getElementById("slots-title");
const slotsGrid = document.getElementById("slots-grid");

const modalOverlay = document.getElementById("modal-overlay");
const modalType = document.getElementById("modal-type");
const modalDate = document.getElementById("modal-date");
const modalTime = document.getElementById("modal-time");
const modalCancel = document.getElementById("modal-cancel");
const modalConfirm = document.getElementById("modal-confirm");

const toast = document.getElementById("toast");
const toastMessage = document.getElementById("toast-message");

const TYPE_LABELS = {
  EVALUACION: "Evaluación",
  TRATAMIENTO: "Tratamiento",
};

let selectedType = null;
let pendingSlot = null;

// ── Type selector ────────────────────────────────────────────────────────────

const typeSelect = document.getElementById("type-select");

typeSelect.addEventListener("change", () => {
  selectedType = typeSelect.value || null;
  if (selectedType) fetchSlots();
  else {
    slotsSection.classList.add("hidden");
    noSlots.classList.add("hidden");
    loading.classList.add("hidden");
  }
});

// ── Date picker ──────────────────────────────────────────────────────────────

datePicker.addEventListener("change", () => {
  if (selectedType) fetchSlots();
});

// ── Fetch availability ───────────────────────────────────────────────────────

async function fetchSlots() {
  const date = datePicker.value;
  if (!date || !selectedType) return;

  setLoadingState(true);

  try {
    const res = await fetch(`/api/availability?date=${date}&type=${selectedType}`);
    const slots = await res.json();

    setLoadingState(false);

    if (!Array.isArray(slots) || slots.length === 0) {
      noSlots.classList.remove("hidden");
      return;
    }

    renderSlots(slots, date);
    slotsSection.classList.remove("hidden");
  } catch {
    setLoadingState(false);
    showToast("Error al cargar disponibilidad", true);
  }
}

function setLoadingState(isLoading) {
  loading.classList.toggle("hidden", !isLoading);
  noSlots.classList.add("hidden");
  slotsSection.classList.add("hidden");
}

// ── Render slots ─────────────────────────────────────────────────────────────

function renderSlots(slots, date) {
  const formatted = formatDate(date);
  slotsTitle.textContent = `${TYPE_LABELS[selectedType]} — ${formatted}`;

  slotsGrid.innerHTML = "";
  slots.forEach((slot) => {
    const card = document.createElement("button");
    card.className = "slot-card";
    card.type = "button";
    card.innerHTML = `
      <span class="slot-time">${slot.start}</span>
      <span class="slot-end-time">hasta ${slot.end}</span>
    `;
    card.addEventListener("click", () => openModal(slot, date));
    slotsGrid.appendChild(card);
  });
}

function formatDate(isoDate) {
  // Use noon to avoid DST/timezone shifting the date
  const d = new Date(isoDate + "T12:00:00");
  return d.toLocaleDateString("es-CL", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

// ── Modal ────────────────────────────────────────────────────────────────────

function openModal(slot, date) {
  pendingSlot = { ...slot, date };
  modalType.textContent = TYPE_LABELS[selectedType];
  modalDate.textContent = formatDate(date);
  modalTime.textContent = `${slot.start} – ${slot.end}`;
  modalOverlay.classList.remove("hidden");
}

function closeModal() {
  modalOverlay.classList.add("hidden");
  pendingSlot = null;
  modalConfirm.disabled = false;
  modalConfirm.textContent = "Confirmar";
}

modalCancel.addEventListener("click", closeModal);

// Close when clicking the backdrop
modalOverlay.addEventListener("click", (e) => {
  if (e.target === modalOverlay) closeModal();
});

// Close on Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !modalOverlay.classList.contains("hidden")) closeModal();
});

// ── Confirm booking ──────────────────────────────────────────────────────────

modalConfirm.addEventListener("click", async () => {
  if (!pendingSlot) return;

  modalConfirm.disabled = true;
  modalConfirm.textContent = "Agendando…";

  try {
    const res = await fetch("/api/appointments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        date: pendingSlot.date,
        time: pendingSlot.start,
        type: selectedType,
      }),
    });

    const data = await res.json();
    closeModal();

    if (res.ok) {
      showToast(data.message || "¡Cita agendada!");
      fetchSlots(); // Refresh to reflect the newly booked slot
    } else {
      showToast(data.error || "Error al agendar", true);
    }
  } catch {
    closeModal();
    showToast("Error de conexión", true);
  }
});

// ── Toast ────────────────────────────────────────────────────────────────────

let toastTimer = null;

function showToast(message, isError = false) {
  clearTimeout(toastTimer);
  toastMessage.textContent = message;
  toast.className = "toast" + (isError ? " error" : "");
  toast.classList.remove("hidden");
  toastTimer = setTimeout(() => toast.classList.add("hidden"), 3500);
}
