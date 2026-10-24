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

/* ==========================================================================
   Matching Fields
   An input with data-match-input="<id>" must equal the input with that id
   (e.g. Confirm password). Uses the browser's built-in validation, so the
   form won't submit and the browser shows the message on the field.
   ========================================================================== */

// Message the browser shows on the confirm field
const MISMATCH_MESSAGE = "The passwords don't match.";

document.querySelectorAll("[data-match-input]").forEach((confirmInput) => {
  const originalInput = document.getElementById(confirmInput.dataset.matchInput);
  // Skip it if the id doesn't point at a real input
  if (!originalInput) {
    return;
  }

  const checkMatch = () => {
    // An empty custom message means "valid"
    const matches = confirmInput.value === originalInput.value;
    confirmInput.setCustomValidity(matches ? "" : MISMATCH_MESSAGE);
  };

  // Re-check when either field changes, so fixing the first one also clears the error
  confirmInput.addEventListener("input", checkMatch);
  originalInput.addEventListener("input", checkMatch);
});
