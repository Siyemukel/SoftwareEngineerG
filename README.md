# SoftwareEngineerG

A full-stack web application with a React frontend and a Flask backend, designed as a Learning Disability Detector and Classifier System.

## Project Overview

Many university students underperform due to undiagnosed learning disabilities originating from early childhood. This system is developed in collaboration with the Disability Unit at DUT to enable early detection and intervention. The application assesses students through a series of targeted tests to identify potential learning disabilities. If a student fails a test, the system provides tailored exercises to help improve their skills and learning outcomes.

### Key features

- **Assessment:** Students complete a series of exercises/tests designed to detect learning disabilities.
- **Personalized Support:** If a student struggles with a test, the system recommends and delivers targeted exercises for improvement.
- **Reporting:** The system generates reports to help the Disability Unit provide adequate support to students.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Backend (Flask)](#backend-flask)
  - [API Routes](#api-routes)
- [Frontend (React)](#frontend-react)
  - [Routing](#routing)
- [Development](#development)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [License](#license)

---

## Project Structure

```bash
SoftwareEngineerG/
.
├── client
│   ├── eslint.config.js
│   ├── index.html
│   ├── node_modules
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   ├── public
|   └── src
|       ├── admin
|       │   ├── Admin.jsx
|       │   └── pages
|       ├── authentication
|       │   ├── Authentication.jsx
|       │   └── pages
|       ├── components
|       ├── landing
|       │   ├── Index.jsx
|       │   └── pages
|       ├── main.css
|       ├── main.jsx
|       ├── router.jsx
|       └── user
|           ├── pages
|           └── User.jsx
├── server
|   ├── app
|   ├── main.py
|   ├── requirements.txt
|   └── venv
├── LICENSE
└── README.md
```

---

## Backend (Flask)

- Located in [`server/`](server/)
- Uses Flask for API endpoints and routing.
- Entry point: [`main.py`](server/main.py)
- Blueprints organize routes for modularity.

### API Routes

- **Root:** `GET /`  
  Returns a welcome message.

- **Authentication:**  
  - `GET /auth/login`  
    Returns a login success message.
  - `GET /auth/signup`  
    Returns a signup success message.

> **Note:** These endpoints currently return static messages for demonstration.

---

## Frontend (React)

- Located in [`client/`](client/)
- Uses React with React Router for navigation.
- Tailwind CSS for styling.

### Routing

Defined in [`src/router.jsx`](client/src/router.jsx):

- `/`  
  - Home page
- `/auth/login`  
  - Login page
- `/auth/signup`  
  - Signup page
- `/user/dashboard`  
  - User dashboard
- `/admin/dashboard`  
  - Admin dashboard

Each section uses a layout component with nested routes for extensibility.

---

## Development

### Backend Setup

1. Navigate to `server/`

2. Install dependencies:

```sh
pip install -r requirements.txt
```

3. Run the server:

```sh
python main.py
```

### Frontend Setup

1. Navigate to `client/`

2. Install dependencies:

```sh
npm install
```

3. Start the development server:

```sh
npm run dev
```

---

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.
