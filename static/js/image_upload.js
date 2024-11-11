class ImageUploadHandler {
    constructor(inputElement, previewElement) {
        this.input = inputElement;
        this.preview = previewElement;
        this.setupListeners();
    }

    setupListeners() {
        this.input.addEventListener('change', this.handleFileSelect.bind(this));
    }

    async handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Validate file type
        const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
        if (!validTypes.includes(file.type)) {
            alert('Please select a valid image file (JPEG, PNG, or GIF)');
            return;
        }

        // Create form data
        const formData = new FormData();
        formData.append('image', file);

        try {
            const response = await fetch('/upload_image', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (response.ok) {
                // Create responsive image preview
                const img = document.createElement('img');
                const srcset = data.images
                    .map(img => `${img.path} ${img.width}w`)
                    .join(', ');
                
                img.src = data.images[1].path; // Use middle size as default
                img.srcset = srcset;
                img.sizes = "(max-width: 300px) 300px, (max-width: 600px) 600px, 900px";
                img.classList.add('img-fluid');
                
                // Clear previous preview and add new image
                this.preview.innerHTML = '';
                this.preview.appendChild(img);
            } else {
                throw new Error(data.error || 'Failed to upload image');
            }
        } catch (error) {
            console.error('Error uploading image:', error);
            alert(error.message);
        }
    }
}

// Initialize image upload handlers
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-image-upload]').forEach(input => {
        const previewId = input.dataset.imageUpload;
        const preview = document.getElementById(previewId);
        if (preview) {
            new ImageUploadHandler(input, preview);
        }
    });
});
