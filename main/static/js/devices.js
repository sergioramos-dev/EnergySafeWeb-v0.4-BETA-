// main/static/js/devices.js - Versión simplificada
document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos
    const btnAgregar = document.querySelectorAll('.btn_agregar');
    const modalDispositivo = document.getElementById('modal-agregar-dispositivo');
    const modalIcono = document.getElementById('modal-seleccionar-icono');
    const btnSeleccionarIcono = document.getElementById('btn-seleccionar-icono');
    const btnConfirmarIcono = document.getElementById('btn-confirmar-icono');
    const btnsCancel = document.querySelectorAll('.btn-cancelar');
    const btnsCerrar = document.querySelectorAll('.cerrar-modal');
    const iconoItems = document.querySelectorAll('.icono-item');
    const previewIconoContainer = document.getElementById('preview-icono-container');
    const formDispositivo = document.getElementById('form-dispositivo');
    const numeroSerieInput = document.getElementById('numero-serie');
    
    let iconoSeleccionado = null;
    let dispositivoVerificado = false;

    // Abrir modal de agregar dispositivo
    btnAgregar.forEach(btn => {
        btn.addEventListener('click', function() {
            modalDispositivo.style.display = 'block';
        });
    });

    // Abrir modal de seleccionar ícono
    if (btnSeleccionarIcono) {
        btnSeleccionarIcono.addEventListener('click', function() {
            modalIcono.style.display = 'block';
        });
    }

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
    if (btnConfirmarIcono) {
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
    }

    // Función para actualizar la vista previa del ícono
    function actualizarPreviewIcono(icono) {
        if (!previewIconoContainer) return;
        
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
        
        // Agregar un campo oculto con el nombre del ícono
        const iconoInput = document.createElement('input');
        iconoInput.type = 'hidden';
        iconoInput.name = 'icono';
        iconoInput.value = icono.nombre;
        
        if (formDispositivo) {
            // Eliminar campo oculto previo si existe
            const prevInput = formDispositivo.querySelector('input[name="icono"]');
            if (prevInput) {
                prevInput.remove();
            }
            formDispositivo.appendChild(iconoInput);
        }
    }

    // Función para limpiar la vista previa
    function limpiarPreviewIcono() {
        if (!previewIconoContainer) return;
        
        previewIconoContainer.innerHTML = '<div class="icono-preview-add">+</div>';
        iconoSeleccionado = null;
    }
    
    // Verificar número de serie al perder el foco
    if (numeroSerieInput) {
        numeroSerieInput.addEventListener('blur', function() {
            const numeroSerie = this.value.trim();
            
            if (numeroSerie.length < 5) {
                mostrarFeedback('El número de serie debe tener al menos 5 caracteres', 'error');
                return;
            }
            
            // Verificar si el número de serie existe
            fetch(`/devices/verify/${numeroSerie}/`)
                .then(response => response.json())
                .then(data => {
                    if (data.exists) {
                        if (data.available) {
                            // El dispositivo existe y está disponible
                            dispositivoVerificado = true;
                            
                            // Auto-completar campos si están disponibles
                            if (data.device_name) {
                                const nombreInput = document.getElementById('nombre-dispositivo');
                                if (nombreInput && !nombreInput.value) {
                                    nombreInput.value = data.device_name;
                                }
                            }
                            
                            if (data.voltage) {
                                const voltajeSelect = document.getElementById('voltaje');
                                if (voltajeSelect) {
                                    // Buscar la opción que coincida con el voltaje
                                    const opciones = voltajeSelect.options;
                                    for (let i = 0; i < opciones.length; i++) {
                                        if (opciones[i].value == data.voltage) {
                                            voltajeSelect.selectedIndex = i;
                                            break;
                                        }
                                    }
                                }
                            }
                            
                            mostrarFeedback('Número de serie verificado correctamente', 'success');
                        } else {
                            // El usuario ya tiene este dispositivo
                            dispositivoVerificado = false;
                            mostrarFeedback(data.message, 'error');
                        }
                    } else {
                        // El dispositivo no existe
                        dispositivoVerificado = false;
                        mostrarFeedback(data.message, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error al verificar número de serie:', error);
                    mostrarFeedback('Error al verificar el número de serie', 'error');
                    dispositivoVerificado = false;
                });
        });
    }
    
    // Función para mostrar feedback al usuario
    function mostrarFeedback(mensaje, tipo) {
        // Buscar o crear elemento de feedback
        let feedbackElement = document.getElementById('serie-feedback');
        if (!feedbackElement) {
            feedbackElement = document.createElement('div');
            feedbackElement.id = 'serie-feedback';
            numeroSerieInput.parentNode.appendChild(feedbackElement);
        }
        
        // Configurar estilo según el tipo
        feedbackElement.className = `feedback ${tipo}`;
        feedbackElement.textContent = mensaje;
        
        // Auto-ocultar después de unos segundos
        setTimeout(() => {
            feedbackElement.style.opacity = '0';
            setTimeout(() => {
                feedbackElement.style.display = 'none';
            }, 500);
        }, 5000);
        
        // Mostrar
        feedbackElement.style.display = 'block';
        feedbackElement.style.opacity = '1';
    }

    // Envío de formulario
    if (formDispositivo) {
        formDispositivo.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validar campos requeridos
            const nombre = document.getElementById('nombre-dispositivo').value;
            const serie = document.getElementById('numero-serie').value;
            const voltaje = document.getElementById('voltaje').value;
            
            if (!nombre || !serie || !voltaje) {
                alert('Por favor, completa todos los campos requeridos');
                return;
            }
            
            if (!dispositivoVerificado) {
                alert('El número de serie debe ser verificado primero');
                return;
            }
            
            if (!iconoSeleccionado) {
                alert('Por favor, selecciona un ícono para el dispositivo');
                return;
            }
            
            // Crear FormData con los datos del formulario
            const formData = new FormData(this);
            
            // Obtener token CSRF
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // Enviar datos al servidor
            fetch('/devices/add/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Éxito
                    alert(data.message);
                    
                    // Cerrar modal y reiniciar formulario
                    modalDispositivo.style.display = 'none';
                    formDispositivo.reset();
                    limpiarPreviewIcono();
                    
                    // Recargar la página para mostrar el nuevo dispositivo
                    window.location.reload();
                } else {
                    // Error
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error al agregar dispositivo:', error);
                alert('Ha ocurrido un error al agregar el dispositivo');
            });
        });
    }
});