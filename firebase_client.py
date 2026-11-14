"""Firebase Authentication (email/password) via the REST API."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://identitytoolkit.googleapis.com/v1/accounts:"

ERROR_MESSAGES = {
    "EMAIL_EXISTS": "This email is already registered. Please sign in instead.",
    "INVALID_EMAIL": "The email address is not valid.",
    "MISSING_PASSWORD": "Please enter a password.",
    "WEAK_PASSWORD": "Password must be at least 6 characters.",
    "EMAIL_NOT_FOUND": "Wrong email or password.",
    "INVALID_PASSWORD": "Wrong email or password.",
    "INVALID_LOGIN_CREDENTIALS": "Wrong email or password.",
    "USER_DISABLED": "This account has been disabled.",
    "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many attempts. Please try again later.",
}

class AuthError(Exception):
    """Sign-in / sign-up error; the message is ready to show to the user."""

def _call(endpoint: str, email: str, password: str) -> dict:
    api_key = os.getenv("FIREBASE_API_KEY", "").strip()
    if not api_key:
        raise AuthError("FIREBASE_API_KEY is missing in the .env file.")

    try:
        response = requests.post(
            f"{BASE_URL}{endpoint}?key={api_key}",
            json={"email": email, "password": password, "returnSecureToken": True},
            timeout=10,
        )
    except requests.RequestException:
        raise AuthError("Cannot reach Firebase. Please check your internet connection.")

    data = response.json()
    if response.status_code != 200:
        raw = data.get("error", {}).get("message", "UNKNOWN")
        if "API key not valid" in raw:
            raise AuthError("FIREBASE_API_KEY in .env is not valid.")
        code = raw.split(" ")[0]  # "WEAK_PASSWORD : Password should..." -> "WEAK_PASSWORD"
        raise AuthError(ERROR_MESSAGES.get(code, f"Authentication failed ({code})."))

    return {"email": data["email"], "uid": data["localId"], "id_token": data["idToken"]}

def sign_up(email: str, password: str) -> dict:
    return _call("signUp", email, password)

def sign_in(email: str, password: str) -> dict:
    return _call("signInWithPassword", email, password)