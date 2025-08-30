SoftwareEngineering/
.
├── run.py                  # Entry point
├── config.py               # Configuration (DB, secret key)
├── requirements.txt        # Python dependencies
├── /app
│   ├── __init__.py         # Initializes Flask, DB, Login Manager
│   ├── models.py           # SQLAlchemy models
│   ├── forms.py            # WTForms for login/signup
│   ├── router.py           # Routes (home, auth, dashboards, etc.)
│   ├── /templates
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── admin_dashboard.html
│   │   └── customer_dashboard.html
│   └── /static
│       ├── style.css
│       └── interation.js
└── venv/                   # Virtual environment