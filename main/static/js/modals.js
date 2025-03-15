document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos
    const btnAgregar = document.querySelector('.btn_agregar');
    const modalDispositivo = document.getElementById('modal-agregar-dispositivo');
    const modalIcono = document.getElementById('modal-seleccionar-icono');
    const btnSeleccionarIcono = document.getElementById('btn-seleccionar-icono');
    const btnConfirmarIcono = document.getElementById('btn-confirmar-icono');
    const btnsCancel = document.querySelectorAll('.btn-cancelar');
    const btnsCerrar = document.querySelectorAll('.cerrar-modal');
    const iconoItems = document.querySelectorAll('.icono-item');
    const previewIconoContainer = document.getElementById('preview-icono-container');
    
    let iconoSeleccionado = null;

    // Abrir modal de agregar dispositivo
    if (btnAgregar) {
        btnAgregar.addEventListener('click', function() {
            modalDispositivo.style.display = 'block';
        });
    }

    // Abrir modal de seleccionar ícono
    btnSeleccionarIcono.addEventListener('click', function() {
        modalIcono.style.display = 'block';
    });

    // Cerrar modales con botón X
    btnsCerrar.forEach(btn => {
        btn.addEventListener('click', function() {
            modalDispositivo.style.display = 'none';
            modalIcono.style.display = 'none';
        });
    });

    // Cerrar modales con botón cancelar
    btnsCancel.forEach(btn => {
        btn.addEventListener('click', function() {
            modalDispositivo.style.display = 'none';
            modalIcono.style.display = 'none';
        });
    });

    // Cerrar modales al hacer clic fuera de ellos
    window.addEventListener('click', function(event) {
        if (event.target === modalDispositivo) {
            modalDispositivo.style.display = 'none';
        }
        if (event.target === modalIcono) {
            modalIcono.style.display = 'none';
        }
    });

    // Seleccionar ícono
    iconoItems.forEach(item => {
        item.addEventListener('click', function() {
            // Quitar selección previa
            iconoItems.forEach(i => i.classList.remove('seleccionado'));
            // Agregar selección actual
            this.classList.add('seleccionado');
            
            // Obtener el nombre del ícono desde el atributo data-icono del div
            iconoSeleccionado = {
                nombre: this.getAttribute('data-icono'),
                src: this.querySelector('img').src
            };
        });
    });

    // Confirmar selección de ícono
    btnConfirmarIcono.addEventListener('click', function() {
        if (iconoSeleccionado) {
            // Actualizar la vista previa del ícono en el contenedor
            actualizarPreviewIcono(iconoSeleccionado);
            // Cerrar modal de íconos
            modalIcono.style.display = 'none';
        } else {
            alert('Por favor, selecciona un ícono');
        }
    });

    // Función para actualizar la vista previa del ícono
    function actualizarPreviewIcono(icono) {
        // Limpiar el contenedor
        previewIconoContainer.innerHTML = '';
        
        // Crear la imagen
        const img = document.createElement('img');
        img.src = icono.src;
        img.alt = icono.nombre;
        
        // Crear el botón de añadir
        const addButton = document.createElement('div');
        addButton.className = 'icono-preview-add';
        addButton.innerHTML = '+';
        
        // Agregar elementos al contenedor
        previewIconoContainer.appendChild(img);
        previewIconoContainer.appendChild(addButton);
    }

    // Función para limpiar la vista previa
    function limpiarPreviewIcono() {
        previewIconoContainer.innerHTML = '<div class="icono-preview-add">+</div>';
        iconoSeleccionado = null;
    }

    // Envío de formulario
    document.getElementById('form-dispositivo').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Obtener valores del formulario
        const nombre = document.getElementById('nombre-dispositivo').value;
        const serie = document.getElementById('numero-serie').value;
        const voltaje = document.getElementById('voltaje').value;
        
        if (!iconoSeleccionado) {
            alert('Por favor, selecciona un ícono para el dispositivo');
            return;
        }
        
        // Aquí procesarías los datos para crear el nuevo dispositivo
        console.log('Dispositivo a agregar:', {
            nombre,
            serie,
            voltaje,
            icono: iconoSeleccionado.nombre
        });
        
        // Cerrar modal y reiniciar formulario
        modalDispositivo.style.display = 'none';
        this.reset();
        
        // Limpiar vista previa del ícono
        limpiarPreviewIcono();
    });
});