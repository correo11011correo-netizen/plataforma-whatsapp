# 🛡️ 06_Security_Audit: Análisis de Vulnerabilidades y Riesgos

Este documento detalla los hallazgos de seguridad encontrados tras una auditoría exhaustiva del código fuente.

## 🚨 Hallazgos Críticos (Acción Inmediata Requerida)

### 1. Autenticación Inexistente / Simulada
* **Ubicación:** `bot-admin-panel/backend/dashboard_api.py` (Endpoint `/api/login`).
* **Problema:** El sistema de login devuelve un token estático (`token-falso-123`) y los endpoints posteriores no validan este token.
* **Riesgo:** Cualquier persona que descubra la URL de la API puede realizar peticiones para leer mensajes, cambiar el modo del bot o enviar mensajes masivos en nombre de la empresa.
* **Solución:** Implementar un sistema de autenticación basado en **JWT (JSON Web Tokens)** con expiración de tiempo y almacenamiento de usuarios en la base de datos.

### 2. Exposición de Secretos (Hardcoded/Env)
* **Ubicación:** `bot-manager/bot-engine/engine.py` y `.env`.
* **Problema:** El sistema depende de variables de entorno para tokens de Meta y Facebook. Si bien es mejor que tenerlos en el código, la gestión centralizada para un SaaS es inexistente.
* **Riesgo:** Si el servidor es comprometido, el acceso a la API de Meta es total.
* **Solución:** Implementar un gestor de secretos (Secret Manager) o cifrar los tokens en la base de datos antes de su almacenamiento.

---

## ⚠️ Hallazgos de Riesgo Moderado

### 1. Dependencia de Procesos Locales (Arquitectura de Seguridad)
* **Ubicación:** `bot-admin-panel/backend/dashboard_api.py`.
* **Problema:** El panel de administración importa directamente `engine.py` del motor del bot.
* **Riesgo:** Un fallo crítico en el motor puede tirar abajo el panel de administración (y viceversa). Además, esto impide que ambos servicios corran en contenedores/servidores separados.
* **Solución:** Comunicación exclusiva vía **API REST** entre el Panel y el Motor.

### 2. Gestión de Sesiones en Memoria
* **Ubicación:** `bot-manager/bot-engine/engine.py` (`processed_message_ids = set()`).
* **Problema:** La deduplicación de mensajes ocurre en la memoria RAM de un solo proceso.
* **Riesgo:** En un despliegue con múltiples instancias (escalabilidad), un mensaje duplicado podría ser procesado por una instancia diferente.
* **Solución:** Mover el registro de `message_id` procesados a la base de datos con una restricción de unicidad.

---

## 🟡 Hallazgos de Riesgo Menor

### 1. Integridad de la Base de Datos
* **Ubicación:** `bot-manager/bot-engine/db_manager.py`.
* **Problema:** La limpieza de conversaciones (`delete_conversation`) se gestiona manualmente por código.
* **Riesgo:** Riesgo de inconsistencia de datos (registros huérfanos) si se eliminan registros por fuera del flujo estándar.
* **Solución:** Utilizar restricciones `ON DELETE CASCADE` a nivel de esquema SQL.

---

## 📊 Resumen de Riesgos

| Categoría | Nivel | Impacto | Mitigación |
| :--- | :---: | :--- | :--- |
| **Acceso** | 🔴 Crítico | Control total de la plataforma por terceros. | Implementar JWT. |
| **Secretos** | 🟠 Moderado | Compromiso de la API de Meta. | Cifrado en DB / Secret Manager. |
| **Disponibilidad** | 🟠 Moderado | Caída de servicios por acoplamiento. | Separación mediante API REST. |
| **Consistencia** | 🟡 Menor | Datos corruptos o duplicados. | Persistencia de estados y deduplicación en DB. |

---
**Estado de Seguridad:** ⚠️ **NO APTO PARA PRODUCCIÓN.** Requiere una reestructuración completa de la capa de autenticación y comunicación.
