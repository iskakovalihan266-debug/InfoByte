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

document.querySelector('.forgot-button').addEventListener('click', () => {
  status.classList.add('is-info');
  status.textContent = 'Құпиясөзді қалпына келтіру сервер қосылғанда іске қосылады.';
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

  const firstError = form.querySelector('[aria-invalid="true"]');
  if (firstError) {
    firstError.focus();
    return;
  }
  status.textContent = 'Кіру формасы дұрыс толтырылды. Аккаунтты тексеру үшін backend қажет.';
});
