# Motor del Bot (Bot Engine) - Arquitectura 100% Base de Datos

Este directorio contiene el "cerebro" del bot de WhatsApp (`engine.py`). 
Tras una reestructuración profunda, este motor ahora utiliza una arquitectura **"Zero-Code"** basada íntegramente en la base de datos.

## ¿Qué significa Arquitectura 100% Base de Datos?

En versiones anteriores, cada menú, respuesta o flujo especial (como el carrito de compras o atención al cliente) requería la creación y modificación de archivos `.py` dentro de la carpeta `flows/`. Esto obligaba a reiniciar el servidor cada vez que se cambiaba un texto.

**Ahora, el código Python es estático y universal:**
1. **Punto Único de Verdad:** Cuando un usuario envía un mensaje, el archivo `engine.py` intercepta el texto y consulta la base de datos SQLite (`bot_dashboard.db`) en **tiempo real**.
2. **Sin reinicios:** Cualquier cambio que hagas en el "Editor de Opciones del Bot" (la web en `api.fundacionidear.com/dashboard`) se guarda instantáneamente en la base de datos. El siguiente mensaje que reciba el bot ya usará la nueva configuración sin necesidad de tocar el servidor.
3. **Navegación Dinámica:**
   - La base de datos almacena "Categorías" (Menús) y sus "Opciones".
   - El bot utiliza la función de "estado" (`flows/state.py`) para recordar en qué Categoría está cada usuario (ej. si está dentro de 'Soporte').
   - Cuando el usuario digita un número (ej. '1'), el bot busca qué acción debe ejecutar ('Responder Texto' o 'Abrir Submenú') leyendo la base de datos en vivo.

## Comportamiento Principal

- **Palabras Clave Globales:** `hola`, `buenas`, `/start` -> Despliegan el Mensaje de Bienvenida y el listado automático de todas las Categorías.
- **Vuelta Atrás:** `volver`, `menu`, `opciones` -> Limpian la memoria (estado) del usuario y lo regresan al menú principal.
- **Intervención Humana:** Si en la base de datos el contacto tiene `is_human_intervening = 1` (controlado desde el Panel de Chats en `fundacionidear.com/dashboard/`), este motor ignora todos los mensajes del usuario hasta que el agente humano lo libere.

## Archivos Clave

- `engine.py`: El procesador principal de lógica (completamente reescrito, sin dependencias a flujos estáticos).
- `db_manager.py`: Contiene todas las funciones SQL seguras para extraer y escribir datos (ej. `get_all_menus()`, `delete_conversation()`).
- `server.py`: El servidor Flask que recibe los webhooks de Meta, los pasa a `engine.py`, y además expone la API para que el panel de control web pueda configurar el bot.