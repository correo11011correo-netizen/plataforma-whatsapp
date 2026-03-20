# Motor del Bot (Bot Engine) - Arquitectura 100% Base de Datos

Este directorio contiene el "cerebro" del bot de WhatsApp (`engine.py`) y sus servicios anexos. 
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

## Comportamiento Principal (`engine.py`)

- **Palabras Clave Globales:** `hola`, `buenas`, `/start` -> Despliegan el Mensaje de Bienvenida y el listado automático de todas las Categorías en cualquier momento.
- **Mensajes Libres (Nuevas conversaciones):** Si el usuario escribe cualquier cosa y NO está navegando dentro de un submenú, el bot le dará la bienvenida y le mostrará el menú principal (siempre y cuando la palabra no coincida con el nombre directo de una categoría existente).
- **Navegación por Nombre o Número:** Los usuarios pueden digitar un número de opción cuando están en un submenú, o escribir el nombre exacto de la categoría (ej: `ventas`) para saltar directamente a ella.
- **Vuelta Atrás:** `volver`, `menu`, `opciones` -> Limpian la memoria (estado) del usuario y lo regresan al menú principal.
- **Intervención Humana:** Si en la base de datos el contacto tiene `is_human_intervening = 1` (controlado desde el Panel de Chats en `fundacionidear.com/dashboard/`), este motor ignora todos los mensajes del usuario hasta que el agente humano lo libere.

## Sistema de Notificaciones (`notifier.py`)

Se ha incorporado un script independiente (`notifier.py`) encargado de alertar al administrador sobre nuevos mensajes entrantes.

**¿Cómo funciona?**
- Se ejecuta automáticamente cada 10 minutos mediante una tarea **Cron** en el servidor de Linux.
- Lee los últimos 5 mensajes de clientes desde la base de datos.
- Revisa un archivo temporal (`last_notification_time.txt`). Si hay algún mensaje con una fecha más reciente a la guardada allí, envía una alerta al WhatsApp del administrador mostrando un resumen de los chats.
- Si no hay actividad nueva, se silencia para no hacer spam.

### 🛠️ ¿Cómo editar las Notificaciones sin romper el código?

**1. Cambiar el número que recibe las alertas:**
Abre el archivo `notifier.py` y modifica la variable `NOTIFY_NUMBER` (línea 7 aprox.):
```python
NOTIFY_NUMBER = "5493765245980" # <-- Cambia esto por tu nuevo número con código de país
```
*(Nota: Asegúrate de dejar las comillas y no usar el símbolo +).*

**2. Cambiar cada cuánto tiempo se envía la alerta:**
Las notificaciones no se controlan desde Python, sino desde el servidor Linux (Cron). Para cambiar el intervalo de 10 minutos:
1. Conéctate por SSH al servidor (`gcloud compute ssh mi-servidor-web...`)
2. Ejecuta el comando: `crontab -e`
3. Busca la línea que dice:
   `*/10 * * * * cd /home/nestorfabianriveros2014/bot-manager/bot-engine && ...`
4. Cambia el `*/10` por los minutos que desees. Ejemplos:
   - `*/5` -> Cada 5 minutos.
   - `0 * * * *` -> Cada 1 hora en punto.

## Archivos Clave

- `engine.py`: El procesador principal de lógica (completamente reescrito, sin dependencias a flujos estáticos).
- `notifier.py`: Script de alertas automáticas vía Cron.
- `db_manager.py`: Contiene todas las funciones SQL seguras para extraer y escribir datos (ej. `get_all_menus()`, `delete_conversation()`).
- `server.py`: El servidor Flask que recibe los webhooks de Meta, los pasa a `engine.py`, y además expone la API para que el panel de control web pueda configurar el bot.
