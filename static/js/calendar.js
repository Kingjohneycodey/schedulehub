document.addEventListener("DOMContentLoaded", () => {
  const calendarEl = document.getElementById("calendar");
  if (!calendarEl || typeof FullCalendar === "undefined") return;

  const isMobile = window.innerWidth < 768;

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: isMobile ? "timeGridDay" : "timeGridWeek",
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,timeGridWeek,timeGridDay",
    },
    height: "auto",
    nowIndicator: true,
    slotMinTime: "08:00:00",
    slotMaxTime: "19:00:00",
    dayMaxEvents: true,
    events: "/calendar/events/",
    eventClick: (info) => {
      info.jsEvent.preventDefault();
      if (info.event.url) window.location.href = info.event.url;
    },
  });
  calendar.render();
});
