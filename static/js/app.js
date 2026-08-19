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

  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebar-overlay");
  const openBtn = document.getElementById("menu-toggle");
  const closeBtn = document.getElementById("sidebar-close");
  const closeMenu = () => {
    sidebar?.classList.remove("open");
    overlay?.classList.remove("show");
  };
  const openMenu = () => {
    sidebar?.classList.add("open");
    overlay?.classList.add("show");
  };
  openBtn?.addEventListener("click", openMenu);
  closeBtn?.addEventListener("click", closeMenu);
  overlay?.addEventListener("click", closeMenu);
});
