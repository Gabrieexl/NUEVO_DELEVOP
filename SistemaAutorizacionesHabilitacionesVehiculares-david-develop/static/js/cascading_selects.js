/**
 * Helper para manejar selects en cascada (Empresa -> Autorización, Vehículos, Conductores)
 */
const CascadingSelects = {
    /**
     * Inicializa los listeners para los selects en cascada
     * @param {Object} config Configuración de los selectores (IDs)
     */
    init: function(config) {
        const defaults = {
            empresaSelectId: 'id_empresa',
            autorizacionSelectId: 'id_autorizacion',
            vehiculoSelectId: 'id_vehiculo',
            conductorSelectId: 'id_conductor',
            apiUrl: '/tramites/ajax/'
        };
        
        this.config = { ...defaults, ...config };
        
        const empresaSelect = document.getElementById(this.config.empresaSelectId);
        
        if (empresaSelect) {
            empresaSelect.addEventListener('change', (e) => this.handleEmpresaChange(e.target.value));
            // Si ya hay empresa seleccionada al cargar, poblar dependientes
            if (empresaSelect.value) {
                this.handleEmpresaChange(empresaSelect.value, { preserveSelection: true });
            }
        }
    },

    handleEmpresaChange: function(empresaId, options = {}) {
        const preserveSelection = options.preserveSelection === true;
        const selectedValues = preserveSelection ? this.getSelectedValues() : {};

        this.clearSelects();
        
        if (!empresaId) return;
        
        this.loadAutorizaciones(empresaId, selectedValues.autorizacion);
        this.loadVehiculos(empresaId, selectedValues.vehiculo);
        this.loadConductores(empresaId, selectedValues.conductor);
    },

    getSelectedValues: function() {
        const autorizacionSelect = document.getElementById(this.config.autorizacionSelectId);
        const vehiculoSelect = document.getElementById(this.config.vehiculoSelectId);
        const conductorSelect = document.getElementById(this.config.conductorSelectId);

        return {
            autorizacion: autorizacionSelect ? autorizacionSelect.value : '',
            vehiculo: vehiculoSelect ? vehiculoSelect.value : '',
            conductor: conductorSelect ? conductorSelect.value : ''
        };
    },

    clearSelects: function() {
        const selects = [
            this.config.autorizacionSelectId,
            this.config.vehiculoSelectId,
            this.config.conductorSelectId
        ];
        
        selects.forEach(id => {
            const select = document.getElementById(id);
            if (select) {
                select.innerHTML = '<option value="">---------</option>';
                // Disparar evento change por si hay otros listeners
                select.dispatchEvent(new Event('change'));
            }
        });
    },

    loadAutorizaciones: function(empresaId, selectedId) {
        const select = document.getElementById(this.config.autorizacionSelectId);
        if (!select) return;

        fetch(`${this.config.apiUrl}autorizacion-por-empresa/${empresaId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.autorizaciones) {
                    let selectedApplied = false;
                    data.autorizaciones.forEach(auth => {
                        const option = document.createElement('option');
                        option.value = auth.id;
                        option.textContent = auth.text;
                        if (selectedId && String(auth.id) === String(selectedId)) {
                            option.selected = true;
                            selectedApplied = true;
                        } else if (auth.estado === 'VIGENTE' && data.autorizaciones.length === 1 && !selectedId) {
                            option.selected = true;
                        }
                        select.appendChild(option);
                    });
                    // Si había selección previa pero no existe, dejar placeholder
                    if (selectedId && !selectedApplied) {
                        select.value = '';
                    }
                }
            })
            .catch(console.error);
    },

    loadVehiculos: function(empresaId, selectedId) {
        const select = document.getElementById(this.config.vehiculoSelectId);
        if (!select) return;

        fetch(`${this.config.apiUrl}vehiculos-por-empresa/${empresaId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.vehiculos) {
                    data.vehiculos.forEach(v => {
                        const option = document.createElement('option');
                        option.value = v.id;
                        option.textContent = v.text;
                        if (selectedId && String(v.id) === String(selectedId)) {
                            option.selected = true;
                        }
                        select.appendChild(option);
                    });
                }
            })
            .catch(console.error);
    },

    loadConductores: function(empresaId, selectedId) {
        const select = document.getElementById(this.config.conductorSelectId);
        if (!select) return;

        fetch(`${this.config.apiUrl}conductores-por-empresa/${empresaId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.conductores) {
                    data.conductores.forEach(c => {
                        const option = document.createElement('option');
                        option.value = c.id;
                        option.textContent = c.text;
                        if (selectedId && String(c.id) === String(selectedId)) {
                            option.selected = true;
                        }
                        select.appendChild(option);
                    });
                }
            })
            .catch(console.error);
    }
};
