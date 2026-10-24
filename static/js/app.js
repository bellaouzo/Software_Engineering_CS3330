Shows a message under a field as soon as its input breaks a rule, and again
   for every problem when the user clicks submit, before anything is sent.
   The rules themselves are plain HTML attributes on each field (required,
   minlength, pattern); data-rule-message holds the text shown when a
   minlength or pattern rule is broken. The server still checks everything.
   ========================================================================== */
 
const FIELD_SELECTOR = "input, textarea, select";
 
// The text of the field's <label>, e.g. "Title"
function getFieldLabel(field) {
  const label = field.form.querySelector(`label[for="${field.id}"]`);
  return label ? label.textContent.trim() : "This field";
}
 
// Two checks the browser does not do reliably on its own:
// - a required field holding only spaces counts as empty (the server agrees)
// - minlength, which browsers skip for values filled in by autofill or scripts
function checkExtraRules(field) {
  const value = field.value;
  const isText = field.tagName === "TEXTAREA" || field.type === "text";
  let message = "";
  if (isText && field.required && value !== "" && value.trim() === "") {
    message = `${getFieldLabel(field)} is required.`;
  } else if (field.minLength > 0 && value !== "" && value.length < field.minLength) {
    message = field.dataset.ruleMessage || `${getFieldLabel(field)} is too short.`;
  }
  field.setCustomValidity(message);
}
 
// The message for the first rule this field breaks, or "" if it is fine
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
 
// The message element under a field, created the first time it is needed
function getErrorElement(field) {
  const errorId = `${field.id}-error`;
  let error = document.getElementById(errorId);
  if (!error) {
    error = document.createElement("p");
    error.id = errorId;
    error.className = "field-error";
    error.hidden = true;
 
    // Put it after the field's hint text if there is one, otherwise after the field
    const hint = field.nextElementSibling;
    const anchor = hint && hint.classList.contains("field-hint") ? hint : field;
    anchor.insertAdjacentElement("afterend", error);
 
    // Screen readers read the hint and the error together with the field
    const describedBy = field.getAttribute("aria-describedby");
    field.setAttribute("aria-describedby", describedBy ? `${describedBy} ${errorId}` : errorId);
  }
  return error;
}
 
// Checks one field and shows or hides its message. Returns true if it is valid.
function validateField(field) {
  if (!field.id || !field.willValidate) {
    return true;
  }
  checkExtraRules(field);
  const message = getErrorMessage(field);
  if (!message && !document.getElementById(`${field.id}-error`)) {
    return true; // valid and never showed an error: nothing to update
  }
  const error = getErrorElement(field);
  error.textContent = message;
  error.hidden = !message;
  field.classList.toggle("has-error", Boolean(message));
  field.setAttribute("aria-invalid", message ? "true" : "false");
  return !message;
}
 
document.querySelectorAll("form").forEach((form) => {
  // Our messages replace the browser's pop-up bubbles. Without JavaScript,
  // noValidate stays false and the browser's own checks still run.
  form.noValidate = true;
 
  // Leaving a field the user typed in: check it right away
  form.addEventListener("focusout", (event) => {
    const field = event.target;
    if (field.matches(FIELD_SELECTOR) && field.value !== "") {
      field.dataset.touched = "true";
      validateField(field);
    }
  });
 
  // Typing in a field that was already checked: update its message live,
  // so it disappears as soon as the input is fixed
  form.addEventListener("input", (event) => {
    const field = event.target;
    if (field.dataset.touched) {
      validateField(field);
    }
  });
 
  form.addEventListener("submit", (event) => {
    // Check every field, so all problems show at once
    let firstInvalid = null;
    form.querySelectorAll(FIELD_SELECTOR).forEach((field) => {
      field.dataset.touched = "true";
      if (!validateField(field) && !firstInvalid) {
        firstInvalid = field;
      }
    });
 
    if (firstInvalid) {
      event.preventDefault(); // nothing is sent
      firstInvalid.focus();
      return;
    }
 
    /* Form Submit Guard: disable the submit button once a valid form is sent,
       to prevent accidental double submissions (e.g. duplicate tickets or
       comments). Disabling happens after the submit event fires, so the form
       still submits normally; it just can't be clicked a second time. */
    const button = form.querySelector("button[type='submit']");
    if (button) {
      button.disabled = true;
    }
  });
});
