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
    link_init();
    proj_init();
    init_list_visibility();
    info_expanded_init();
});


function link_init() {
    const github = document.getElementById('github');
    const vercel = document.getElementById('vercel');

    github.onclick = function () {
        window.open("https://github.com/vshay1", "_blank")
    }
    vercel.onclick = function(){
        window.open("https://vercel.com/shadyflowey-6162s-projects", "_blank")
    }
}

function proj_init() {
    const projects = document.querySelectorAll('.list-item');
    for (const project of projects) {
        project.addEventListener('click', function () {
            document.getElementById('info-overlay').style.display = 'block';
            document.getElementById('expanded-info').style.display = 'block';
            document.getElementById('overview').click(); 
        });
    }
}
function info_expanded_init(){
    document.getElementById('info-overlay').addEventListener('click',()=>{
        document.getElementById('info-overlay').style.display='none';
        document.getElementById('expanded-info').style.display='none';
        document.querySelectorAll('.header-option').forEach(t => t.classList.remove('active'));
    });
    
    const buttons = document.querySelectorAll('.header-option');
    
    buttons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.stopPropagation();
            
            const targetView = button.id;
            
            const containers = document.querySelectorAll('.info-content');
            containers.forEach(container => {
                container.setAttribute('data-view', targetView);
            });
            
            document.querySelectorAll('.header-option').forEach(t => t.classList.remove('active'));
            
            button.classList.add('active');
        });
    });

    const galleryImgs = document.getElementById('gallery').children;
    for (image of galleryImgs){
        image.addEventListener('click', (e) => {
            console.log(e + 'clicked');
        });
    }
}

function init_list_visibility() {
    const toggleButtons = document.querySelectorAll('.toggle-list');

    for (const button of toggleButtons) {
        button.addEventListener('click', function () {
            const projectList = this.parentElement.parentElement;

            const parentHeight = this.parentElement.offsetHeight;
            if (this.classList.contains('clicked')) {
                projectList.style.maxHeight = 2000 + 'px';
                this.classList.remove('clicked');
                this.innerHTML = `<svg width="30" height="30" viewBox="0 0 16 16">
                                <path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0"/>
                                <path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8m8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7"/>
                                </svg>`;
            } else {
                projectList.style.maxHeight = (parentHeight - 1) + 'px';
                this.classList.add('clicked');
                this.innerHTML = `<svg width="30" height="30" viewBox="0 0 16 16">
                                <path d="m10.79 12.912-1.614-1.615a3.5 3.5 0 0 1-4.474-4.474l-2.06-2.06C.938 6.278 0 8 0 8s3 5.5 8 5.5a7 7 0 0 0 2.79-.588M5.21 3.088A7 7 0 0 1 8 2.5c5 0 8 5.5 8 5.5s-.939 1.721-2.641 3.238l-2.062-2.062a3.5 3.5 0 0 0-4.474-4.474z"/>
                                <path d="M5.525 7.646a2.5 2.5 0 0 0 2.829 2.829zm4.95.708-2.829-2.83a2.5 2.5 0 0 1 2.829 2.829zm3.171 6-12-12 .708-.708 12 12z"/>
                                </svg>`;
            }
        });
    }
}