document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector(".upload-form");
  if (!form) return;

  form.addEventListener("submit", () => {
    const btn = form.querySelector("button[type='submit']");
    if (btn) {
      btn.textContent = "Analyzing...";
      btn.disabled = true;
    }
  });
});
