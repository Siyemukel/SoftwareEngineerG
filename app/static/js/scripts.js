// ----------------  Home  ----------------  //
document.addEventListener('DOMContentLoaded', () => {
    const images = document.querySelectorAll('.hero-slider img');
    let currentIndex = 0;
    const intervalTime = 3000;

    function showImage(index) {
        images.forEach((img, i) => {
            img.classList.remove('active');
            if (i === index) {
                img.classList.add('active');
            }
        });
    }

    function nextImage() {
        currentIndex = (currentIndex + 1) % images.length;
        showImage(currentIndex);
    }

    setInterval(nextImage, intervalTime);
});

// ---------------- Authentication
document.addEventListener('DOMContentLoaded', function() {
  const signupForm = document.getElementById('signupForm');
  const successModal = document.getElementById('successModal');
  const continueBtn = document.getElementById('continueBtn');

  signupForm.addEventListener('submit', function(e) {
    e.preventDefault();
    successModal.style.display = 'flex';
  });

  continueBtn.addEventListener('click', function() {
    successModal.style.display = 'none';
    alert('Redirecting to Dashboard...');
  });
});

// ====== LOGIN JS ======
const loginBtn = document.getElementById('login-btn');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const rememberCheckbox = document.querySelector('.remember-section input[type="checkbox"]');

const errorModal = document.getElementById('error-modal');
const errorMessage = document.getElementById('error-message');
const closeError = document.getElementById('close-error');

const successLoginModal = document.getElementById('success-login-modal');
const proceedSave = document.getElementById('proceed-save');

const saveModal = document.getElementById('save-modal');
const saveYes = document.getElementById('save-yes');
const saveNo = document.getElementById('save-no');

// Check if email ends with @dut4life.ac.za
function isValidEmail(email) {
  return email.toLowerCase().endsWith("@dut4life.ac.za");
}

// Login validation
loginBtn.addEventListener('click', function() {
  const email = emailInput.value.trim();
  const password = passwordInput.value.trim();

  if (email === "" || password === "") {
    errorMessage.textContent = "All fields are required.";
    errorModal.style.display = 'flex';
    return;
  }

  if (!isValidEmail(email)) {
    errorMessage.textContent = "Invalid email or password";
    errorModal.style.display = 'flex';
    return;
  }

  // ✅ Valid DUT email → show success popup
  successLoginModal.style.display = 'flex';
});

// Close error modal
closeError.addEventListener('click', function() {
  errorModal.style.display = 'none';
});

// Proceed after success login
proceedSave.addEventListener('click', function() {
  successLoginModal.style.display = 'none';

  // Only show save password modal if "Remember me" is NOT checked
  if (!rememberCheckbox.checked) {
    saveModal.style.display = 'flex';
  }
});

// Save password actions
saveYes.addEventListener('click', function() {
  alert("Password saved!");
  saveModal.style.display = 'none';
});
saveNo.addEventListener('click', function() {
  saveModal.style.display = 'none';
});
