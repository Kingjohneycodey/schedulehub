document.addEventListener("DOMContentLoaded", () => {
  const service = document.querySelector("#id_service");
  const date = document.querySelector("#id_date");
  const start = document.querySelector("#id_start_time");
  const slotBox = document.querySelector("#slot-box");
  const slotMsg = document.querySelector("#slot-message");
  if (!service || !date || !slotBox) return;

  const appointmentId = slotBox.dataset.appointment || "";

  const loadSlots = async () => {
    slotBox.innerHTML = "";
    slotMsg.textContent = "Checking availability…";
    if (!service.value || !date.value) {
      slotMsg.textContent = "Choose a service and date to see free times.";
      return;
    }
    const params = new URLSearchParams({
      service: service.value,
      date: date.value,
    });
    if (appointmentId) params.set("appointment", appointmentId);
    const response = await fetch(`/appointments/slots/?${params.toString()}`);
    const data = await response.json();
    slotMsg.textContent = data.message || "";
    data.slots.forEach((time) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "slot-btn";
      button.textContent = formatTime(time);
      button.dataset.value = time;
      if (start.value && start.value.slice(0, 5) === time) {
        button.classList.add("active");
      }
      button.addEventListener("click", () => {
        start.value = time;
        slotBox.querySelectorAll(".slot-btn").forEach((el) => el.classList.remove("active"));
        button.classList.add("active");
      });
      slotBox.appendChild(button);
    });
  };

  const formatTime = (value) => {
    const [h, m] = value.split(":");
    const hour = Number(h);
    const suffix = hour >= 12 ? "PM" : "AM";
    const twelve = ((hour + 11) % 12) + 1;
    return `${twelve}:${m} ${suffix}`;
  };

  service.addEventListener("change", loadSlots);
  date.addEventListener("change", loadSlots);
  loadSlots();
});
