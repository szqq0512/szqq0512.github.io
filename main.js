(function () {
    // 变量声明
    const $ = {
        navMenu: document.getElementById('nav-menu'),
        treeView: document.getElementById('tree-view'),
        sidebar: document.getElementById('sidebar'),
        sidebarHeader: document.getElementById('sidebar-header'),
        content: document.getElementById('content'),
        toggleSidebar: document.getElementById('toggle-sidebar'),
        mobileMenuToggle: document.getElementById('mobile-menu-toggle'),
        topNav: document.getElementById('top-nav')
    };
    const searchInput = document.getElementById('search-input');
    const cache = {dirCache:{}, mdContent:{}, headings:{}, markedLoaded:false, currentFile:null, initialContentHTML:'', currentFolderPath:''};
    let fullTree = null;
    const cleanPath = p => p ? p.replace(/\\/g, '/').trim() : '';

    // 目录数据加载
    async function loadVxJson(path) {
        path = cleanPath(path||'');
        if (cache.dirCache[path]) return cache.dirCache[path];
        let url = path ? `旅游/${path}/vx.json` : '旅游/vx.json';
        try {
            let r = await fetch(url);
            if (!r.ok) return {folders:[],files:[]};
            let d = await r.json();
            cache.dirCache[path] = d; return d;
        } catch { return {folders:[],files:[]}; }
    }
    // 设置侧栏标题
    function setSidebarTitle(path) {
        const sidebarTitle = document.getElementById('sidebar-title');
        if (!sidebarTitle) return;
        if (!path || path === '') {
            sidebarTitle.textContent = '全部文件';
        } else {
            const arr = path.split('/');
            sidebarTitle.textContent = arr[arr.length-1] || '全部文件';
        }
    }
    async function loadFolder(path) {
        $.treeView.innerHTML = '<div class="loader"></div>';
        let d = await loadVxJson(path);
        $.treeView.innerHTML = '';
        d.folders.forEach(f=>$.treeView.appendChild(folderElem(f, path)));
        d.files.forEach(f=>$.treeView.appendChild(fileElem(f, path)));
        updateNav(path); $.content.innerHTML = cache.initialContentHTML;
        setSidebarTitle(path);
    }
    function folderElem(f, p) {
        let c = document.createElement('div'), e = document.createElement('div');
        e.className = 'folder'; e.innerHTML = '<span class="emoji-icon">📁</span>' + f.name;
        e.dataset.path = p?p+'/'+f.name:f.name; e.title = f.name;
        let ch = document.createElement('div'); ch.className = 'children';
        c.appendChild(e); c.appendChild(ch); return c;
    }
    function fileElem(f, p) {
        let c = document.createElement('div'), e = document.createElement('div');
        e.className = 'file';
        let n = f.name.endsWith('.md')?f.name.slice(0,-3):f.name;
        e.innerHTML = '<span class="emoji-icon">📄</span>' + n;
        e.dataset.path = p?p+'/'+f.name:f.name; e.title = n;
        let ch = document.createElement('div'); ch.className = 'children'; ch.style.display='none';
        c.appendChild(e); c.appendChild(ch); return c;
    }
    function updateNav(path) {
        let n = path.split('/')[0];
        document.querySelectorAll('#nav-menu a').forEach(a=>a.classList.toggle('active',a.dataset.path===n));
    }
    async function fetchMd(filePath) {
        let full = `旅游/${filePath}`;
        if (cache.mdContent[full]) return cache.mdContent[full];
        let r = await fetch(full); if (!r.ok) return '';
        let t = await r.text(); cache.mdContent[full]=t; return t;
    }
    function parseHeadings(md) {
        if (cache.headings[md]) return cache.headings[md];
        let h=[], t=window.marked.lexer(md);
        t.forEach(tok=>{if(tok.type==='heading'&&tok.depth<=3)h.push({level:tok.depth,text:tok.text})});
        cache.headings[md]=h; return h;
    }
    async function showMd(filePath, headingsContainer) {
        await checkMarkedLoaded();
        let md = await fetchMd(filePath), h = parseHeadings(md);
        let cont = document.createElement('div'); cont.className='markdown-container';
        let area = document.createElement('div'); area.className='markdown-content';
        let renderer = new window.marked.Renderer(), hid=0;
        renderer.heading = (t,l)=>`<h${l} id="heading-${l}-${hid++}">${t}</h${l}>`;
        area.innerHTML = window.marked.parse(md, {renderer});
        cont.appendChild(area);
        genHeadingsTree(h, headingsContainer);
        $.content.innerHTML = ''; $.content.appendChild(cont);
    }
    function genHeadingsTree(h, c) {
        c.innerHTML=''; c.style.display='block';
        h.forEach(he=>{
            let hi=document.createElement('div'); hi.className=`heading-item h${he.level}`;
            let icon=he.level===1?'›&nbsp; ':he.level===2?'&nbsp;»&nbsp; ':he.level===3?'&nbsp;&nbsp;»›&nbsp; ':'';
            hi.innerHTML=`<span class=\"emoji-icon\">${icon}</span><span>${he.text}</span>`;
            hi.onclick=e=>{e.stopPropagation();scrollToHeading(he.text,he.level)};
            c.appendChild(hi);
        });
    }
    function scrollToHeading(text, level) {
        let hs=document.querySelectorAll(`h${level}`);
        let t=Array.from(hs).find(h=>h.textContent===text);
        if(t){let c=document.querySelector('.markdown-container'),cr=c.getBoundingClientRect(),tr=t.getBoundingClientRect(),st=c.scrollTop,off=tr.top-cr.top+st-12;c.scrollTo({top:off,behavior:'smooth'});}
    }
    async function checkMarkedLoaded() {
        if (window.marked) return;
        await new Promise(r=>{let i=setInterval(()=>{if(window.marked){clearInterval(i);r();}},100)});
    }
    // 构建全量树
    async function buildFullTree() {
        async function walk(path) {
            const data = await loadVxJson(path);
            let node = {name: path.split('/').pop()||'根目录', path, type:'folder', children:[]};
            (data.folders||[]).forEach(f=>{
                node.children.push(walk(path?path+'/'+f.name:f.name));
            });
            (data.files||[]).forEach(f=>{
                node.children.push(Promise.resolve({name: f.name, path: path?path+'/'+f.name:f.name, type:'file'}));
            });
            node.children = await Promise.all(node.children);
            return node;
        }
        fullTree = await walk('');
    }
    // 渲染树，支持高亮和展开
    function renderTree(tree, filter = '') {
        $.treeView.innerHTML = '';
        function createNode(node) {
            let isMatch = false;
            if (filter && node.name && node.name.toLowerCase().includes(filter.toLowerCase())) isMatch = true;
            let hasMatchChild = false;
            let childrenEls = [];
            if (node.children && node.children.length) {
                for (const child of node.children) {
                    const childResult = createNode(child);
                    if (childResult && childResult.el) childrenEls.push(childResult.el);
                    if (childResult && childResult.hasMatch) hasMatchChild = true;
                }
            }
            const expanded = filter && (isMatch || hasMatchChild);
            let el;
            if (node.type === 'folder') {
                el = document.createElement('div');
                let folder = document.createElement('div');
                folder.className = 'folder' + (expanded ? ' expanded' : '');
                folder.innerHTML = '<span class="emoji-icon">' + (expanded ? '📂' : '📁') + '</span>' + node.name;
                folder.dataset.path = node.path;
                folder.title = node.name;
                if (isMatch) folder.classList.add('search-hit');
                let children = document.createElement('div');
                children.className = 'children';
                if (expanded) children.style.display = 'block';
                else children.style.display = '';
                childrenEls.forEach(childEl => children.appendChild(childEl));
                el.appendChild(folder);
                if (children.children.length) el.appendChild(children);
            } else {
                el = document.createElement('div');
                let file = document.createElement('div');
                file.className = 'file';
                let n = node.name.endsWith('.md') ? node.name.slice(0, -3) : node.name;
                file.innerHTML = '<span class="emoji-icon">📄</span>' + n;
                file.dataset.path = node.path;
                file.title = n;
                if (isMatch) file.classList.add('search-hit');
                let children = document.createElement('div');
                children.className = 'children';
                children.style.display = 'none';
                el.appendChild(file);
                el.appendChild(children);
            }
            return { el, hasMatch: isMatch || hasMatchChild };
        }
        let root = tree;
        (root.children || []).forEach(child => {
            const result = createNode(child);
            if (result && result.el) $.treeView.appendChild(result.el);
        });
    }
    // 清除树和内容区高亮
    function clearTreeSearchHighlight() {
        document.querySelectorAll('.tree-view .search-hit').forEach(el => el.classList.remove('search-hit'));
    }
    function clearContentSearchHighlight() {
        document.querySelectorAll('.markdown-content .search-hit').forEach(el => {
            el.outerHTML = el.innerText;
        });
    }
    function searchContent(keyword) {
        clearContentSearchHighlight();
        if (!keyword) return;
        const area = document.querySelector('.markdown-content');
        if (!area) return;
        // 只在纯文本节点中高亮，跳过标签
        const walk = document.createTreeWalker(area, NodeFilter.SHOW_TEXT, null, false);
        const nodes = [];
        while (walk.nextNode()) {
            nodes.push(walk.currentNode);
        }
        const reg = new RegExp(keyword.replace(/[.*+?^${}()|[\\]\]]/g, '\\$&'), 'gi');
        nodes.forEach(node => {
            if (!node.parentElement) return;
            if (!reg.test(node.nodeValue)) return;
            // 创建临时容器
            const temp = document.createElement('span');
            temp.innerHTML = node.nodeValue.replace(reg, match => `<span class=\"search-hit\">${match}</span>`);
            // 替换节点
            while (temp.firstChild) {
                node.parentNode.insertBefore(temp.firstChild, node);
            }
            node.parentNode.removeChild(node);
        });
        // 自动滚动到第一个高亮内容
        setTimeout(() => {
            const firstHit = area.querySelector('.search-hit');
            if (firstHit) {
                let scrollTarget = firstHit.closest('p, h1, h2, h3, h4, h5, h6, li, blockquote, div') || firstHit;
                const container = document.querySelector('.markdown-container');
                if (container && scrollTarget) {
                    const cRect = container.getBoundingClientRect();
                    const tRect = scrollTarget.getBoundingClientRect();
                    const offset = tRect.top - cRect.top + container.scrollTop - 24;
                    container.scrollTo({top: offset, behavior: 'smooth'});
                }
            }
        }, 0);
    }
    // 工具函数：清空搜索框及相关按钮
    function clearSearchInputAndBtn() {
        if (searchInput) searchInput.value = '';
        const clearBtn = document.getElementById('search-clear');
        if (clearBtn) clearBtn.style.display = 'none';
        const actionBtn = document.getElementById('search-action');
        if (actionBtn) actionBtn.style.visibility = 'hidden';
    }
    // 工具函数：仅在无结果提示栏可见时清空搜索框及按钮
    function clearSearchIfNoResultBarVisible() {
        const noResultBar = document.getElementById('search-no-result');
        if (noResultBar && noResultBar.style.display !== 'none') {
            clearSearchInputAndBtn();
        }
        if (noResultBar) noResultBar.style.display = 'none';
    }
    // 事件绑定
    $.navMenu.onclick=async e=>{
        if(e.target.tagName==='A'){
            e.preventDefault();
            clearSearchIfNoResultBarVisible();
            clearTreeSearchHighlight();
            clearContentSearchHighlight();
            let p=e.target.dataset.path;
            await loadFolder(p);
            $.content.innerHTML=cache.initialContentHTML;
            // 新增：窄屏下点击菜单自动展开侧栏
            if(window.innerWidth<=992 && $.sidebar.classList.contains('collapsed')){
                $.sidebar.classList.remove('collapsed');
                let icon = $.toggleSidebar.querySelector('.emoji-icon');
                $.toggleSidebar.setAttribute('data-collapsed', false);
                if (icon) icon.textContent = '▽';
            }
            if(window.innerWidth<=992)$.topNav.classList.remove('active');
        }
    };
    // 搜索类型切换与分流逻辑
    let searchMode = 'menu'; // menu 或 content
    const searchType = document.getElementById('search-type');
    const searchTypeLabel = document.getElementById('search-type-label');
    const searchTypeDropdown = document.getElementById('search-type-dropdown');
    if (searchType && searchTypeLabel && searchTypeDropdown) {
      searchType.onclick = function(e) {
        searchTypeDropdown.style.display = searchTypeDropdown.style.display === 'block' ? 'none' : 'block';
        e.stopPropagation();
      };
      document.addEventListener('click', function() {
        searchTypeDropdown.style.display = 'none';
      });
      // 鼠标移出下拉菜单自动收起
      searchTypeDropdown.addEventListener('mouseleave', function() {
        searchTypeDropdown.style.display = 'none';
      });
      searchTypeDropdown.querySelectorAll('div').forEach(opt => {
        opt.onclick = function(e) {
          searchMode = this.getAttribute('data-type');
          if (searchMode === 'menu') {
            searchTypeLabel.textContent = '菜单';
            searchInput.placeholder = '搜索菜单文档...';
          } else {
            searchTypeLabel.textContent = '内容';
            searchInput.placeholder = '搜索当前内容...';
          }
          searchTypeDropdown.style.display = 'none';
          e.stopPropagation(); // 新增：阻止冒泡，防止窄屏下偶发不收起
          // 切换类型时：有文字则不清空，仅清除高亮并刷新搜索；无文字时才清空高亮
          if (searchInput.value) {
            clearTreeSearchHighlight();
            clearContentSearchHighlight();
            searchHandler();
          } else {
            clearTreeSearchHighlight();
            clearContentSearchHighlight();
          }
          // 新增：窄屏下切换类型时自动隐藏虚拟键盘
          if (window.innerWidth <= 992) {
            searchInput.blur();
          } else {
            searchInput.focus();
          }
        };
      });
    }
    // 搜索逻辑封装
    async function searchHandler() {
        const val = searchInput.value.trim();
        const clearBtn = document.getElementById('search-clear');
        const noResultBar = document.getElementById('search-no-result');
        if (clearBtn) clearBtn.style.display = val ? 'block' : 'none';
        clearTreeSearchHighlight();
        clearContentSearchHighlight();
        const sidebarTitle = document.getElementById('sidebar-title');
        if (sidebarTitle) {
            if (val) sidebarTitle.textContent = '请选择文件';
            else setSidebarTitle(cache.currentFolderPath);
        }
        if (window.innerWidth <= 992 && $.sidebar.classList.contains('collapsed')) {
            $.sidebar.classList.remove('collapsed');
            let icon = $.toggleSidebar.querySelector('.emoji-icon');
            $.toggleSidebar.setAttribute('data-collapsed', false);
            if (icon) icon.textContent = '▽';
        }
        if (!val) {
            let d = await loadVxJson(cache.currentFolderPath || '');
            $.treeView.innerHTML = '';
            d.folders.forEach(f=>$.treeView.appendChild(folderElem(f, cache.currentFolderPath)));
            d.files.forEach(f=>$.treeView.appendChild(fileElem(f, cache.currentFolderPath)));
            $.content.innerHTML = cache.initialContentHTML;
            if (noResultBar) noResultBar.style.display = 'none';
            return;
        }
        if (searchMode === 'menu') {
            if (!fullTree) await buildFullTree();
            renderTree(fullTree, val);
            // 判断是否有高亮项
            setTimeout(async ()=>{
                const firstMenu = document.querySelector('.tree-view .search-hit');
                if(firstMenu) {
                  firstMenu.scrollIntoView({behavior:'smooth', block:'center'});
                  if (noResultBar) noResultBar.style.display = 'none';
                  // 新增：如果第一个高亮是文件，自动打开
                  if(firstMenu.classList.contains('file')) {
                    // 触发文件点击逻辑，自动显示内容
                    // 先清除之前激活
                    document.querySelectorAll('.file,.folder').forEach(el=>el.classList.remove('active'));
                    firstMenu.classList.add('active','expanded');
                    // 记录当前文件
                    cache.currentFile = firstMenu;
                    // 打开内容
                    await showMd(firstMenu.dataset.path, firstMenu.parentElement.querySelector('.children'));
                  }
                } else {
                  if (noResultBar) noResultBar.style.display = 'block';
                }
            }, 0);
        } else if (searchMode === 'content') {
            searchContent(val);
            // 判断内容区是否有高亮
            setTimeout(()=>{
                const area = document.querySelector('.markdown-content');
                const hit = area && area.querySelector('.search-hit');
                if (hit) {
                  if (noResultBar) noResultBar.style.display = 'none';
                } else {
                  if (noResultBar) noResultBar.style.display = 'block';
                }
            }, 0);
        }
    }
    // 替换 input 事件绑定，只控制按钮显隐，不触发搜索
    searchInput.addEventListener('input', function() {
        const actionBtn = document.getElementById('search-action');
        if (actionBtn) actionBtn.style.visibility = this.value ? 'visible' : 'hidden';
        // 不自动搜索
        clearTreeSearchHighlight();
        clearContentSearchHighlight();
        const noResultBar = document.getElementById('search-no-result');
        if (noResultBar) noResultBar.style.display = 'none';
    });
    // 按下Enter键才触发搜索
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            searchHandler();
            // 移动端收起虚拟键盘
            if (window.innerWidth <= 992) {
                searchInput.blur();
            }
        }
        // Backspace 为空时阻止网页后退，只清除高亮
        if (e.key === 'Backspace' && !searchInput.value) {
            e.preventDefault();
            searchInput.value = '';
            const actionBtn = document.getElementById('search-action');
            if (actionBtn) actionBtn.style.visibility = 'hidden';
            clearTreeSearchHighlight();
            clearContentSearchHighlight();
            const noResultBar = document.getElementById('search-no-result');
            if (noResultBar) noResultBar.style.display = 'none';
            searchInput.focus();
        }
    });
    // 搜索按钮点击事件
    const actionBtn = document.getElementById('search-action');
    if (actionBtn) {
        actionBtn.addEventListener('click', function(e) {
            searchHandler();
            // 移动端收起虚拟键盘
            if (window.innerWidth <= 992) {
                searchInput.blur();
            } else {
                searchInput.focus();
            }
        });
        // 初始隐藏
        actionBtn.style.visibility = searchInput.value ? 'visible' : 'hidden';
    }
    $.treeView.onclick=async e=>{
        let f=e.target.closest('.folder'),file=e.target.closest('.file');
        // 新增：窄屏下菜单折叠时，点击顶级菜单自动展开侧栏
        if (f && window.innerWidth <= 992 && $.sidebar.classList.contains('collapsed')) {
            $.sidebar.classList.remove('collapsed');
            let icon = $.toggleSidebar.querySelector('.emoji-icon');
            $.toggleSidebar.setAttribute('data-collapsed', false);
            if (icon) icon.textContent = '▽';
        }
        if(f){
            let ch=f.parentElement.querySelector('.children');
            ch.querySelectorAll('.folder.expanded').forEach(sf=>{sf.classList.remove('expanded');let se=sf.querySelector('.emoji-icon');if(se)se.textContent='📁';});
            ch.querySelectorAll('.children').forEach(sc=>sc.style.display='none');
            f.classList.toggle('expanded');
            let em=f.querySelector('.emoji-icon');
            if(f.classList.contains('expanded')){
                if(em)em.textContent='📂';
                if(ch.children.length===0){
                    let d=await loadVxJson(f.dataset.path);ch.innerHTML='';
                    d.folders.forEach(sf=>ch.appendChild(folderElem(sf,f.dataset.path)));
                    d.files.forEach(fi=>ch.appendChild(fileElem(fi,f.dataset.path)));
                }
                ch.style.display='block';
            }else{if(em)em.textContent='📁';ch.style.display='none';}
        }else if(file){
            let ch=file.parentElement.querySelector('.children');
            if(cache.currentFile===file){let o=ch.style.display==='block';ch.style.display=o?'none':'block';file.classList.toggle('expanded',!o);return;}
            if(cache.currentFile){let pch=cache.currentFile.parentElement.querySelector('.children');if(pch)pch.style.display='none';cache.currentFile.classList.remove('expanded','active');}
            cache.currentFile=file;document.querySelectorAll('.file,.folder').forEach(el=>el.classList.remove('active'));
            file.classList.add('active','expanded');
            await showMd(file.dataset.path,ch);
        }
        clearSearchIfNoResultBarVisible();
    };
    // 内容区点击也仅在无结果提示栏可见时清空搜索框
    $.content.onclick = function() {
        clearSearchIfNoResultBarVisible();
    };
    $.sidebarHeader.onclick = (e) => {
        if (e.target.closest('#toggle-sidebar')) {
            if(window.innerWidth<=992){
                $.sidebar.classList.toggle('collapsed');
                let icon=$.toggleSidebar.querySelector('.emoji-icon'),col=$.sidebar.classList.contains('collapsed');
                $.toggleSidebar.setAttribute('data-collapsed',col);
                icon.textContent=col?'△':'▽';
            }
        }
    };
    $.mobileMenuToggle.onclick=()=>{$.topNav.classList.toggle('active');};
    // 页面初始化
    (async function(){
        cache.initialContentHTML=$.content.innerHTML;
        let d=await loadVxJson('');
        if(d.folders&&d.folders.length){
            $.navMenu.innerHTML='';
            d.folders.forEach(f=>{let li=document.createElement('li'),a=document.createElement('a');a.href='#';a.textContent=f.name;a.dataset.path=f.name;li.appendChild(a);$.navMenu.appendChild(li);});
            cache.currentFolderPath = d.folders[0].name;
            await loadFolder(cache.currentFolderPath);
        }
        setSidebarTitle(cache.currentFolderPath);
    })();
})();
