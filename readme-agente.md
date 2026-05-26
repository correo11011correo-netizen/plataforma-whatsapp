# 🕵️ README-AGENTE: Auditoría Técnica y Mapa de Ruta SaaS

**DOCUMENTO DE CONTROL INTERNO. USO EXCLUSIVO PARA ARQUITECTURA Y DESARROLLO.**

Este documento detalla la realidad técnica actual del proyecto y la brecha tecnológica que debe cerrarse para transformarlo de un sistema de automatización local en un modelo de Software as a Service (SaaS) de bajo coste operativo.

---

## 🏗️ 1. ANÁLISIS DE ARQUITECTURA ACTUAL

El sistema opera bajo una arquitectura de **Procesamiento de Eventos Basado en Estados (Stateful Event Processing)**.

### Flujo de Datos:
1.  **Entrada:** Webhook de Meta $ightarrow$ `engine.py`.
2.  **Identificación:** `engine.py` consulta `db_manager.py` para recuperar el contexto del usuario (ID, último menú, estado de intervención).
3.  **Decisión:** El motor evalúa el comando contra la estructura de menús en la DB.
4.  **Salida:** Respuesta vía API de Meta.

### Componentes Tecnológicos:
*   **Motor (Core):** Python (Síncrono/Bloqueante por naturaleza en su estado actual).
*   **Persistencia:** SQLite (Archivo local).
*   **Interfaz:** Dashboard Web (Node.js/JS).

---

## 📊 2. MATRIZ DE CAPACIDADES: [HECHO] vs [FALTA]

Para alcanzar el estándar SaaS, se debe completar la siguiente matriz:

| Capacidad | Estado | Observación Técnica |
| :--- | :---: | :--- |
| **Gestión de Flujos (Menús)** | ✅ | Implementado mediante estructura de árbol en DB. |
| **Intervención Humana** | ✅ | Sistema de flag en DB para pausar el bot. |
| **Gestión de Contactos** | ✅ | Registro básico de números y nombres. |
| **Multitenencia (Multi-usuario)** | ❌ | **FALTA:** El sistema actual asume una única configuración global. Un SaaS requiere que cada cliente tenga sus propios tokens, números y menús aislados. |
| **Configuración Dinámica** | ❌ | **FALTA:** Los secretos (tokens) están en `.env`. Un SaaS debe permitir la gestión de credenciales vía UI hacia la DB. |
| **Gestión de Multimedia** | ❌ | **FALTA:** La lógica de carga y envío de archivos no está integrada en el flujo de respuesta. |
| **Escalabilidad de Datos** | ❌ | **FALTA:** SQLite es excelente para un solo proceso, pero impide la ejecución de múltiples instancias de `bot-engine` en paralelo para manejar volumen. |
| **Dashboard de Analíticas** | ❌ | **FALTA:** Visualización de métricas de mensajes, tasa de éxito de bots y uso de API. |

---

## 🛠️ 3. DIAGNÓSTICO TÉCNICO Y RECOMENDACIONES

### 🚨 El Problema del "Single-Tenant" (Un solo cliente)
Actualmente, el código lee una única configuración de entorno. Para que sea un SaaS, la arquitectura debe cambiar de **"Configuración por Entorno"** a **"Configuración por Contexto de Cliente"**.

**Requerimiento:** El `engine.py` no debe buscar `os.getenv("TOKEN")`, debe buscar `db_manager.get_token_for_client(client_id)`.

### 🛡️ Seguridad y Gestión de Secretos
El uso de `.env` para la operación diaria es un cuello de botella de gestión. 
*   **Acción:** Los tokens de Meta deben tratarse como datos sensibles en la base de datos, preferiblemente con una capa de cifrado a nivel de aplicación.

### 🚀 Optimización de Costes (Arquitectura Low-Cost)
Para mantener el coste casi en cero:
1.  **Servidor:** Mantener el uso de Python y Node.js en instancias pequeñas (micro-instancias).
2.  **Base de Datos:** Iniciar con PostgreSQL (vía servicios gratuitos o managed) para facilitar la escalabilidad sin cambiar el código de SQL.
3.  **Cómputo:** La arquitectura actual es ligera y no requiere clusters pesados, lo cual es un punto a favor para la rentabilidad.

---

## 🎯 4. CONCLUSIÓN DE VIABILIDAD

El proyecto **TIENE FUTURO** como SaaS porque la lógica de "Menú $ightarrow$ Estado $ightarrow$ Respuesta" ya está resuelta. El esfuerzo no debe ser en "crear nuevos bots", sino en **"aislar la ejecución"** para que múltiples clientes puedan usar la misma infraestructura de forma independiente.

**Prioridad Técnica Inmediata:**
1.  **Desacoplamiento de Configuración:** Mover todo de `.env` a la base de datos.
2.  **Implementación de Multi-tenancy:** Añadir `client_id` a todas las tablas de la base de datos.
