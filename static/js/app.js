document.addEventListener("DOMContentLoaded", () => {
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.classList.add("opacity-50");
    }, 4000);
  });

  // Auto-submit filters with debounce
  const form = document.getElementById("filter-form");
  if (form) {
    let timer = null;
    form.querySelectorAll(".auto-submit").forEach((el) => {
      const event = el.tagName === "SELECT" ? "change" : "input";
      el.addEventListener(event, () => {
        clearTimeout(timer);
        timer = setTimeout(() => form.submit(), 400);
      });
    });
  }
});
