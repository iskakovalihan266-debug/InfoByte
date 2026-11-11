// Бұл файл тек өз HTML бетінде қолданылады.
const form = document.querySelector('#auth-form');
const email = document.querySelector('#email');
const password = document.querySelector('#password');
const status = document.querySelector('#form-status');
const toggle = document.querySelector('.password-toggle');

function clearErrors() {
  form.querySelectorAll('.field-error').forEach(item => { item.textContent = ''; });
  form.querySelectorAll('[aria-invalid]').forEach(input => input.removeAttribute('aria-invalid'));
  status.textContent = '';
  status.classList.remove('is-info');
}

function showError(input, errorId, message) {
  input.setAttribute('aria-invalid', 'true');
  input.setAttribute('aria-describedby', errorId);
  document.getElementById(errorId).textContent = message;
}

toggle.addEventListener('click', () => {
  const visible = password.type === 'password';
  form.querySelectorAll('[name="password"], [name="confirmPassword"]').forEach(input => {
    input.type = visible ? 'text' : 'password';
  });
  toggle.setAttribute('aria-pressed', String(visible));
  toggle.setAttribute('aria-label', visible ? 'Құпиясөзді жасыру' : 'Құпиясөзді көрсету');
});

form.addEventListener('submit', event => {
  event.preventDefault();
  clearErrors();
  if (!email.value.trim() || !email.validity.valid) {
    showError(email, 'email-error', 'Жарамды электрондық поштаны енгізіңіз.');
  }
  if (password.value.length < 8) {
    showError(password, 'password-error', 'Құпиясөз кемінде 8 таңбадан тұруы керек.');
  }

  const fullName = document.querySelector('#full-name');
  const confirm = document.querySelector('#confirm-password');
  if (fullName.value.trim().length < 2) {
    showError(fullName, 'name-error', 'Аты-жөніңізді енгізіңіз.');
  }
  if (confirm.value !== password.value) {
    showError(confirm, 'confirm-error', 'Құпиясөздер бірдей емес.');
  }

  const firstError = form.querySelector('[aria-invalid="true"]');
  if (firstError) {
    firstError.focus();
    return;
  }
  status.textContent = 'Тіркелу формасы дұрыс толтырылды. Нақты аккаунт ашу үшін backend қажет.';
});
