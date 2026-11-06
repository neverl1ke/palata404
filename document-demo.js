function updateDocumentDemo(){
    const variant=document.getElementById('demo-variant').value;
    const department=document.getElementById('demo-custom-department').value.trim()||document.getElementById('demo-department').value;
    document.querySelectorAll('[data-demo-variant]').forEach(paper=>{
        paper.style.setProperty('--demo-width',`${document.getElementById('demo-width').value}px`);
        paper.classList.toggle('hidden',variant!=='both'&&paper.dataset.demoVariant!=='layout'&&paper.dataset.demoVariant!==variant);
        paper.querySelector('document-header').setAttribute('department',department);
    });
    PalataI18n.refresh();
}
document.querySelector('.demo-controls').addEventListener('input',updateDocumentDemo);
updateDocumentDemo();
