# GENERATE ENCRYPTED PASSWORD WITH BCRYPT
# STORE THE DECODED HASHED PASSWORD IN YOUR MONGO DB IN THE USER COLLECTION ROOT
# ALONG WITH A USERNAME
# PASSWORD HAS TO BE ENCODED INTO BYTES
import os
import base64
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def hash_password(password):

    # THIS HASHES THE PASSWORD ABOVE
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    return hashed.decode("utf-8").strip()


def generate_key(password, salt=os.urandom(16)):

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=1_000_000,
    )

    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8"))), salt


def encrypt_message(message, password):
    """Encrypts a message using the provided password."""

    key, salt = generate_key(password)

    f = Fernet(key)

    encrypted_message = f.encrypt(message.encode())

    return encrypted_message, salt


def decrypt_message(encrypted_message, password, salt):
    """Decrypts a message using the provided password and salt."""

    key, salt_flat = generate_key(password, salt)

    f = Fernet(key)

    decrypted_message = f.decrypt(encrypted_message).decode()

    return decrypted_message
