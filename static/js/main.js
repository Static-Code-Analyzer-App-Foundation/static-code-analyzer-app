document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("uploadForm");
  if (!form) return;

  const fileInput = form.querySelector('input[type="file"]');
  const submitBtn = document.getElementById("submitBtn");

  if (fileInput) {
    fileInput.addEventListener("change", () => {
      if (fileInput.files && fileInput.files.length > 0) {
        const file = fileInput.files[0];
        if (submitBtn) {
          submitBtn.textContent = `Run Enterprise Evaluation: ${file.name}`;
        }
      } else if (submitBtn) {
        submitBtn.textContent = "Run Enterprise Evaluation";
      }
    });
  }

  form.addEventListener("submit", () => {
    if (submitBtn) {
      submitBtn.textContent = "Analyzing...";
      submitBtn.disabled = true;
      submitBtn.style.opacity = "0.85";
      submitBtn.style.cursor = "wait";
    }
  });
});
