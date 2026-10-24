/* ==========================================================================
   Inline Form Validation (Req 6.1)
   Shows an error under a field once it breaks a rule, and shows all of them
   when you hit submit so nothing bad gets sent. The rules are just HTML
   attributes on the field (required, minlength, pattern, data-match-input).
   data-rule-message is the error text. The server still checks everything.
   ========================================================================== */

const FIELD_SELECTOR = "input, textarea, select";
// Used if a match field doesn't have its own data-rule-message
const MISMATCH_MESSAGE = "The passwords don't match.";

// Gets the field's label text (like "Title") for the error message
function getFieldLabel(field) {
  const label = field.form.querySelector(`label[for="${field.id}"]`);
  return label ? label.textContent.trim() : "This field";
}

// Checks the browser doesn't do well on its own:
// spaces only counts as empty (the server strips them too), minlength
// (browsers skip it for autofilled values), and confirm password matching
function checkExtraRules(field) {
  const value = field.value;
  const isText = field.tagName === "TEXTAREA" || field.type === "text";
  let message = "";
  if (isText && field.required && value !== "" && value.trim() === "") {
    message = `${getFieldLabel(field)} is required.`;
  } else if (field.minLength > 0 && value !== "" && value.length < field.minLength) {
    message = field.dataset.ruleMessage || `${getFieldLabel(field)} is too short.`;
  } else if (field.dataset.matchInput) {
    const original = document.getElementById(field.dataset.matchInput);
    if (original && value !== "" && value !== original.value) {
      message = field.dataset.ruleMessage || MISMATCH_MESSAGE;
    }
  }
  // An empty message means the field is fine
  field.setCustomValidity(message);
}

// Returns the error for the first rule the field breaks, or "" if it's fine
function getErrorMessage(field) {
  const validity = field.validity;
  if (validity.valueMissing) {
    return `${getFieldLabel(field)} is required.`;
  }
  if (validity.tooShort || validity.tooLong || validity.patternMismatch) {
    return field.dataset.ruleMessage || `${getFieldLabel(field)} is not in the right format.`;
  }
  if (validity.customError) {
    return field.validationMessage;
  }
  return "";
}

// Finds the error <p> under a field, or makes one the first time
function getErrorElement(field) {
  const errorId = `${field.id}-error`;
  let error = document.getElementById(errorId);
  if (!error) {
    error = document.createElement("p");
    error.id = errorId;
    error.className = "field-error";
    error.hidden = true;

    // Goes under the hint text if the field has one, otherwise right under the field
    const hint = field.nextElementSibling;
    const anchor = hint && hint.classList.contains("field-hint") ? hint : field;
    anchor.insertAdjacentElement("afterend", error);

    // Lets screen readers read the error along with the field
    const describedBy = field.getAttribute("aria-describedby");
    field.setAttribute("aria-describedby", describedBy ? `${describedBy} ${errorId}` : errorId);
  }
  return error;
}

// Checks one field and shows or hides its error. Returns true if it's valid.
function validateField(field) {
  if (!field.id || !field.willValidate) {
    return true;
  }
  checkExtraRules(field);
  const message = getErrorMessage(field);
  // Fine and never had an error, so there's nothing to update
  if (!message && !document.getElementById(`${field.id}-error`)) {
    return true;
  }
  const error = getErrorElement(field);
  error.textContent = message;
  error.hidden = !message;
  field.classList.toggle("has-error", Boolean(message));
  field.setAttribute("aria-invalid", message ? "true" : "false");
  return !message;
}

document.querySelectorAll("form").forEach((form) => {
  // Turn off the browser's popup bubbles since we show our own errors.
  // If JavaScript is off this never runs, so the browser checks still work.
  form.noValidate = true;

  // When they click out of a field they typed in, check it
  form.addEventListener("focusout", (event) => {
    const field = event.target;
    if (field.matches(FIELD_SELECTOR) && field.value !== "") {
      field.dataset.touched = "true";
      validateField(field);
    }
  });

  // Once a field has been checked, re-check it as they type so the error
  // goes away as soon as it's fixed
  form.addEventListener("input", (event) => {
    const field = event.target;
    if (field.dataset.touched) {
      validateField(field);
    }
    // Changing the password also re-checks Confirm password
    form.querySelectorAll(`[data-match-input="${field.id}"]`).forEach((confirmField) => {
      if (confirmField.dataset.touched) {
        validateField(confirmField);
      }
    });
  });

  form.addEventListener("submit", (event) => {
    // Check every field so all the errors show at once
    let firstInvalid = null;
    form.querySelectorAll(FIELD_SELECTOR).forEach((field) => {
      field.dataset.touched = "true";
      if (!validateField(field) && !firstInvalid) {
        firstInvalid = field;
      }
    });

    // Something's wrong, so stop the submit and jump to the first bad field
    if (firstInvalid) {
      event.preventDefault();
      firstInvalid.focus();
      return;
    }

    // Submit guard: disable the button after a good submit so people can't
    // double click and make duplicate tickets or comments. The form still
    // sends since this runs after the submit already started.
    const button = form.querySelector("button[type='submit']");
    if (button) {
      button.disabled = true;
    }
  });
});
