document.addEventListener('DOMContentLoaded', function() {
    console.log('📚 Documentación cargada');
    
    if (typeof mermaid !== 'undefined') {
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default'
        });
    }
});
