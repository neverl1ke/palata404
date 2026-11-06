// Native elements fit the existing plain HTML/JS UI, without a second rendering framework.
(function(){
    const emblem='assets/ui/wardrobe/requested-header-emblem.webp';
    const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    class LocalizedDocumentElement extends HTMLElement{
        connectedCallback(){this._localeListener=()=>this.render();window.addEventListener('palata:localechange',this._localeListener);this.render();}
        disconnectedCallback(){window.removeEventListener('palata:localechange',this._localeListener);this._resize?.disconnect();}
        attributeChangedCallback(){if(this.isConnected)this.render();}
    }
    class DocumentHeader extends LocalizedDocumentElement{
        static observedAttributes=['variant','department','document-type','scale','stamps'];
        render(){
            const t=PalataI18n.t,variant=this.getAttribute('variant')==='center'?'center':'left';
            this.dataset.variant=variant;this.dataset.scale=this.getAttribute('scale')||'normal';
            const scale=Number(this.getAttribute('scale'))||({small:.9,large:1.15}[this.dataset.scale])||1;
            this.style.setProperty('--document-scale',Math.max(.85,Math.min(1.2,scale)));
            this.setAttribute('role','group');this.setAttribute('aria-label',`${t('documents.name1')} ${t('documents.name2')}`);
            const department=t(this.getAttribute('department')||'documents.wardrobe');
            this.innerHTML=`<div class="document-header-grid">${variant==='left'?'<img class="document-paperclip" src="assets/ui/documents/paperclip.png" alt="" aria-hidden="true">':''}<div class="document-emblem-cell"><img class="document-emblem" src="${emblem}" alt="${esc(t('documents.emblem'))}" draggable="false"></div><small class="document-ministry" data-fit-text>${esc(t('documents.ministry'))}</small><h2 class="document-institution" data-fit-text><span>${esc(t('documents.name1'))}</span><span>${esc(t('documents.name2'))}</span></h2><div class="document-department" data-fit-text>${esc(department)}${this.hasAttribute('document-type')?`<small>${esc(t(this.getAttribute('document-type')))}</small>`:''}</div>${variant==='center'&&this.hasAttribute('stamps')?'<document-stamp class="document-header-service" type="service" rotate="-11"></document-stamp><document-stamp class="document-header-seal" type="seal" rotate="8"></document-stamp>':''}</div>`;
            this._resize?.disconnect();this._resize=new ResizeObserver(()=>this.fit());this._resize.observe(this);
            this.fit();document.fonts?.ready.then(()=>{if(this.isConnected)this.fit();});
        }
        fit(){
            const tracks=getComputedStyle(this.querySelector('.document-header-grid')).gridTemplateRows.split(' ').map(parseFloat);
            this.querySelectorAll('[data-fit-text]').forEach(el=>{
                el.style.removeProperty('font-size');const base=parseFloat(getComputedStyle(el).fontSize);if(!base)return;
                const available=el.clientWidth;
                const lines=el.matches('.document-institution')?[...el.children]:[el];
                const width=Math.max(...lines.map(line=>line.scrollWidth));
                const row=Number(getComputedStyle(el).gridRowStart)-1;
                const ratio=Math.min(1,available>0?available/width:1,tracks[row]>0?tracks[row]/el.scrollHeight:1);
                if(ratio<1)el.style.setProperty('font-size',`${Math.max(base*.78,base*ratio)}px`,'important');
            });
        }
    }
    class DocumentStamp extends LocalizedDocumentElement{
        static observedAttributes=['type','label','rotate','opacity','position'];
        render(){
            const t=PalataI18n.t,type=this.getAttribute('type')||'service';this.dataset.type=type;
            const rotate=Number(this.getAttribute('rotate')||0),opacity=Number(this.getAttribute('opacity')??'.78');
            this.style.setProperty('--stamp-rotation',`${Number.isFinite(rotate)?Math.max(-30,Math.min(30,rotate)):0}deg`);
            this.style.setProperty('--stamp-opacity',Number.isFinite(opacity)?Math.max(0,Math.min(1,opacity)):'.78');
            const position=this.getAttribute('position');this.dataset.position=['left','right','center'].includes(position)?position:'';
            this.removeAttribute('role');this.removeAttribute('aria-label');
            if(type!=='seal'){this.textContent=t(this.getAttribute('label')||`documents.${type==='completed'?'completed':type==='archive'?'archive':'service'}`);return;}
            this.setAttribute('role','img');
            this.innerHTML='<img class="document-approved-seal" src="assets/ui/wardrobe/weapon-red-seal.svg" alt="">';
            this.setAttribute('aria-label',t('documents.sealTop')+' '+t('documents.number'));

        }
    }
    class DocumentPaper extends HTMLElement{connectedCallback(){this.classList.add('document-paper');}}
    class DocumentLayout extends HTMLElement{
        static observedAttributes=['variant','department','document-type','scale'];
        connectedCallback(){this.classList.add('document-paper','document-layout');this.updateHeader();}
        attributeChangedCallback(){if(this.isConnected)this.updateHeader();}
        updateHeader(){
            let header=this.querySelector(':scope > document-header');
            if(!header){header=document.createElement('document-header');this.prepend(header);}
            for(const name of DocumentLayout.observedAttributes){if(this.hasAttribute(name))header.setAttribute(name,this.getAttribute(name));}
        }
    }
    customElements.define('document-header',DocumentHeader);customElements.define('document-stamp',DocumentStamp);
    customElements.define('document-paper',DocumentPaper);customElements.define('document-layout',DocumentLayout);
    window.PalataDocuments=Object.freeze({emblem,header:({variant='left',department='documents.wardrobe',documentType='',scale='normal',stamps=false}={})=>`<document-header variant="${esc(variant)}" department="${esc(department)}" scale="${esc(scale)}"${documentType?` document-type="${esc(documentType)}"`:''}${stamps?' stamps':''}></document-header>`});
})();
