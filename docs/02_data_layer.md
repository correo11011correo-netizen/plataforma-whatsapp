# 💾 02_Data_Layer: Análisis de Persistencia

Este módulo es el sistema nervioso del proyecto. Se encarga de la comunicación con la base de datos SQLite y garantiza que el estado de las conversaciones, los menús y la configuración se mantengan persistentes.

## 🧩 Estructura y Funciones Principales

### 1. Conexión y Modelo de Datos (`get_db_connection`)
*   **Funcionamiento:** Utiliza `sqlite3` para establecer conexiones. Usa `row_factory = sqlite3.Row` para permitir el acceso a las columnas por nombre, lo cual es excelente para la legibilidad.
*   **Ubicación de la DB:** La base de datos `bot_dashboard.db` se encuentra en una ruta relativa fuera del motor del bot (`../database/`).

### 2. Gestión de Conversaciones y Contactos
*   **`add_message`:** Implementa una lógica de "Inserción o Ignorar" para contactos, asegurando que la estructura `Contacto -> Conversación -> Mensaje` se mantenga íntegra.
*   **`get_conversation_status` / `set_human_intervention_status`:** Gestiona el flag `is_human_intervening`. Esto es crítico para la lógica de "Modo Humano" del motor.
*   **`delete_conversation`:** Realiza una limpieza en cascada manual (borra mensajes y luego la conversación) para mantener la integridad referencial.

### 3. Motor de Menús y Configuración
*   **`get_all_menus`:** Recupera la jerarquía de menús. Es una función compleja que realiza una consulta de dos pasos: primero obtiene los menús y luego hace un `JOIN` lógico (mediante un segundo bucle) para traer las opciones de cada uno.
*   **`get_bot_setting` / `update_bot_setting`:** Permite la configuración dinámica de variables (como mensajes de bienvenida o de error) sin tocar el código.
*   **`get_all_inventory`:** Gestión de un catálogo de productos/servicios para uso en el bot.

---

## ⚠️ Hallazgos de Auditoría (Data Layer)

### 🔴 Crítico: Modelo de Datos "Single-Tenant" (No apto para SaaS)
*   **Problema:** Todas las tablas (`contacts`, `conversasiones`, `menus`, `bot_settings`) carecen de una columna `client_id` o `account_id`.
*   **Impacto:** Actualmente, es imposible separar los datos de dos clientes distintos en la misma base de datos. Si un cliente cambia su menú, cambia para todos.
*   **Requerimiento SaaS:** Se debe migrar a un esquema donde cada registro pertenezca a un `owner_id`.

### 🟠 Moderado: Gestión de Conexiones
*   **Problema:** Cada función abre y cierra una conexión (`get_db_connection`) de forma individual.
*   **Impacto:** Para un volumen bajo es aceptable, pero en un entorno de alto tráfico (muchos mensajes por segundo), el *overhead* de abrir/cerrar archivos SQLite será un cuello de botella importante.
*   **Recomendación:** Implementar un **Connection Pool** o mantener una conexión persistente en el hilo principal del servidor.

### 🟡 Menor: Integridad Referencial Manual
*   **Problema:** La limpieza de datos (como en `delete_conversation`) se hace mediante código manual en lugar de depender de `ON DELETE CASCADE` de la base de datos.
*   **Impacto:** Si se borra un contacto por otro medio, podrían quedar mensajes "huérfanos" en la base de datos.

---

## 📊 Matriz de Capacidades (DB)

| Capacidad | Estado | Observación Técnica |
| :--- | :---: | :--- |
| **Persistencia de Mensajes** | ✅ | Funcional y relacional. |
| **Gestión de Estados** | ✅ | Basada en flags de intervención. |
| **Configuración Dinámica** | ✅ | Mediante tabla `bot_settings`. |
| **Aislamiento de Clientes** | ❌ | **FALTA:** No hay separación lógica de datos por usuario/empresa. |
| **Escalabilidad Horizontal** | ❌ | **FALTA:** SQLite bloquea la escritura en múltiples procesos. |

---
**Estado del Módulo:** 🏗️ *Funcional para uso local, pero requiere rediseño relacional para multitenencia.*
