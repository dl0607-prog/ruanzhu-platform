/* Server-managed account sessions; no credentials stored in localStorage. */
async function requireLogin() {
  let user = await fetch('/api/auth/me').then(r => r.ok ? r.json() : null);
  if (!user) {
    await new Promise(resolve => {
      const overlay = document.createElement('div');
      overlay.className = 'modal-mask';
      overlay.style.zIndex = '9999';
      overlay.innerHTML = `<form class="modal" style="max-width:440px"><div class="modal-head"><h3>登录软著工场</h3></div><div class="modal-body"><p>每个账号独立管理项目和申请材料。账号由管理员创建。</p><div class="field"><label>账号</label><input name="username" autocomplete="username" required maxlength="80"></div><div class="field"><label>密码</label><input name="password" type="password" autocomplete="current-password" required maxlength="256"></div><p class="login-error" role="alert"></p><button class="btn btn-primary" type="submit">登录</button></div></form>`;
      document.body.appendChild(overlay);
      overlay.querySelector('form').onsubmit = async e => {
        e.preventDefault();
        const button = overlay.querySelector('button');
        button.disabled = true;
        try {
          const form = new FormData(e.target);
          const response = await fetch('/api/auth/login', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(Object.fromEntries(form))});
          if (!response.ok) {
            const error = await response.json();
            throw new Error(typeof error.detail === 'string' ? error.detail : '请检查账号及密码，密码至少12位');
          }
          user = await fetch('/api/auth/me').then(r => r.ok ? r.json() : null);
          if (!user) throw new Error('会话未生效：服务器需使用 HTTPS；本机测试请设置 COOKIE_SECURE=false');
          overlay.remove(); resolve();
        } catch (error) { overlay.querySelector('.login-error').textContent = error.message; }
        finally { button.disabled = false; }
      };
    });
  }
  window.sessionUser = user;
  const bar = document.createElement('div');
  bar.className = 'row';
  bar.style.padding = '10px';
  const name = document.createElement('span'); name.textContent = user.username;
  const logout = document.createElement('button'); logout.className = 'btn btn-ghost btn-sm'; logout.textContent = '退出登录';
  logout.onclick = async () => { await fetch('/api/auth/logout', {method:'POST'}); location.reload(); };
  bar.append(name, logout);
  if (user.admin) {
    const add = document.createElement('button'); add.className = 'btn btn-ghost btn-sm'; add.textContent = '创建账号';
    add.onclick = () => {
      const modal = document.createElement('div'); modal.className = 'modal-mask';
      modal.innerHTML = `<form class="modal" style="max-width:440px"><div class="modal-body"><h3>创建成员账号</h3><div class="field"><label>账号（字母、数字、_.@-）</label><input name="username" required pattern="[A-Za-z0-9_.@-]+" maxlength="80"></div><div class="field"><label>初始密码（至少12位）</label><input name="password" type="password" required minlength="12" maxlength="256" autocomplete="new-password"></div><p role="alert"></p><button class="btn btn-primary">创建</button> <button type="button" class="btn close-account">取消</button></div></form>`;
      modal.querySelector('.close-account').onclick = () => modal.remove();
      modal.querySelector('form').onsubmit = async e => {
        e.preventDefault();
        const button = e.target.querySelector('button'); button.disabled = true;
        try {
          const res = await fetch('/api/auth/users', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});
          const data = await res.json();
          if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : '字段格式不正确');
          modal.remove(); toast('账号已创建');
        } catch (error) { modal.querySelector('[role="alert"]').textContent = error.message; }
        finally { button.disabled = false; }
      };
      document.body.appendChild(modal);
    };
    bar.append(add);
  }
  (document.querySelector('.sidebar') || document.body).appendChild(bar);
}
