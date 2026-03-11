# Panel de Administración de Bots (Bot Admin Panel)

Este directorio contiene las herramientas, APIs y la interfaz de usuario para la **administración centralizada de todos los bots**. Se concibe como un proyecto independiente dentro del repositorio para facilitar su escalabilidad futura, ya que más adelante administrará múltiples bots y se le agregarán más opciones.

## Estructura del Proyecto (Arquitectura de Panel Doble)

El sistema de administración visual está dividido en dos aplicaciones Frontend separadas para mayor seguridad y enfoque de las tareas:

- `frontend/`: Contiene la interfaz gráfica (HTML, CSS, JS) del **Dashboard de Conversaciones**. Se sirve estáticamente vía Apache (`fundacionidear.com/dashboard/`). Permite a los agentes humanos ver chats en vivo, tomar el control de una conversación, enviar mensajes e imágenes, y borrar chats de forma segura mediante peticiones `POST`.
- `frontend-settings/`: Contiene el **Constructor Dinámico de Menús en Línea**. Esta interfaz avanzada se sirve desde el backend (`api.fundacionidear.com/dashboard`). Permite configurar los textos globales, crear categorías, agregar opciones en línea con numeración automática, y enlazar submenús visualmente sin tocar la base de datos de forma directa.
- `backend/`: Código de la API heredada (por ejemplo `dashboard_api.py`). *Actualmente, la funcionalidad API la sirve directamente el `bot-engine` (puerto 5001).*
- `cli/`: Herramientas de terminal (línea de comandos) para administración directa del servidor. Útil para operaciones de soporte técnico y mantenimiento manual.

## ¿Cómo interactúa el Frontend con la Base de Datos?

**Importante:** La página web (frontend) **NO** se conecta ni maneja la base de datos de forma directa. La arquitectura es la siguiente:

1. El navegador hace peticiones al Proxy (Webhook Recepcionista en el puerto `5000` o servidor Web).
2. El Proxy redirige el tráfico hacia el Backend (por ejemplo, el `Bot Engine` en el puerto `5001` o hacia el servicio de este panel en el `5002`).
3. El servicio Backend, utilizando Python (ej. `db_manager.py`), es quien se encarga de ejecutar de forma segura las consultas e inserciones en la base de datos SQLite (y futuras bases de datos).