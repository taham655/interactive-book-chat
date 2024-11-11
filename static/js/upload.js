document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    const fileInput = document.getElementById('bookFile');
    formData.append('file', fileInput.files[0]);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (data.success) {
            window.location.reload();
        } else {
            alert('Upload failed: ' + data.error);
        }
    } catch (error) {
        alert('Upload failed: ' + error.message);
    }
});
