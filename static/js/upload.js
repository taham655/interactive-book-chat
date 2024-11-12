document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.querySelector('.upload-area');
    const fileInput = document.getElementById('bookFile');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        uploadArea.classList.add('highlight');
    }

    function unhighlight(e) {
        uploadArea.classList.remove('highlight');
    }

    uploadArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length > 0) {
            fileInput.files = files;
            uploadFile(files[0]);
        }
    }

    fileInput.addEventListener('change', function(e) {
        if (this.files.length > 0) {
            uploadFile(this.files[0]);
        }
    });

    function uploadFile(file) {
        if (file.type !== 'application/pdf') {
            alert('Please upload a PDF file');
            return;
        }

        if (file.size > 16 * 1024 * 1024) {
            alert('File size must be less than 16MB');
            return;
        }

        // Handle the file upload here
        const formData = new FormData();
        formData.append('file', file);

        // Add your upload API endpoint here
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Handle successful upload
            window.location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while uploading the file');
        });
    }

    // Tab functionality
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            // Add active class to clicked button
            button.classList.add('active');
            // Add your filtering logic here
        });
    });

    // Search functionality
    const searchInput = document.querySelector('.search-input');
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const books = document.querySelectorAll('.book-card');

        books.forEach(book => {
            const title = book.querySelector('.book-title').textContent.toLowerCase();
            if (title.includes(searchTerm)) {
                book.style.display = '';
            } else {
                book.style.display = 'none';
            }
        });
    });

    // Sort functionality
    const filterSelect = document.querySelector('.filter-select');
    filterSelect.addEventListener('change', (e) => {
        const sortBy = e.target.value;
        // Add your sorting logic here
    });
});
