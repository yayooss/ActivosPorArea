import io
import json
from nicegui import ui, app
import requests
import base64
from datetime import datetime, timezone
from config import *
import cv2
import os

BACKUP_FILE = "backup_activos.json"


# --- CAMERA ---
video_capture = None


def init_camera():
    global video_capture
    for i in range(3):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            video_capture = cap
            return
    video_capture = None


init_camera()


@app.on_shutdown
def close_camera():
    if video_capture:
        video_capture.release()


def get_frame():
    if not video_capture:
        return None

    ret, frame = video_capture.read()
    if not ret:
        return None

    _, buffer = cv2.imencode('.jpg', frame)
    return f'data:image/jpeg;base64,{base64.b64encode(buffer).decode()}'


# --- STATE ---
current_image = None   # 👈 UN SOLO ESTADO
current_file = None

# --- CAMERA ---
def take_snapshot():
    global current_image, current_file

    if not video_capture:
        ui.notify('No hay cámara', type='warning')
        return

    ret, frame = video_capture.read()
    if ret:
        _, buffer = cv2.imencode('.jpg', frame)

        current_file = io.BytesIO(buffer.tobytes())
        current_image = f'data:image/jpeg;base64,{base64.b64encode(buffer).decode()}'

        form_view.refresh()


def clear_image():
    global current_image, current_file
    current_image = None
    current_file = None
    form_view.refresh()


# --- CLIPBOARD ---
async def paste_from_clipboard():
    global current_image, current_file

    js = """
        const items = await navigator.clipboard.read();
        for (const item of items) {
            for (const type of item.types) {
                if (type.startsWith('image/')) {
                    const blob = await item.getType(type);
                    const reader = new FileReader();
                    return await new Promise(resolve => {
                        reader.onload = () => resolve(reader.result);
                        reader.readAsDataURL(blob);
                    });
                }
            }
        }
        return null;
    """

    result = await ui.run_javascript(js)

    if result:
        current_image = result
        header, data = result.split(',', 1)
        current_file = io.BytesIO(base64.b64decode(data))

        form_view.refresh()
        ui.notify('Imagen cargada', type='positive')
    else:
        ui.notify('No hay imagen en portapapeles', type='warning')

# --- ACTIVOS ---
def fetch_activos():
    try:
        r = requests.get(f"{BASE_URL}/api/collections/activos/records?perPage=200", headers=headers)
        if r.status_code == 200:
            return r.json().get('items', [])
        return []
    except Exception as e:
        print("Error fetching: ",e)
        return []

# --- AGRUPAR POR AREA ---
def group_by_area(items):
    grouped = {}
    for item in items:
        area = item.get('area', 'Sin area')
        grouped.setdefault(area, []).append(item)
    return grouped

# --- SAVE ---
def submit_form(data):
    if not current_file:
        ui.notify('Falta imagen', type='negative')
        return

    try:

        payload = {
            'name': data.get('name'),
            'area': data.get('area'),
            'description': data.get('description'),
            'properties': json.dumps(data.get('properties', {}), ensure_ascii=False)
        }

        current_file.seek(0)
        files = {
            'photo': ('image.jpg', current_file, 'image/jpeg')
        }

        r = requests.post(
            f"{BASE_URL}/api/collections/activos/records",
            data=payload,
            files=files,
            headers=headers
        )

        if r.status_code not in (200, 201):
            print("STATUS:", r.status_code)
            print("RESPONSE:", r.text)
            print(r.json())
            print("PAYLOAD:", payload)
            print("FILE SIZE:", current_file.getbuffer().nbytes)

        if r.status_code in (200, 201):
            ui.notify('Guardado en BD', type='positive')
            clear_image()
            activos.refresh()
        else:
            ui.notify(f'Error: {r.text}', type='negative')

    except Exception as e:
        ui.notify(f'Error conexión: {e}', type='negative')


# --- UI ---
@ui.refreshable
def form_view():
    with ui.row().classes('w-full gap-6'):

        # --- CAMARA / IMAGEN UNICA ---
        with ui.card().classes('flex-1 p-4'):
            ui.label('📷 Cámara / Imagen')

            with ui.element('div').classes('relative w-full h-[420px]'):

                # SI HAY IMAGEN → SOLO MOSTRAR ESA
                if current_image:
                    ui.image(current_image)\
                        .classes('w-full h-full object-cover rounded')

                    ui.button(icon='close', on_click=clear_image)\
                        .props('round dense color=negative')\
                        .classes('absolute top-2 right-2')

                # SI NO HAY → CAMARA EN VIVO
                else:
                    live = ui.interactive_image()\
                        .classes('w-full h-full rounded bg-gray-100')

                    ui.timer(0.15, lambda: live.set_source(get_frame()))

            # BOTONES
            with ui.row().classes('w-full justify-center items-center gap-6 mt-3'):

                ui.button(icon='photo_camera', on_click=take_snapshot)\
                    .props('round color=purple-6')\
                    .classes('w-8 h-8')

                ui.button(icon='content_paste', on_click=paste_from_clipboard)\
                    .props('round color=secondary')\
                    .classes('w-8 h-8')

        # --- FORM ---
        with ui.card().classes('flex-1 p-6'):

            ui.label('📝 Nuevo Activo').classes('text-lg font-bold mb-4')

            with ui.row().classes('w-full gap-3'):
                name = ui.input('Nombre').classes('flex-1')
                area = ui.input('Área').classes('flex-1')

            description = ui.textarea('Descripción').classes('w-full')

            properties = []
            ui.label('⚙️Propiedades').classes('mt-4 font-bold')
            container = ui.column().classes('w-full gap-2')

            def add_property():
                with container:
                    with ui.row().classes('w-full gap-2'):
                        k = ui.input('Clave').classes('flex-1')
                        v = ui.input('Valor').classes('flex-1')
                        properties.append((k, v))

            ui.button('+ Agregar propiedad', on_click=add_property).props('color=teal').classes('mt-2')

            def guardar():
                props = {
                    k.value: v.value
                    for k, v in properties
                    if k.value
                }

                submit_form({
                    'name': name.value,
                    'area': area.value,
                    'description': description.value,
                    'properties': props
                })

            ui.button('Guardar', on_click=guardar).props('color=green-7').classes('w-full mt-4')

# --- ACTIVOS ---
@ui.refreshable
def activos():
    items = fetch_activos()
    grouped = group_by_area(items)

    # --- DIALOGO PARA ZOOM ---
    with ui.dialog() as zoom_dialog, ui.card().classes('p-0 overflow-hidden w-full max-w-[95vw] h-auto max-h-[100vh]'):
        zoom_img = ui.image('').classes('w-full h-full object-contain')

    def open_zoom(url):
        zoom_img.set_source(url)
        zoom_dialog.open()

    with ui.column().classes('w-full gap-6'):
        for area, activos_list in grouped.items():
            with ui.row().classes('items-center gap-3 mt-4'):
                ui.icon('folder').classes('text-gray-500 text-2xl text-center')
                ui.label(f'- {area}').classes('text-xl font-semibold text-gray-800')
                ui.element('div').classes('flex-grow h-[1px] bg-gray-200')

            with ui.grid(columns=3).classes('w-full gap-5'):
                for a in activos_list:
                    with ui.card().classes('p-0 rounded-2xl border border-gray-100'
                                        'shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden'):
                        # --- IMG ---
                        if a.get('photo'):
                            img_url = f"{BASE_URL}/api/files/activos/{a['id']}/{a['photo']}"
                            ui.image(img_url) \
                                .classes('w-full h-44 object-contain bg-gray-50 cursor-pointer') \
                                .on('click', lambda _, url=img_url: open_zoom(url))

                        with ui.column().classes('p-4 gap-3'):
                            # --- INFO ---
                            ui.label(a.get('name')).classes('text-lg font-bold text-gray-900')

                            # --- DESC ---
                            if a.get('description'):
                                ui.label(f"Descripción: {a.get('description')}").classes('text-sm text-gray-500')

                            # --- PROPIEDADES ---
                            try:
                                props = a.get('properties', {})
                                if isinstance(props, str):
                                    props = json.loads(props)

                                if props:
                                    ui.label('Propiedades:').classes('text-sm font-semibold text-gray-700 mt-1')

                                    # Usamos flex-wrap para que si no caben horizontalmente, bajen a la siguiente fila
                                    with ui.row().classes('w-full flex-wrap gap-2'):
                                        # Quitamos el [:3] para que recorra TODAS las propiedades
                                        for k, v in props.items():
                                            ui.label(f'{k}: {v}') \
                                                .classes(
                                                'text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-md border border-gray-200')
                            except:
                                pass


# --- HEAD JS (ENTER = PEGAR) ---
ui.add_head_html("""
<script>
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        window.dispatchEvent(new Event('paste_trigger'));
    }
});
</script>
""", shared=True)

ui.on('paste_trigger', lambda _: ui.run_async(paste_from_clipboard()))


# --- MAIN ---
with ui.column().classes('w-full p-6'):

    tabs = ui.tabs().classes('w-full')

    with tabs:
        t1 = ui.tab('Nuevo Activo')
        t2 = ui.tab('Activos')

    with ui.tab_panels(tabs, value=t1).classes('w-full'):
        with ui.tab_panel(t1):
            form_view()

        with ui.tab_panel(t2):
            activos()


ui.run(port=8085)
