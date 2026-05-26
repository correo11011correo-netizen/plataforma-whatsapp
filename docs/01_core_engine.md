# ⚙️ 01_Core_Engine: Análisis de Procesamiento

Este módulo es el cerebro operativo del sistema. Su responsabilidad es la orquestación de mensajes, la gestión de la comunicación con la API de Meta y el control del flujo de conversación.

## 🧩 Estructura y Funciones Principales

### 1. Gestión de Configuración (`load_config`)
*   **Funcionamiento:** Carga parámetros críticos desde variables de entorno (`os.getenv`).
*   **Observación Técnica:** Actualmente es un punto de **acoplamiento fuerte** con el entorno del servidor. Para un SaaS, esta función debe evolucionar para consultar una base de datos basada en un `client_id`.
*   **Variables detectadas:** Token de WhatsApp, IDs de Facebook/Meta, tokens de verificación, y parámetros de testing.

### 2. Comunicación con Meta (`send_msg`, `upload_media`, `send_media_msg`)
*   **`send_msg`:** Implementación de mensajes de texto mediante `POST` a la Graph API de Facebook (v19.0).
*   **`upload_media`:** Gestión de la subida de archivos (binarios) para obtener un `media_id`.
*   **`send_media_msg`:** Envío de archivos usando el ID obtenido. Soporta imágenes, videos, audio y documentos.
*   **Crítica de Robustez:** El manejo de errores usa bloques `try-except` genéricos. Aunque imprime el error, la recuperación es limitada.

### 3. Orquestador de Mensajes (`process_message`)
Es la función de mayor complejidad. Sigue este flujo por cada mensaje entrante:

1.  **Deduplicación:** Utiliza `processed_message_ids` (un `set` en memoria) para evitar procesar el mismo `message_id` dos veces. 
    *   *Riesgo:* Al ser un `set` en memoria, si el servidor se reinicia, la lista se pierde, permitiendo duplicados temporales.
2.  **Logging y Persistencia:** Registra el mensaje en logs y lo inserta en la base de datos (`db_manager.add_message`).
3.  **Gestión de Intervención Humana:**
    *   Comandos: `!humano`, `asesor`, etc.
    *   **Lógica:** Activa un flag en la DB (`is_human_intervening`) y notifica al administrador.
    *   **Modo Bot:** Comando `!bot` para devolver el control al sistema.
4.  **Lógica de Navegación (El Árbol de Decisiones):**
    *   **Bienvenida:** Si el usuario dice "hola" o no tiene estado, se dispara el menú principal.
    *   **Navegación de Menús:** Si el usuario responde con un número o palabra clave, el motor busca en el diccionario de menús y actualiza el estado del usuario (`set_state`).
    *   **Acciones Especiales:** Soporta tipos de acción: `text`, `image`, `document`, `inventory` (catálogo) y `submenu`.

## ⚠️ Hallazgos de Auditoría (Engine)

### 🔴 Crítico: Acoplamiento de Configuración
El uso de `os.getenv` en `load_config` impide la multitenencia. No hay forma de tener dos clientes con tokens distintos corriendo en la misma instancia de `engine.py` sin cambiar el entorno.

### 🟠 Moderado: Gestión de Estado en Memoria
`processed_message_ids = set()` es peligroso para la consistencia en entornos distribuidos o tras reinicios. La deduplicación debería ser persistente en la base de datos.

### 🟡 Menor: Lógica de Menús en `process_message`
La función `process_message` es demasiado larga y hace demasiadas cosas (maneja mensajes, gestiona humanos, navega menús, gestiona catálogo). 
*   **Recomendación:** Aplicar el principio de **Responsabilidad Única**. Separar la lógica de navegación de la lógica de procesamiento de mensajes.

---
**Estado del Módulo:** 🏗️ *Funcional, pero requiere refactorización para escalabilidad SaaS.*
