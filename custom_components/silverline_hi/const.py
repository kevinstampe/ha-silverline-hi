"""Constants for Silverline Hi+ integration."""

DOMAIN = "silverline_hi"
SCAN_INTERVAL = 30  # seconds

# Firebase config (from the Silverline Hi+ app)
FIREBASE_API_KEY = "AIzaSyCqqw4cNYr1NmCxqenllCCu7kKKT4oJyC4"
FIREBASE_PROJECT_ID = "silverlinehi2020"

# API endpoints
AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
COMMAND_URL = "https://hi.silverline.kuartis.com/command"
DEVICE_STATE_URL = "https://hi.silverline.kuartis.com/deviceState"
FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents"

# Command component IDs
COMPONENT_VENTILATION = 1
COMPONENT_LIGHT = 2
COMPONENT_FILTER = 2

# Filter lifetimes used when resetting (minutes)
CARBON_FILTER_LIFETIME = 18000
GREASE_FILTER_LIFETIME = 7200
