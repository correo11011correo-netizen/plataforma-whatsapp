# Panel de Administración de Bots (Bot Admin Panel)

Este directorio contiene las herramientas, APIs y la interfaz de usuario para la **administración centralizada de todos los bots**. Se concibe como un proyecto independiente dentro del repositorio para facilitar su escalabilidad futura, ya que más adelante administrará múltiples bots y se le agregarán más opciones.

## Estructura del Proyecto

- `frontend/`: Contiene la interfaz gráfica (HTML, CSS, JS) del Dashboard de Administración. Se conecta al backend a través de la API para visualizar conversaciones, gestionar el modo "Bot" vs "Humano", y borrar chats.
- `backend/`: Código de la API (por ejemplo `dashboard_api.py`) dedicada exclusivamente a proveer datos a los paneles de control. *Actualmente, parte de la funcionalidad API la sirve directamente el `bot-engine`, pero aquí se alojarán los microservicios administrativos.*
- `cli/`: Herramientas de terminal (línea de comandos) para administración directa del servidor, bases de datos de los bots y utilidades puente (webhook bridge). Útil para operaciones de soporte técnico y mantenimiento manual.

## ¿Cómo interactúa el Frontend con la Base de Datos?

**Importante:** La página web (frontend) **NO** se conecta ni maneja la base de datos de forma directa. La arquitectura es la siguiente:

1. El navegador hace peticiones al Proxy (Webhook Recepcionista en el puerto `5000` o servidor Web).
2. El Proxy redirige el tráfico hacia el Backend (por ejemplo, el `Bot Engine` en el puerto `5001` o hacia el servicio de este panel en el `5002`).
3. El servicio Backend, utilizando Python (ej. `db_manager.py`), es quien se encarga de ejecutar de forma segura las consultas e inserciones en la base de datos SQLite (y futuras bases de datos).