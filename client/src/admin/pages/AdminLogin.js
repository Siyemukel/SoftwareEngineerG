const loginBtn = document.getElementById('login-btn');
const identifierInput = document.getElementById('identifier');
const passwordInput = document.getElementById('password');

const studentOption = document.getElementById('student-option');
const staffOption = document.getElementById('staff-option');

const errorModal = document.getElementById('error-modal');
const errorMessage = document.getElementById('error-message');
const closeError = document.getElementById('close-error');

const successLoginModal = document.getElementById('success-login-modal');
const proceedSave = document.getElementById('proceed-save');

const saveModal = document.getElementById('save-modal');
const saveYes = document.getElementById('save-yes');
const saveNo = document.getElementById('save-no');

// Track role
let selectedRole = null;

// Role selection events
studentOption.addEventListener("click", () => {
  studentOption.classList.add("active");
  staffOption.classList.remove("active");
  identifierInput.placeholder = "Student Number";
  identifierInput.value = "";
  selectedRole = "student";
});

staffOption.addEventListener("click", () => {
  staffOption.classList.add("active");
  studentOption.classList.remove("active");
  identifierInput.placeholder = "Staff Number";
  identifierInput.value = "";
  selectedRole = "staff";
});

// Fake credentials
const validStudent = { id: "12345", password: "studpass" };
const validStaff = { id: "67890", password: "staffpass" };

// Login validation
loginBtn.addEventListener('click', function() {
  const identifier = identifierInput.value.trim();
  const password = passwordInput.value.trim();

  if (!selectedRole) {
    errorMessage.textContent = "Please select Student or Staff.";
    errorModal.style.display = 'flex';
    return;
  }

  if (identifier === "" || password === "") {
    errorMessage.textContent = "All fields are required.";
    errorModal.style.display = 'flex';
    return;
  }

  // Validate based on role
  if (selectedRole === "student") {
    if (identifier !== validStudent.id || password !== validStudent.password) {
      errorMessage.textContent = "Invalid student number or password.";
      errorModal.style.display = 'flex';
      return;
    }
  } else if (selectedRole === "staff") {
    if (identifier !== validStaff.id || password !== validStaff.password) {
      errorMessage.textContent = "Invalid staff number or password.";
      errorModal.style.display = 'flex';
      return;
    }
  }

  // Show success login modal
  successLoginModal.style.display = 'flex';
});

// Close error modal
closeError.addEventListener('click', function() {
  errorModal.style.display = 'none';
});

// Proceed to save password modal
proceedSave.addEventListener('click', function() {
  successLoginModal.style.display = 'none';
  saveModal.style.display = 'flex';
});

// Save password actions
saveYes.addEventListener('click', function() {
  alert("Password saved!");
  saveModal.style.display = 'none';
});
saveNo.addEventListener('click', function() {
  saveModal.style.display = 'none';
});
