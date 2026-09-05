document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function(){
        const loader = document.querySelector('.loading-page');
        if (loader) {
            loader.style.opacity = '0';
            setTimeout(function() {
                loader.style.display = 'none';
            }, 500); 
        }

        const content = document.querySelector('.content-box');
        if (content) content.style.display = 'block';
    }, 2000);
    document.getElementById('contact-me-btn').onclick = function() {
        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: 'smooth'
        });
    };

    init_info_list();
});


function init_info_list() {
    const toggleButtons = document.querySelectorAll('.info-list-header');

    
    for (const button of toggleButtons) {
        button.addEventListener('click', function () {
            const body = this.nextElementSibling; 
            
            if (this.classList.contains('clicked')) {
                body.style.maxHeight = '0px';
                this.classList.remove('clicked');
            } else {
                body.style.maxHeight = body.scrollHeight + 'px';
                this.classList.add('clicked');
            }
        });
    }

}

