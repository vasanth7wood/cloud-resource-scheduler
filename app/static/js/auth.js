/**
 * Quick Credential Auto-Fill Helper for Academic Demonstration & Grading
 */
function fillCredentials(email, password) {
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');

  if (emailInput && passwordInput) {
    emailInput.value = email;
    passwordInput.value = password;

    // Visual feedback flash
    emailInput.style.borderColor = '#06b6d4';
    passwordInput.style.borderColor = '#06b6d4';
    setTimeout(() => {
      emailInput.style.borderColor = '';
      passwordInput.style.borderColor = '';
    }, 600);
  }
}
