document.addEventListener('DOMContentLoaded', function() {
    // Handle adding books to libraries
    document.querySelectorAll('.add-to-library').forEach(button => {
        button.addEventListener('click', async function() {
            const libraryId = this.dataset.libraryId;
            const bookId = this.dataset.bookId;
            
            try {
                const response = await fetch(`/library/${libraryId}/add_book/${bookId}`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    alert('Book added to library successfully');
                } else {
                    const data = await response.json();
                    alert(data.error || 'Failed to add book to library');
                }
            } catch (error) {
                alert('Failed to add book to library: ' + error.message);
            }
        });
    });

    // Handle toggling favorites
    document.querySelectorAll('.toggle-favorite').forEach(button => {
        button.addEventListener('click', async function() {
            const type = this.dataset.type;
            const id = this.dataset.id;
            
            try {
                const response = await fetch('/favorites/toggle', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `${type}_id=${id}`
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.action === 'added') {
                        this.classList.remove('btn-outline-danger');
                        this.classList.add('btn-danger');
                        this.textContent = type === 'book' ? 'Remove from Favorites' : '';
                        if (type === 'character') {
                            this.innerHTML = '<i class="bi bi-heart"></i>';
                        }
                    } else {
                        this.classList.remove('btn-danger');
                        this.classList.add('btn-outline-danger');
                        this.textContent = type === 'book' ? 'Add to Favorites' : '';
                        if (type === 'character') {
                            this.innerHTML = '<i class="bi bi-heart-fill"></i>';
                        }
                    }
                } else {
                    const data = await response.json();
                    alert(data.error || 'Failed to update favorite');
                }
            } catch (error) {
                alert('Failed to update favorite: ' + error.message);
            }
        });
    });
});
