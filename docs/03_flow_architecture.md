# 🧠 03_Flow_Architecture: Análisis de la Lógica de Negocio

Este módulo es el conjunto de "scripts de especialidad". Define cómo el bot se comporta cuando entra en un dominio específico (Ventas, Inmobiliaria, Casino, etc.).

## 🧩 Estructura de los Flujos

El sistema utiliza un modelo de **Máquina de Estados Híbrida**:
1.  **Estado Global:** Gestionado por el motor principal (`engine.py`).
2.  **Estado de Flujo Local:** Gestionado por archivos `state.json` individuales por usuario (vía `flows/state.py`).

### Tipos de Flujos Identificados

#### A. Flujos de "Mensaje Único" (Stateless)
*   **Ejemplos:** `casino/main.py`, `celulares/main.py`, `cursos/main.py`, `inmobiliario/main.py`, `contact.py`, `instagram.py`, `whatsapp.py`.
*   **Funcionamiento:** Reciben el mensaje y devuelven un texto estático de bienvenida. No mantienen una conversación larga.
*   **Crítica:** Son muy básicos y sirven más como "placeholders" o disparadores de otros procesos.

#### B. Flujos de "Estado Complejo" (Stateful)
*   **Ejemplo:** `shop/main.py`.
*   **Funcionamiento:** Implementa una máquina de estados real (`step`: `choose_product` $ightarrow$ `choose_payment`).
*   **Mecanismo:** Utiliza el módulo `state.py` para persistir en qué paso de la compra se encuentra el usuario.

---

## 🔍 Análisis de Componentes Críticos

### 1. Gestión de Estado (`flows/state.py`)
*   **Mecanismo:** Guarda el estado del usuario en archivos JSON locales (`/user_data/{sender}/state.json`).
*   **Ventaja:** Muy fácil de implementar y depurar.
*   **🔴 Riesgo SaaS (Crítico):** 
    *   **Escalabilidad:** Almacenar el estado en archivos locales impide que el bot corra en múltiples servidores o contenedores (si el mensaje llega a la Instancia A y el siguiente a la Instancia B, el estado se pierde).
    *   **Solución SaaS:** El estado DEBE vivir en la base de datos centralizada (`db_manager.py`), no en archivos locales.

### 2. Interacción con Multi-Canal (`messenger.py`, `instagram.py`, `whatsapp.py`)
*   **Funcionamiento:** El sistema intenta abstraer la respuesta, pero cada canal tiene su propia lógica de envío (`send_message` para Messenger vs `send_msg` para WhatsApp).
*   **Crítica:** Hay una duplicación de lógica de envío. El motor debería tener un `Dispatcher` que unifique el envío según el canal detectado.

---

## ⚠️ Hallazgos de Auditoría (Flows)

### 🔴 Crítico: Dependencia de Archivos Locales para el Estado
El uso de `state.json` es el mayor impedimento para la escalabilidad horizontal. Si queremos usar Kubernetes o múltiples instancias de Python, el bot "olvidará" en qué paso estaba el usuario al cambiar de servidor.

### 🟠 Moderado: Fragmentación de la Lógica
La lógica de los flujos está muy dispersa. Algunos usan `handle_flow(cfg, sender, send_msg)` y otros requieren parámetros distintos. Esto dificulta la creación de un generador de flujos automático.

### 🟡 Menor: Falta de Validación de Entradas en Flujos
En el flujo de `shop`, si un usuario envía algo que no es un número, el bot responde, pero no hay un sistema de "limpieza" o validación de tipos de datos robusto.

---

## 📊 Matriz de Capacidades (Flows)

| Capacidad | Estado | Observación Técnica |
| :--- | :---: | :--- |
| **Navegación por Menús** | ✅ | Basada en ID y texto. |
| **Persistencia de Flujo** | ✅ | Funciona para un solo servidor (archivos locales). |
| **Multi-canal (FB/IG/WA)** | ✅ | Implementado pero con lógica duplicada. |
| **Escalabilidad de Estado** | ❌ | **FALTA:** El estado debe pasar de archivos a la DB. |
| **Interacción con IA** | ❌ | **FALTA:** No hay un "hook" para delegar el flujo a un LLM. |

---
**Estado del Módulo:** 🏗️ *Funcional para uso monoproceso, requiere migración de estado a DB para SaaS.*
