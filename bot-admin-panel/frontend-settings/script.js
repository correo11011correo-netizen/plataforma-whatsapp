document.addEventListener('DOMContentLoaded', () => {
    // API endpoint setup (Proxy via webhook recepcionista)
    const API_BASE_URL = '/dashboard';

    // --- DOM Elements: Settings (Textos Globales) ---
    const settingsWelcome = document.getElementById('welcome_message');
    const settingsMainMenu = document.getElementById('main_menu_text');
    const settingsFallback = document.getElementById('fallback_message');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const settingsFeedback = document.getElementById('settings-feedback');

    // --- Funciones Textos Globales ---
    async function loadSettings() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/settings`);
            if (!response.ok) throw new Error(`Error: ${response.status}`);
            const settings = await response.json();
            
            settingsWelcome.value = settings.welcome_message || '';
            settingsMainMenu.value = settings.main_menu_text || '';
            settingsFallback.value = settings.fallback_message || '';
        } catch (error) {
            showSettingsFeedback('Error al cargar textos.', 'error');
            console.error(error);
        }
    }

    async function saveSettings() {
        saveSettingsBtn.disabled = true;
        saveSettingsBtn.textContent = 'Guardando...';

        const data = {
            welcome_message: settingsWelcome.value,
            main_menu_text: settingsMainMenu.value,
            fallback_message: settingsFallback.value
        };

        try {
            const response = await fetch(`${API_BASE_URL}/api/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) throw new Error(`Error: ${response.status}`);
            showSettingsFeedback('Textos guardados exitosamente.', 'success');
        } catch (error) {
            showSettingsFeedback('Error al guardar textos.', 'error');
            console.error(error);
        } finally {
            saveSettingsBtn.disabled = false;
            saveSettingsBtn.textContent = 'Guardar Textos';
        }
    }

    function showSettingsFeedback(message, type) {
        settingsFeedback.textContent = message;
        settingsFeedback.className = `feedback-msg ${type}`;
        settingsFeedback.style.display = 'block';
        setTimeout(() => {
            settingsFeedback.style.display = 'none';
        }, 3000);
    }

    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', saveSettings);
    }

    // --- Constructor de Menús Dinámicos (Inline Builder) ---
    const menusContainer = document.getElementById('menus-container');
    const addMenuBtn = document.getElementById('add-menu-btn');
    
    // Lista global de menus para referencias cruzadas (submenus)
    let globalMenusList = [];

    async function loadMenus() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/menus`);
            if (!response.ok) throw new Error(`Error: ${response.status}`);
            const menus = await response.json();
            globalMenusList = menus;
            
            if (menus.length === 0) {
                menusContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: #666; font-size: 1.1em; border: 2px dashed #ccc; border-radius: 8px;">No hay menús ni categorías creadas.<br>Haz clic en <b>"+ Nuevo Menú / Categoría"</b> arriba para empezar.</div>';
                return;
            }

            menusContainer.innerHTML = '';
            menus.forEach(menu => {
                const menuCard = document.createElement('div');
                menuCard.className = 'menu-card builder-card';
                menuCard.style = 'border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 25px; background: #fff; box-shadow: 0 4px 8px rgba(0,0,0,0.05);';
                
                // Calcular la siguiente llave (1, 2, 3...)
                let nextKey = 1;
                if (menu.options && menu.options.length > 0) {
                    const keys = menu.options.map(o => parseInt(o.option_key)).filter(k => !isNaN(k));
                    if (keys.length > 0) nextKey = Math.max(...keys) + 1;
                }

                let optionsRows = '';
                if (menu.options && menu.options.length > 0) {
                    optionsRows = menu.options.map(opt => {
                        let actionHtml = '';
                        if (opt.action_type === 'submenu') {
                            actionHtml = `<span style="background: #e1f0ff; color: #0066cc; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; font-weight: bold;">📁 Abre Categoría:</span> <span style="font-weight: bold;">${opt.action_payload}</span>`;
                        } else {
                            actionHtml = `<span style="background: #e8f5e9; color: #2e7d32; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; font-weight: bold;">💬 Responde Texto:</span> "${opt.action_payload}"`;
                        }

                        return `
                        <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 8px; padding: 12px; background: #fcfcfc; border: 1px solid #eee; border-radius: 6px;">
                            <div style="width: 30px; font-weight: bold; color: #555; font-size: 1.1em; text-align: center;">${opt.option_key}.</div>
                            <div style="flex: 2; font-size: 1.05em; color: #111;">${opt.option_text}</div>
                            <div style="flex: 2;">${actionHtml}</div>
                            <button class="btn-danger btn-sm" onclick="deleteOption(${opt.id})" title="Eliminar Opción" style="padding: 6px 12px; cursor: pointer;">X</button>
                        </div>
                        `;
                    }).join('');
                } else {
                    optionsRows = `<div style="color: #888; font-style: italic; margin-bottom: 15px; text-align: center; padding: 10px;">Aún no hay opciones en esta categoría. Agrega la primera abajo.</div>`;
                }

                // Generar opciones para el selector de submenus (para enlazar fácilmente sin escribir)
                let submenuOptions = globalMenusList.map(m => `<option value="${m.name}">${m.name}</option>`).join('');

                menuCard.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-bottom: 15px;">
                        <div>
                            <h4 style="margin: 0; color: #222; font-size: 1.3em;">🏷️ Categoría: <span style="color:#007bff">${menu.name}</span></h4>
                            <p style="margin: 5px 0 0 0; color: #666; font-size: 0.9em;">${menu.description || 'Sin descripción'}</p>
                        </div>
                        <button class="btn-danger btn-sm" onclick="deleteMenu(${menu.id}, '${menu.name}')" style="background: #dc3545;">Eliminar Toda la Categoría</button>
                    </div>
                    
                    <div class="options-list">
                        ${optionsRows}
                    </div>

                    <!-- Constructor en línea (Agrega nueva opcion) -->
                    <div style="display: flex; gap: 10px; align-items: center; background: #f0f7ff; padding: 12px; border-radius: 6px; margin-top: 15px; border: 1px dashed #99c2ff;">
                        <div style="font-weight: bold; color: #0066cc; width: 30px; font-size: 1.1em; text-align: center;">${nextKey}.</div>
                        <input type="hidden" id="key-${menu.id}" value="${nextKey}">
                        
                        <input type="text" id="text-${menu.id}" placeholder="Texto del botón (Ej: Ver Comidas)" style="flex: 2; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 1em;">
                        
                        <select id="action-${menu.id}" onchange="togglePayloadInput(${menu.id})" style="padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 1em; background: #fff;">
                            <option value="text">Muestra un Mensaje</option>
                            <option value="submenu">Abre otra Categoría</option>
                        </select>
                        
                        <!-- Input híbrido (texto libre o selector de submenu) -->
                        <div id="payload-container-${menu.id}" style="flex: 2;">
                            <input type="text" id="payload-text-${menu.id}" placeholder="Mensaje que dirá el bot..." style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 1em; box-sizing: border-box;">
                            <select id="payload-select-${menu.id}" style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 1em; display: none; background: #fff; box-sizing: border-box;">
                                <option value="">-- Selecciona a qué Categoría irá --</option>
                                ${submenuOptions}
                            </select>
                        </div>

                        <button class="btn-primary" onclick="addOptionInline(${menu.id})" style="padding: 10px 20px; background: #28a745; font-weight: bold; cursor: pointer;">+ Agregar</button>
                    </div>
                `;
                menusContainer.appendChild(menuCard);
            });

        } catch (error) {
            menusContainer.innerHTML = '<p style="color:red; font-weight:bold;">Error al cargar el constructor. Revisa la consola.</p>';
            console.error(error);
        }
    }

    window.togglePayloadInput = function(menuId) {
        const action = document.getElementById(`action-${menuId}`).value;
        const textInput = document.getElementById(`payload-text-${menuId}`);
        const selectInput = document.getElementById(`payload-select-${menuId}`);
        
        if (action === 'submenu') {
            textInput.style.display = 'none';
            selectInput.style.display = 'block';
        } else {
            textInput.style.display = 'block';
            selectInput.style.display = 'none';
        }
    };

    window.addOptionInline = async function(menuId) {
        const key = document.getElementById(`key-${menuId}`).value;
        const text = document.getElementById(`text-${menuId}`).value.trim();
        const type = document.getElementById(`action-${menuId}`).value;
        
        let payload = '';
        if (type === 'submenu') {
            payload = document.getElementById(`payload-select-${menuId}`).value;
            if (!payload) { alert("Debes seleccionar una categoría de destino en el recuadro desplegable."); return; }
        } else {
            payload = document.getElementById(`payload-text-${menuId}`).value.trim();
        }

        if (!text) { alert("Debes escribir el texto de la opción (Ej: Ver Comidas)."); return; }

        try {
            await fetch(`${API_BASE_URL}/api/menus/${menuId}/options`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    option_key: key,
                    option_text: text,
                    action_type: type,
                    action_payload: payload
                })
            });
            loadMenus(); // Recarga y aparece instantáneamente el número siguiente
        } catch (e) { alert("Error al guardar la opción en la base de datos."); }
    };

    addMenuBtn.addEventListener('click', async () => {
        const name = prompt("Escribe una palabra clave para tu nueva categoría (Ej: comidas_menu, precios, soporte):\\n\\nImportante: Usa minúsculas y no dejes espacios.");
        if (!name) return;
        
        const desc = prompt("Breve descripción interna para ti (Opcional):");
        
        try {
            await fetch(`${API_BASE_URL}/api/menus`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name.replace(/\\s+/g, '_').toLowerCase(), description: desc || '' })
            });
            loadMenus();
        } catch (e) { alert("Error creando la nueva categoría."); }
    });

    window.deleteMenu = async function(menuId, menuName) {
        if (!confirm(`⚠️ ¿PELIGRO: Eliminar la categoría entera "${menuName}" y TODAS las opciones que tiene adentro?`)) return;
        try {
            await fetch(`${API_BASE_URL}/api/menus/${menuId}`, { method: 'DELETE' });
            loadMenus();
        } catch (e) { alert("Error al borrar categoría."); }
    }

    window.deleteOption = async function(optionId) {
        if (!confirm("¿Eliminar esta opción específica de la lista?")) return;
        try {
            await fetch(`${API_BASE_URL}/api/options/${optionId}`, { method: 'DELETE' });
            loadMenus();
        } catch (e) { alert("Error al borrar opción."); }
    }

    // --- Initial Load ---
    loadSettings();
    loadMenus();
});