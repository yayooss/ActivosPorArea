from pocketbase import PocketBase
import os

# --- ASEGURAR QUE LA BD EXISTA EN EL PROYECTO
BASE_URL = "http://172.21.228.86:8090"
pb = PocketBase(BASE_URL)

pb.admins.auth_with_password("practicasryd@palliser.ca", "3**ARAgF")
token = pb.auth_store.token

headers = {"Authorization": f'Bearer {token}'}