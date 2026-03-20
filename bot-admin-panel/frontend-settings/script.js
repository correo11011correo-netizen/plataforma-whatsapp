document.addEventListener('DOMContentLoaded', () => {
    // API endpoint setup
    const API_BASE_URL = '/dashboard';

    // --- Tab Switching ---
    window.switchTab = function(tabName) {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.getElementById(`tab-${tabName}`).classList.add('active');
        
        if(tabName === 'flows') {
            document.getElementById('view-flows').style.display = 'block';
            document.getElementById('view-inventory').style.display = 'none';
        } else {
            document.getElementById('view-flows').style.display = 'none';
            document.getElementById('view-inventory').style.display = 'block';
            loadInventory();
        }
    };

    // --- DOM Elements: Settings ---
    const settingsWelcome = document.getElementById('welcome_message');
    const settingsMainMenu = document.getElementById('main_menu_text');
    const settingsFallback = document.getElementById('fallback_message');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const settingsFeedback = document.getElementById('settings-feedback');

    async function loadSettings() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/settings`);
            if (!response.ok) throw new Error(`Error: ${response.status}`);
            const settings = await response.json();
            
            settingsWelcome.value = settings.welcome_message || '';
            settingsMainMenu.value = settings.main_menu_text || '';
            settingsFallback.value = settings.fallback_message || '';
        } catch (error) {
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
            await fetch(`${API_BASE_URL}/api/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            showSettingsFeedback('Textos guardados exitosamente.', 'success');
        } catch (error) {
            showSettingsFeedback('Error al guardar textos.', 'error');
        } finally {
            saveSettingsBtn.disabled = false;
            saveSettingsBtn.textContent = 'Guardar Textos';
        }
    }

    function showSettingsFeedback(message, type) {
        settingsFeedback.textContent = message;
        settingsFeedback.className = `feedback-msg ${type}`;
        settingsFeedback.style.display = 'block';
        setTimeout(() => { settingsFeedback.style.display = 'none'; }, 3000);
    }

    if (saveSettingsBtn) saveSettingsBtn.addEventListener('click', saveSettings);

    // --- Constructor de Flujos (Split View) ---
    const menusSidebar = document.getElementById('menus-list-container');
    const menuDetail = document.getElementById('menu-detail-container');
    const addMenuBtn = document.getElementById('add-menu-btn');
    
    let globalMenusList = [];
    let currentSelectedMenuId = null;

    async function loadMenus() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/menus`);
            if (!response.ok) throw new Error(`Error: ${response.status}`);
            const menus = await response.json();
            globalMenusList = menus;
            
            if (menus.length === 0) {
                menusSidebar.innerHTML = '<div style="color: #94a3b8; text-align: center; padding: 20px; font-style: italic;">No hay flujos creados</div>';
                menuDetail.innerHTML = '<div style="text-align: center; color: #94a3b8; margin-top: 100px;"><h3>No hay flujos</h3><p>Crea uno nuevo arriba a la derecha.</p></div>';
                return;
            }

            menusSidebar.innerHTML = '';
            menus.forEach(menu => {
                const item = document.createElement('div');
                const isSelected = menu.id === currentSelectedMenuId;
                item.style = `padding: 12px 15px; margin-bottom: 8px; border-radius: 8px; cursor: pointer; transition: all 0.2s; font-weight: 600; display: flex; align-items: center; justify-content: space-between; border: 1px solid ${isSelected ? '#3b82f6' : 'transparent'}; background: ${isSelected ? '#eff6ff' : '#fff'}; color: ${isSelected ? '#1d4ed8' : '#334155'}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);`;
                item.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <svg width="16" height="16" fill="${isSelected ? '#3b82f6' : '#94a3b8'}" viewBox="0 0 16 16"><path d="M2 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2zm10-1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1z"/></svg>
                        ${menu.name}
                    </div>
                    <span style="font-size: 0.8em; background: ${isSelected ? '#bfdbfe' : '#e2e8f0'}; padding: 2px 6px; border-radius: 10px; color: ${isSelected ? '#1e3a8a' : '#64748b'};">${menu.options ? menu.options.length : 0} opc</span>
                `;
                item.onclick = () => {
                    currentSelectedMenuId = menu.id;
                    loadMenus(); // Re-render sidebar colors
                    showMenuDetail(menu);
                    if (window.innerWidth <= 768) {
                        document.getElementById('menus-sidebar').classList.add('hide-on-mobile');
                        document.getElementById('menu-detail-container').classList.remove('hide-on-mobile');
                    }
                };
                
                // Add hover effect via JS
                item.addEventListener('mouseover', () => { if(!isSelected) item.style.background = '#f1f5f9'; });
                item.addEventListener('mouseout', () => { if(!isSelected) item.style.background = '#fff'; });
                
                menusSidebar.appendChild(item);
            });

            // If a menu was selected, re-show its detail. Otherwise show the first one.
            if (currentSelectedMenuId) {
                const menu = menus.find(m => m.id === currentSelectedMenuId);
                if(menu) showMenuDetail(menu);
                else { currentSelectedMenuId = null; menuDetail.innerHTML = ''; }
            } else if (menus.length > 0) {
                currentSelectedMenuId = menus[0].id;
                loadMenus();
            }

            // Mobile-first check: if we are on mobile, hide details initially unless forced.
            if (window.innerWidth <= 768 && !document.getElementById('menus-sidebar').classList.contains('hide-on-mobile')) {
                document.getElementById('menu-detail-container').classList.add('hide-on-mobile');
            }

        } catch (error) {
            menusSidebar.innerHTML = '<p style="color:red; font-weight:bold;">Error al cargar flujos.</p>';
        }
    }

    window.showMobileSidebar = function() {
        document.getElementById('menus-sidebar').classList.remove('hide-on-mobile');
        document.getElementById('menu-detail-container').classList.add('hide-on-mobile');
    };

    function showMenuDetail(menu) {
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
                    actionHtml = `<span style="background: #e1f0ff; color: #0066cc; padding: 4px 8px; border-radius: 6px; font-size: 0.85em; font-weight: bold;">📁 Abre Flujo:</span> <span style="font-weight: 600; color: #333; margin-left: 5px;">${opt.action_payload}</span>`;
                } else if (opt.action_type === 'image') {
                    actionHtml = `<span style="background: #fff3cd; color: #ff8f00; padding: 4px 8px; border-radius: 6px; font-size: 0.85em; font-weight: bold;">📷 Envía Imagen</span> <a href="${opt.action_payload}" target="_blank" style="font-size: 0.85em; margin-left: 5px; color: #0066cc; text-decoration: none;">[Enlace]</a>`;
                } else if (opt.action_type === 'document') {
                    actionHtml = `<span style="background: #f8bbd0; color: #d81b60; padding: 4px 8px; border-radius: 6px; font-size: 0.85em; font-weight: bold;">📄 Envía Doc</span> <a href="${opt.action_payload}" target="_blank" style="font-size: 0.85em; margin-left: 5px; color: #0066cc; text-decoration: none;">[Enlace]</a>`;
                } else if (opt.action_type === 'inventory') {
                    actionHtml = `<span style="background: #d1fae5; color: #047857; padding: 4px 8px; border-radius: 6px; font-size: 0.85em; font-weight: bold;">🔍 Muestra Inventario</span>`;
                } else {
                    actionHtml = `<span style="background: #e8f5e9; color: #2e7d32; padding: 4px 8px; border-radius: 6px; font-size: 0.85em; font-weight: bold;">💬 Texto:</span> <span style="color: #444; margin-left: 5px;">"${opt.action_payload}"</span>`;
                }

                return `
                <div class="dynamic-option-row" style="display: flex; gap: 15px; align-items: center; margin-bottom: 8px; padding: 12px 15px; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; transition: box-shadow 0.2s;">
                    <div style="background: #f1f5f9; color: #475569; font-weight: 700; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border-radius: 50%; font-size: 0.95em; flex-shrink: 0;">${opt.option_key}</div>
                    <div style="flex: 1.5; font-weight: 600; color: #1e293b; font-size: 1.05em;">${opt.option_text}</div>
                    <div style="flex: 2; font-size: 0.95em;">${actionHtml}</div>
                    <button onclick="deleteOption(${opt.id})" title="Eliminar Opción" style="background: transparent; color: #ef4444; border: none; cursor: pointer; padding: 6px; border-radius: 6px; transition: background 0.2s; flex-shrink: 0;" onmouseover="this.style.background='#fee2e2'" onmouseout="this.style.background='transparent'">
                        <svg width="18" height="18" fill="currentColor" viewBox="0 0 16 16"><path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/></svg>
                    </button>
                </div>
                `;
            }).join('');
        } else {
            optionsRows = `<div style="color: #64748b; font-style: italic; margin-bottom: 15px; text-align: center; padding: 25px; background: #f8fafc; border-radius: 8px; border: 1px dashed #cbd5e1;">Aún no hay opciones en este flujo. Configura la primera abajo.</div>`;
        }

        let submenuOptions = globalMenusList.map(m => `<option value="${m.name}">${m.name}</option>`).join('');

        menuDetail.innerHTML = `
            <button class="mobile-back-btn" onclick="showMobileSidebar()" style="background: #e2e8f0; color: #334155; border: none; padding: 10px 15px; border-radius: 6px; margin-bottom: 20px; font-weight: 600; cursor: pointer; width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px;">
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0z"/></svg>
                Volver a la Lista de Flujos
            </button>
            <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 20px; flex-wrap: wrap; gap: 15px;">
                <div style="flex: 1; min-width: 200px;">
                    <h3 style="margin: 0; color: #0f172a; font-size: 1.6em; display: flex; align-items: center; gap: 8px;">
                        Flujo: <span style="color: #3b82f6;">${menu.name}</span>
                    </h3>
                    <p style="margin: 6px 0 0 0; color: #64748b; font-size: 0.95em;">${menu.description || 'Sin descripción'}</p>
                </div>
                <button onclick="deleteMenu(${menu.id}, '${menu.name}')" style="background: #fff; color: #ef4444; border: 1px solid #fca5a5; border-radius: 6px; padding: 6px 14px; font-size: 0.85em; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.2s;" onmouseover="this.style.background='#fef2f2'; this.style.borderColor='#ef4444';" onmouseout="this.style.background='#fff'; this.style.borderColor='#fca5a5';">
                    <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg>
                    Eliminar Flujo
                </button>
            </div>
            
            <div class="options-list" style="margin-bottom: 25px;">
                <h4 style="margin: 0 0 15px 0; color: #334155;">Opciones / Botones del Menú:</h4>
                ${optionsRows}
            </div>

            <!-- Constructor en línea (Agregar nueva opcion) -->
            <div style="background: #f8fafc; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                <div style="font-weight: 600; color: #475569; font-size: 1.05em; margin-bottom: 15px; display: flex; align-items: center; gap: 6px;">
                    <svg width="18" height="18" fill="#0ea5e9" viewBox="0 0 16 16"><path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/><path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/></svg>
                    Añadir una nueva opción
                </div>
                <div class="dynamic-option-row" style="display: flex; gap: 15px; align-items: flex-start; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 150px;">
                        <label style="display:block; font-size:0.85em; color:#64748b; margin-bottom:4px; font-weight:600;">Llave</label>
                        <div style="display:flex; align-items:center; gap:10px;">
                            <div style="font-weight: 700; color: #0284c7; width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; background: #e0f2fe; border-radius: 8px; font-size: 1.1em; flex-shrink: 0;">${nextKey}</div>
                            <input type="hidden" id="key-${menu.id}" value="${nextKey}">
                            <input type="text" id="text-${menu.id}" placeholder="Texto (Ej: Soporte)" style="width:100%; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.95em; outline: none; box-sizing: border-box;" onfocus="this.style.borderColor='#3b82f6'" onblur="this.style.borderColor='#cbd5e1'">
                        </div>
                    </div>
                    
                    <div style="flex: 1.5; min-width: 200px;">
                        <label style="display:block; font-size:0.85em; color:#64748b; margin-bottom:4px; font-weight:600;">Acción a realizar</label>
                        <select id="action-${menu.id}" onchange="togglePayloadInput(${menu.id})" style="width:100%; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.95em; background: #fff; cursor: pointer; outline: none;" onfocus="this.style.borderColor='#3b82f6'" onblur="this.style.borderColor='#cbd5e1'">
                            <option value="text">Muestra un Mensaje (Texto)</option>
                            <option value="submenu">Abre otro Flujo (Submenú)</option>
                            <option value="inventory">Mostrar Inventario / Catálogo</option>
                            <option value="image">Envía una Imagen (URL)</option>
                            <option value="document">Envía un Doc/PDF (URL)</option>
                        </select>
                    </div>
                    
                    <div id="payload-container-${menu.id}" style="flex: 2; min-width: 220px;">
                        <label id="payload-label-${menu.id}" style="display:block; font-size:0.85em; color:#64748b; margin-bottom:4px; font-weight:600;">Detalle de la acción</label>
                        <input type="text" id="payload-text-${menu.id}" placeholder="Escribe el mensaje aquí..." style="width: 100%; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.95em; outline: none; box-sizing: border-box;" onfocus="this.style.borderColor='#3b82f6'" onblur="this.style.borderColor='#cbd5e1'">
                        <select id="payload-select-${menu.id}" style="width: 100%; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.95em; display: none; background: #fff; outline: none; box-sizing: border-box;" onfocus="this.style.borderColor='#3b82f6'" onblur="this.style.borderColor='#cbd5e1'">
                            <option value="">-- Selecciona a qué Flujo irá --</option>
                            ${submenuOptions}
                        </select>
                    </div>
                </div>
                <div style="margin-top: 15px; text-align: right;">
                    <button onclick="addOptionInline(${menu.id})" style="background: #10b981; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: 600; font-size: 0.95em; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#059669'" onmouseout="this.style.background='#10b981'">
                        <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16" style="margin-right: 5px; vertical-align: text-top;"><path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/><path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/></svg>
                        Guardar Opción
                    </button>
                </div>
            </div>
        `;
    }

    window.togglePayloadInput = function(menuId) {
        const action = document.getElementById(`action-${menuId}`).value;
        const textInput = document.getElementById(`payload-text-${menuId}`);
        const selectInput = document.getElementById(`payload-select-${menuId}`);
        const label = document.getElementById(`payload-label-${menuId}`);
        const container = document.getElementById(`payload-container-${menuId}`);
        
        container.style.visibility = 'visible';
        
        if (action === 'submenu') {
            textInput.style.display = 'none';
            selectInput.style.display = 'block';
            label.innerText = 'Selecciona el Flujo Destino';
        } else if (action === 'inventory') {
            container.style.visibility = 'hidden'; // Inventario no necesita payload
        } else {
            textInput.style.display = 'block';
            selectInput.style.display = 'none';
            if (action === 'image' || action === 'document') {
                textInput.placeholder = "Pega aquí el enlace (URL) público del archivo...";
                label.innerText = 'URL del Archivo';
            } else {
                textInput.placeholder = "Mensaje que dirá el bot...";
                label.innerText = 'Texto a enviar';
            }
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
        } else if (type === 'inventory') {
            payload = 'show_inventory';
        } else {
            payload = document.getElementById(`payload-text-${menuId}`).value.trim();
            if(!payload) { alert("Debes rellenar el detalle de la acción."); return; }
        }

        if (!text) { alert("Debes escribir el texto de la opción."); return; }

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
            loadMenus(); 
        } catch (e) { alert("Error al guardar la opción en la base de datos."); }
    };

    addMenuBtn.addEventListener('click', async () => {
        const name = prompt("Escribe el nombre interno del Flujo (Ej: comidas_menu, principal, soporte):\\n\\nImportante: Usa minúsculas y no dejes espacios.");
        if (!name) return;
        
        const desc = prompt("Breve descripción interna para ti (Opcional):");
        
        try {
            await fetch(`${API_BASE_URL}/api/menus`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name.replace(/\\s+/g, '_').toLowerCase(), description: desc || '' })
            });
            loadMenus();
        } catch (e) { alert("Error creando el flujo."); }
    });

    window.deleteMenu = async function(menuId, menuName) {
        if (!confirm(`⚠️ ¿PELIGRO: Eliminar el flujo "${menuName}" y TODAS las opciones que tiene adentro?`)) return;
        try {
            await fetch(`${API_BASE_URL}/api/menus/${menuId}`, { method: 'DELETE' });
            currentSelectedMenuId = null; // Reset selection
            loadMenus();
        } catch (e) { alert("Error al borrar flujo."); }
    }

    window.deleteOption = async function(optionId) {
        if (!confirm("¿Eliminar esta opción específica de la lista?")) return;
        try {
            await fetch(`${API_BASE_URL}/api/options/${optionId}`, { method: 'DELETE' });
            loadMenus();
        } catch (e) { alert("Error al borrar opción."); }
    }


    // --- GESTIÓN DE INVENTARIO Y STOCK ---
    let globalInventory = [];

    async function loadInventory() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/inventory`);
            if (!response.ok) throw new Error("Network response was not ok");
            globalInventory = await response.json();
            renderInventory(globalInventory);
        } catch (error) {
            document.getElementById('inventory-list-container').innerHTML = `<p style="color:red;">Error cargando inventario. Revisa que el servidor soporte /api/inventory.</p>`;
        }
    }

    window.filterInventory = function() {
        const q = document.getElementById('inventory-search').value.toLowerCase();
        const filtered = globalInventory.filter(item => 
            (item.marca && item.marca.toLowerCase().includes(q)) ||
            (item.modelo && item.modelo.toLowerCase().includes(q)) ||
            (item.reparacion && item.reparacion.toLowerCase().includes(q))
        );
        renderInventory(filtered);
    }

    function renderInventory(items) {
        const container = document.getElementById('inventory-list-container');
        if (items.length === 0) {
            container.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #94a3b8; background: #f8fafc; border-radius: 8px; border: 1px dashed #cbd5e1;">No se encontraron productos o servicios.</div>`;
            return;
        }

        container.innerHTML = items.map(item => `
            <div style="background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); transition: transform 0.2s, box-shadow 0.2s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 10px 15px -3px rgba(0,0,0,0.1)';" onmouseout="this.style.transform='none'; this.style.boxShadow='0 4px 6px -1px rgba(0,0,0,0.05)';">
                <div style="padding: 15px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <span style="background: #e0e7ff; color: #4338ca; font-size: 0.75em; padding: 2px 8px; border-radius: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">${item.marca}</span>
                        <h4 style="margin: 8px 0 0 0; color: #1e293b; font-size: 1.1em;">${item.reparacion}</h4>
                        ${item.modelo ? `<p style="margin: 4px 0 0 0; color: #64748b; font-size: 0.9em;">Modelo: ${item.modelo}</p>` : ''}
                    </div>
                </div>
                <div style="padding: 15px; background: #f8fafc; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="color: #10b981; font-weight: 800; font-size: 1.2em;">$${parseFloat(item.precio).toLocaleString()}</div>
                        <div style="color: #64748b; font-size: 0.85em; margin-top: 2px;">Stock: <span style="font-weight: 600; color: ${item.stock > 0 ? '#334155' : '#ef4444'}">${item.stock}</span></div>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="editInventory(${item.id})" style="background: #e2e8f0; color: #475569; border: none; padding: 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#cbd5e1'" onmouseout="this.style.background='#e2e8f0'" title="Editar">✏️</button>
                        <button onclick="deleteInventory(${item.id})" style="background: #fee2e2; color: #ef4444; border: none; padding: 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#fca5a5'" onmouseout="this.style.background='#fee2e2'" title="Eliminar">🗑️</button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Modal Logic
    document.getElementById('add-inventory-btn').addEventListener('click', () => {
        document.getElementById('inventory-form').reset();
        document.getElementById('inv-id').value = '';
        document.getElementById('inventory-modal-title').innerText = 'Añadir Nuevo Ítem';
        document.getElementById('inventory-modal').style.display = 'flex';
    });

    window.closeInventoryModal = function() {
        document.getElementById('inventory-modal').style.display = 'none';
    }

    window.editInventory = function(id) {
        const item = globalInventory.find(i => i.id === id);
        if(!item) return;
        document.getElementById('inv-id').value = item.id;
        document.getElementById('inv-marca').value = item.marca;
        document.getElementById('inv-modelo').value = item.modelo || '';
        document.getElementById('inv-reparacion').value = item.reparacion;
        document.getElementById('inv-precio').value = item.precio;
        document.getElementById('inv-stock').value = item.stock;
        document.getElementById('inventory-modal-title').innerText = 'Editar Ítem';
        document.getElementById('inventory-modal').style.display = 'flex';
    }

    window.deleteInventory = async function(id) {
        if(!confirm("¿Estás seguro de eliminar este ítem permanentemente?")) return;
        try {
            await fetch(`${API_BASE_URL}/api/inventory/${id}`, { method: 'DELETE' });
            loadInventory();
        } catch (e) { alert("Error al borrar inventario"); }
    }

    document.getElementById('inventory-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('inv-id').value;
        const data = {
            marca: document.getElementById('inv-marca').value,
            modelo: document.getElementById('inv-modelo').value,
            reparacion: document.getElementById('inv-reparacion').value,
            precio: parseFloat(document.getElementById('inv-precio').value),
            stock: parseInt(document.getElementById('inv-stock').value) || 0
        };

        try {
            if (id) {
                // Edit
                await fetch(`${API_BASE_URL}/api/inventory/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            } else {
                // Add
                await fetch(`${API_BASE_URL}/api/inventory`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            }
            closeInventoryModal();
            loadInventory();
        } catch(err) {
            alert("Error guardando el ítem");
        }
    });

    // --- Initial Load ---
    loadSettings();
    loadMenus();
});