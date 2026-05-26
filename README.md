# 📱 WhatsApp Platform (Official Meta API)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/correo11011correo-netizen/plataforma-whatsapp/pulls)
[![Python](https://img.shields.io/badge/Python-3.x-blue)](https://www.python.org/)
[![SaaS Roadmap](https://img.shields.io/badge/Roadmap-SaaS_Transformation-orange)](https://github.com/correo11011correo-netizen/plataforma-whatsapp/blob/main/docs/07_roadmap_final.md)

**Plataforma WhatsApp** es una solución de comunicación empresarial diseñada para aprovechar la **API oficial de Meta**. Actualmente, el proyecto se encuentra en una fase de transición crítica: de ser una herramienta de automatización de uso local a convertirse en una **plataforma SaaS (Software as a Service) multitenant, escalable y profesional.**

---

## 🎯 Visión y Objetivo
Nuestro objetivo es democratizar la gestión de comunicaciones empresariales mediante una plataforma donde cualquier empresa pueda desplegar, configurar y administrar sus propios bots de WhatsApp de forma autónoma, segura y sin necesidad de conocimientos técnicos.

---

## ✅ Hitos Alcanzados (Core Engine Ready)
Hemos construido los cimientos lógicos necesarios para el motor de automatización:

*   **🤖 Motor de Decisiones:** Sistema de procesamiento de eventos basado en estados para flujos de conversación.
*   **📂 Gestión de Menús Dinámicos:** Arquitectura para crear árboles de decisión mediante bases de datos, sin tocar el código.
*   **💬 Intervención Humana:** Lógica nativa para que un operador humano pueda tomar el control de una conversación en tiempo real.
*   **🖥️ Dashboard Administrativo:** Interfaz web para la gestión de chats, mensajes y configuración de parámetros.
*   **📦 Gestión de Inventario:** Sistema base para la integración de catálogos de productos/servicios.

---

## 🚀 Roadmap hacia el Modelo SaaS (Lo que estamos construyendo)
Para alcanzar el estándar de producto comercial, nuestra hoja de ruta se divide en tres fases críticas:

### 🔐 Fase 1: Identidad y Seguridad (Prioridad Alta)
*   **Multitenencia (Multi-tenant):** Migrar la base de datos para permitir múltiples clientes aislados en una misma infraestructura.
*   **Gestión de Secretos:** Mover toda la configuración sensible (Tokens de Meta) de archivos `.env` a un gestor cifrado en la base de datos.
*   **Autenticación Profesional:** Implementación de sistemas de acceso robustos (JWT) para administradores y clientes.

### 🏗️ Fase 2: Escalabilidad y Robustez
*   **Arquitectura de Microservicios:** Desacoplar el Panel de Administración del Motor de Ejecución mediante una API REST dedicada.
*   **Migración de Persistencia:** Evolucionar de SQLite a PostgreSQL para soportar alta concurrencia y despliegues distribuidos.
*   **Estado Centralizado:** Eliminar los archivos de estado locales (`state.json`) para permitir la escalabilidad horizontal.

### 🤖 Fase 3: Inteligencia y Experiencia de Usuario
*   **Integración de Agentes de IA:** Implementar un módulo de "Fallback Inteligente" para delegar conversaciones complejas a modelos de lenguaje (LLMs).
*   **Dashboard de Analíticas:** Visualización de métricas de rendimiento, uso de API y engagement de usuarios.
*   **Gestión Multimedia Avanzada:** Soporte completo para envío y recepción de archivos complejos mediante la interfaz web.

---

## 🛠️ Stack Tecnológico
*   **Lenguaje Principal:** Python
*   **API:** Meta WhatsApp Cloud API
*   **Base de Datos:** SQL-based (Evolucionando a PostgreSQL)
*   **Frontend:** Web Administration Panel (Vanilla JS/HTML/CSS)

## 🤝 ¿Cómo contribuir?
Estamos buscando mentes brillantes que quieran ayudar a construir el estándar de automatización de WhatsApp.

1.  **Explora los Issues:** Busca etiquetas como `good first issue` o `help wanted`.
2.  **Lee la documentación técnica:** Consulta nuestra carpeta `/docs/` para entender la arquitectura.
3.  **Haz un Fork y envía un PR:** ¡Tus contribuciones son bienvenidas!

## 📜 Licencia
Este proyecto está licenciado bajo la Licencia MIT - mira el archivo `LICENSE` para más detalles.
