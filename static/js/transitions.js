document.addEventListener('DOMContentLoaded', () => {
    // Add transition class to content
    const content = document.getElementById('content');
    content.classList.add('page-transition');
    
    // Handle all navigation clicks
    document.querySelectorAll('a[href]:not([target="_blank"])').forEach(link => {
        link.addEventListener('click', function(e) {
            // Don't handle hash links or different domain links
            if (this.getAttribute('href').startsWith('#') || 
                this.getAttribute('href').startsWith('http')) {
                return;
            }
            
            e.preventDefault();
            const targetHref = this.getAttribute('href');
            
            // Start exit animation
            content.classList.add('page-exit');
            
            // Navigate after animation
            setTimeout(() => {
                window.location.href = targetHref;
            }, 300); // Match this with CSS animation duration
        });
    });
    
    // Add entrance animation when page loads
    window.addEventListener('pageshow', () => {
        content.classList.remove('page-exit');
        content.classList.add('page-enter');
    });
});
