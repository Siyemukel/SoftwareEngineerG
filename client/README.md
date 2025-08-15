# Frontend (React)

This directory contains the React frontend for the SoftwareEngineerG project, a Learning Disability Detector and Classifier System.

## Overview

- **Framework:** React (with Vite for fast development)
- **Styling:** Tailwind CSS
- **Routing:** React Router v7

The frontend provides user interfaces for students, admins, and authentication, communicating with the backend API.

---

## Project Structure

```bash
client/
├── public/                # Static assets 
├── src/
│   ├── admin/             # Admin dashboard and pages
│   │   ├── Admin.jsx
│   │   └── pages/
│   │       └── AdminDashboard.jsx
│   ├── authentication/    # Auth pages and logic
│   │   ├── Authentication.jsx
│   │   └── pages/
│   │       ├── Login.jsx
│   │       └── Signup.jsx
│   ├── components/        # Shared React components (future use)
│   ├── landing/           # Landing and home pages
│   │   ├── Index.jsx
│   │   └── pages/
│   │       └── Home.jsx
│   ├── user/              # User dashboard and pages
│   │   ├── User.jsx
│   │   └── pages/
│   │       └── UserDashboard.jsx
│   ├── main.css           # Tailwind CSS entrypoint
│   ├── main.jsx           # App entrypoint
│   └── router.jsx         # App routes
├── index.html             # HTML template
├── package.json           # NPM dependencies and scripts
├── vite.config.js         # Vite configuration
└── eslint.config.js       # ESLint configuration
```

---

## Routing

Routes are defined in [`src/router.jsx`](src/router.jsx):

- `/`  
  - Home page (`landing/pages/Home.jsx`)
- `/auth/login`  
  - Login page (`authentication/pages/Login.jsx`)
- `/auth/signup`  
  - Signup page (`authentication/pages/Signup.jsx`)
- `/user/dashboard`  
  - User dashboard (`user/pages/UserDashboard.jsx`)
- `/admin/dashboard`  
  - Admin dashboard (`admin/pages/AdminDashboard.jsx`)

Each section uses a layout component with nested routes for extensibility.

---

## Styling

- Tailwind CSS is used for utility-first styling.
- Main styles are imported in [`src/main.css`](src/main.css).

---

## Development

### Setup

1. Install dependencies:

    ```sh
    npm install
    ```

2. Start the development server:

    ```sh
    npm run dev
    ```

3. The app will be available at `http://localhost:5173` (default Vite port).

---

## Useful References

- [Vite Documentation](https://vite.dev/guide/)
- [React Router Documentation](https://reactrouter.com/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs/installation/using-vite)

---
