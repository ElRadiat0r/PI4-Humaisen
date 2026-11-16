# PI4-Humaisen
L’expertise humaine, augmentée par l’IA


humaisen/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── config/                  # P1
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── dev.py
│   │   │   └── prod.py
│   │   ├── urls.py              # inclut les urls de chaque app
│   │   ├── asgi.py
│   │   └── wsgi.py
│   └── apps/
│       ├── core/                # P1 : permissions de base, utilitaires
│       ├── accounts/            # P1 : User, rôles, auth
│       ├── projects/            # P2 ← vous
│       ├── experts/             # P2 ← vous
│       ├── scheduling/          # P3 : AvailabilitySlot, Appointment
│       ├── matching/            # P3 : score et justification
│       └── reports/             # P5 : restitution, IA
├── frontend/                    # P4
├── docs/                        # P5 : contrats d'API, documentation
└── README.md