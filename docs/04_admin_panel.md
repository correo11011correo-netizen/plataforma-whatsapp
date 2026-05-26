# 🖥️ 04_Admin_Panel: Análisis de la Interfaz de Control

Este módulo es la capa de interacción humana. Permite a los administradores gestionar los chats, intervenir en conversaciones y controlar el estado del bot.

## 🧩 Estructura y Flujo

### 1. Backend (API de Control - `dashboard_api.py`)
El backend es un servidor **Flask** que actúa como puente entre el frontend y la base de datos/motor.

*   **Seguridad (Punto Crítico):** 
    *   Implementa un login con credenciales "quemadas" (`admin` / `idear2024`).
    *   El "token" devuelto es un string estático (`token-falso-123`).
    *   **Riesgo:** La seguridad es puramente demostrativa. No hay validación real de JWT o sesiones en los endpoints.
*   **Endpoints Principales:**
    *   `GET /api/chats`: Lista conversaciones con metadatos (último mensaje, estado de intervención).
        *   `GET /api/chats/<phone>/messages`: Recupera el historial de un chat específico.
    *   `POST /api/chats/<phone>/toggle`: Cambia el modo de la conversación (Bot $\leftrightarrow$ Humano).
    *   `POST /api/chats/<phone>/send`: Envía mensajes desde la interfaz (simulando al humano).
*   **Integración de Motor:** Importa `send_msg` del `bot-manager` para permitir que el panel envíe mensajes reales a través de la API de Meta.

### 2. Frontend (Interfaz de Usuario)
Una aplicación **SPA (Single Page Application)** construida con Vanilla JS, CSS y HTML.

*   **Arquitectura de la UI:**
    *   **Sidebar:** Lista de chats con indicadores visuales de estado (👤 Humano vs 🤖 Bot).
    *   **Chat View:** Área de visualización de mensajes con scroll automático y diseño similar a WhatsApp Web.
    *   **Modo Responsivo:** Implementa un diseño móvil con ocultación de sidebar y botón de retorno.
*   **Lógica de Interacción (`script.js`):**
    *   **Polling de Datos:** Utiliza `setInterval` para actualizar la lista de chats y los mensajes de un chat activo cada 3-5 segundos.
    *   **Optimistic UI:** Al enviar un mensaje, la interfaz lo muestra inmediatamente con una opacidad reducida antes de la confirmación del servidor para mejorar la percepción de velocidad.
    *   **Gestión de Multimedia:** Incluye soporte para adjuntar archivos mediante un input oculto disparado por un botón.

---

## ⚠️ Hallazgos de Auditoría (Admin Panel)

### 🔴 Crítico: Seguridad de Acceso Nula
*   **Problema:** El sistema de login es simulado. Cualquier usuario que conozca el endpoint puede realizar peticiones sin un token válido o con un token estático.
*   **Impacto:** Un atacante podría tomar el control total de todos los bots, leer chats privados y enviar mensajes masivos.
*   **Requerimiento SaaS:** Implementar **JWT (JSON Web Tokens)** con expiración y una base de datos de usuarios/administradores.

### 🟠 Moderado: Acoplamiento del Backend
*   **Problema:** El backend del panel depende directamente del código del `bot-manager` (importa `engine.py`).
*   **Impacto:** Si el motor del bot tiene un error o se actualiza, el panel puede romperse.
*   **Recomendación:** El panel debería comunicarse con el motor exclusivamente a través de una API interna (ej. REST o gRPC), no mediante importaciones de Python.

### 🟡 Menor: UX de Carga de Multimedia
*   **Problema:** La carga de archivos no tiene una barra de progreso visual real, solo un mensaje optimista.
*   **Impacto:** En conexiones lentas, el usuario puede pensar que la aplicación se ha congelado.

---

## 📊 Matriz de Capacidades (Admin Panel)

| Capacidad | Estado | Observación Técnica |
| :--- | :---: | :--- |
| **Visualización de Chats** | ✅ | Lista dinámica con metadatos. |
| **Intervención Humana** | ✅ | Control de flag en tiempo real. |
| **Envío de Mensajes** | ✅ | Integrado con el motor de envío. |
| **Gestión de Archivos** | ✅ | Soporte para adjuntos vía API. |
| **Autenticación Real** | ❌ | **FALTA:** Implementar JWT y gestión de usuarios. |
| **Aislamiento de API** | ❌ | **FALTA:** El panel debe ser un cliente de una API, no una extensión del motor. |

---
**Estado del Módulo:** 🏗️ *Funcional como prototipo de control, pero inseguro para producción.*
