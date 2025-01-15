// Esperar a que el DOM se cargue completamente
document.addEventListener('DOMContentLoaded', function () {
    const tabButtons = document.querySelectorAll('.tab-button[data-tab]');
    const tabContents = document.querySelectorAll('.tab-content');

    // Gestión de pestañas
    tabButtons.forEach(button => {
        button.addEventListener('click', function () {
            const tabId = this.dataset.tab;

            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });

    tabButtons[0].click();

    // Subir foto de perfil
    const uploadPhotoInput = document.getElementById('upload-photo');
    const profilePhoto = document.getElementById('profile-photo');

    uploadPhotoInput.addEventListener('change', function () {
        const reader = new FileReader();
        reader.onload = function (e) {
            profilePhoto.src = e.target.result;
        };
        reader.readAsDataURL(this.files[0]);
    });

    // Subir foto de portada
    const uploadCoverInput = document.getElementById('upload-cover');
    const coverPhoto = document.getElementById('cover-photo');

    uploadCoverInput.addEventListener('change', function () {
        const reader = new FileReader();
        reader.onload = function (e) {
            coverPhoto.style.backgroundImage = `url('${e.target.result}')`;
        };
        reader.readAsDataURL(this.files[0]);
    });

    // Publicar texto
    const postButton = document.getElementById('post-button');
    const postText = document.getElementById('post-text');
    const postList = document.getElementById('post-list');

    postButton.addEventListener('click', function () {
        const text = postText.value.trim();
        if (text) {
            const newPost = document.createElement('div');
            newPost.classList.add('post');
            newPost.textContent = text;
            postList.prepend(newPost);
            postText.value = '';
        } else {
            alert('Escribe algo antes de publicar.');
        }
    });

    // Mostrar/Ocultar Configuración
    const configuracionBtn = document.getElementById('configuracion-btn');
    const configuracionSidebar = document.getElementById('configuracion');

    configuracionBtn.addEventListener('click', function () {
        const isVisible = configuracionSidebar.style.display === 'block';
        configuracionSidebar.style.display = isVisible ? 'none' : 'block';
    });
});
