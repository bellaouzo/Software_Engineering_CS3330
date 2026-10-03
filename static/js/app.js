/* ==========================================================================
   Form Submit Guard
   Disables each form's submit button once the form is submitted, to prevent
   accidental double submissions (e.g. duplicate tickets or comments).
   ========================================================================== */

// Attach the guard to every form on the page
document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", () => {
    const button = form.querySelector("button[type='submit']");

    // Not every form has a submit button, so check before using it
    if (button) {
      // Disabling happens after the submit event fires, so the form still
      // submits normally; it just can't be clicked a second time
      button.disabled = true;
    }
  });
});
