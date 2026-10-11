"""Legacy BETACODE/Devspark license format compatible with LicenseEncryption.cs.
Secrets must be server-side environment vars. NOTE: legacy desktop embeds them too;
therefore approval enforcement on the server cannot stop offline counterfeit keys.
"""
import base64
import hashlib
import hmac
import json
import os
from datetime import date
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7


def generate_legacy_license(device_id: str, license_type: str, expiry: date) -> str:
    enc_secret = os.environ.get('BETACODE_LICENSE_AES_SECRET')
    mac_secret = os.environ.get('BETACODE_LICENSE_HMAC_SECRET')
    if not enc_secret or not mac_secret:
        raise RuntimeError('Configure BETACODE_LICENSE_AES_SECRET and BETACODE_LICENSE_HMAC_SECRET')
    # Same DataContract names as the existing desktop model.
    payload = json.dumps({'DeviceId': device_id, 'Type': license_type, 'Expiry': expiry.isoformat()},
                         ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    key = hashlib.sha256(enc_secret.encode('utf-8')).digest()
    iv = os.urandom(16)
    padder = PKCS7(128).padder()
    padded = padder.update(payload) + padder.finalize()
    enc = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    encrypted = iv + enc.update(padded) + enc.finalize()
    signature = hmac.new(mac_secret.encode('utf-8'), encrypted, hashlib.sha256).digest()
    return base64.b64encode(encrypted).decode('ascii') + '.' + base64.b64encode(signature).decode('ascii')
