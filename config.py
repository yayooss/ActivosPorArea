from pocketbase import PocketBase
import os

# --- ASEGURAR QUE LA BD EXISTA EN EL PROYECTO
BASE_URL = "http://TU.RUTA.AQUI"
pb = PocketBase(BASE_URL)

pb.admins.auth_with_password("EMAIL@GMAIL.COM", "YOURPASSWORDHERE")
token = pb.auth_store.token

headers = {"Authorization": f'Bearer {token}'}