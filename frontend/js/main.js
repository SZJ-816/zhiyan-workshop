/**
 * 禅道项目管理系统 - Premium SPA 应用
 */
const API_BASE = '/api';
let currentUser = null;
let currentPage = '';
let token = localStorage.getItem('zentao_token');

// ===== API 客户端 =====
async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(API_BASE + path, { ...options, headers });
  if (res.status === 401) { logout(); throw new Error('认证失效'); }
  return res.json();
}

// ===== 认证 =====
async function login(account, password) {
  const data = await api('/auth/login', { method: 'POST', body: JSON.stringify({ account, password }) });
  if (data.access_token) {
    token = data.access_token;
    localStorage.setItem('zentao_token', token);
    currentUser = data.user;
    localStorage.setItem('zentao_user', JSON.stringify(data.user));
    return true;
  }
  throw new Error(data.detail || '登录失败');
}

function logout() {
  token = null;
  currentUser = null;
  localStorage.removeItem('zentao_token');
  localStorage.removeItem('zentao_user');
  showLogin();
}

function restoreSession() {
  const u = localStorage.getItem('zentao_user');
  if (u) {
    try { currentUser = JSON.parse(u); return true; } catch (e) {}
  }
  return token ? true : false;
}

// ===== 路由 =====
const pages = {
  'login': showLogin,
  'dashboard': showDashboard,
  'projects': showProjects,
  'tasks': showTasks,
  'products': showProducts,
  'bugs': showBugs,
  'users': showUsers,
  'reports': showReports,
};

function navigate(page) {
  currentPage = page;
  const fn = pages[page];
  if (fn) fn();
  // 更新侧边栏active
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  const navItem = document.querySelector(`.nav-item[data-page="${page}"]`);
  if (navItem) navItem.classList.add('active');
  // 关闭移动端侧边栏
  document.getElementById('sidebar').classList.remove('open');
}

// ===== 页面渲染 =====
const app = document.getElementById('app');
const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('main-content');

function showLogin() {
  sidebar.style.display = 'none';
  mainContent.style.marginLeft = '0';
  app.innerHTML = `
    <div style="min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,var(--bg-sidebar),#312e81);padding:20px">
      <div style="background:var(--bg-card);backdrop-filter:blur(30px);-webkit-backdrop-filter:blur(30px);border-radius:24px;padding:48px 40px;width:100%;max-width:420px;box-shadow:0 25px 60px rgba(0,0,0,0.2);border:1px solid rgba(255,255,255,0.1)">
        <div style="text-align:center;margin-bottom:32px">
          <div style="width:56px;height:56px;background:linear-gradient(135deg,var(--primary),var(--primary-light));border-radius:16px;display:inline-flex;align-items:center;justify-content:center;font-size:28px;margin-bottom:16px">🏯</div>
          <h1 style="font-size:24px;font-weight:800;color:var(--text);letter-spacing:-0.5px">禅道项目管理系统</h1>
          <p style="color:var(--text-muted);font-size:14px;margin-top:4px">Zentao Project Management</p>
        </div>
        <form id="loginForm" onsubmit="handleLogin(event)">
          <div class="form-group">
            <label class="form-label">账号</label>
            <input type="text" class="form-input" id="loginAccount" placeholder="请输入账号" value="admin" required>
          </div>
          <div class="form-group">
            <label class="form-label">密码</label>
            <input type="password" class="form-input" id="loginPassword" placeholder="请输入密码" value="123456" required>
          </div>
          <div id="loginError" style="color:var(--danger);font-size:13px;margin-bottom:12px;display:none"></div>
          <button type="submit" class="btn btn-primary" style="width:100%;padding:12px;font-size:15px">登录系统</button>
        </form>
        <div style="text-align:center;margin-top:20px;font-size:12px;color:var(--text-muted)">测试账号: admin / 123456</div>
      </div>
    </div>`;
}

window.handleLogin = async function(e) {
  e.preventDefault();
  const btn = e.target.querySelector('button');
  btn.disabled = true;
  btn.textContent = '登录中...';
  document.getElementById('loginError').style.display = 'none';
  try {
    const account = document.getElementById('loginAccount').value;
    const password = document.getElementById('loginPassword').value;
    await login(account, password);
    sidebar.style.display = 'flex';
    mainContent.style.marginLeft = '240px';
    updateSidebarUser();
    navigate('dashboard');
  } catch (err) {
    const el = document.getElementById('loginError');
    el.textContent = err.message;
    el.style.display = 'block';
  } finally {
    btn.disabled = false;
    btn.textContent = '登录系统';
  }
};

function updateSidebarUser() {
  if (!currentUser) return;
  document.getElementById('sidebarUserName').textContent = currentUser.realname;
  const roleMap = { admin: '管理员', pm: '项目经理', dev: '开发工程师', qa: '测试工程师', po: '产品负责人' };
  document.getElementById('sidebarUserRole').textContent = roleMap[currentUser.role] || currentUser.role;
  document.getElementById('sidebarAvatar').textContent = currentUser.realname[0];
  document.getElementById('sidebarAvatar').style.background = currentUser.avatar_color || '#6366f1';
}

// ===== Dashboard =====
async function showDashboard() {
  app.innerHTML = renderTopBar('仪表盘', '首页 / 我的地盘') + `
    <div class="page-content">
      <div id="statsGrid" class="stats-grid"><div class="loading"><div class="spinner"></div>加载统计...</div></div>
      <div class="grid-2" style="margin-bottom:16px">
        <div class="card" id="chartProject"></div>
        <div class="card" id="chartWeekly"></div>
      </div>
      <div class="grid-2">
        <div class="card">
          <div class="card-header"><div class="card-title">最近动态</div></div>
          <div class="activity-list" id="activityList"></div>
        </div>
        <div class="card">
          <div class="card-header"><div class="card-title">Bug严重程度分布</div></div>
          <div class="chart-container" id="chartBug"></div>
        </div>
      </div>
    </div>`;
  loadDashboard();
}

async function loadDashboard() {
  try {
    const res = await api('/dashboard/stats');
    const d = res.data;
    
    // 统计卡片
    document.getElementById('statsGrid').innerHTML = `
      <div class="stat-card"><div class="stat-icon" style="background:rgba(99,102,241,0.12);color:var(--primary)">📁</div><div class="stat-value">${d.total_projects}</div><div class="stat-label">项目总数</div></div>
      <div class="stat-card"><div class="stat-icon" style="background:rgba(34,197,94,0.12);color:var(--success)">✅</div><div class="stat-value">${d.total_tasks}</div><div class="stat-label">任务总数 · ${d.active_tasks} 进行中</div></div>
      <div class="stat-card"><div class="stat-icon" style="background:rgba(239,68,68,0.12);color:var(--danger)">🐛</div><div class="stat-value">${d.total_bugs}</div><div class="stat-label">Bug总数 · ${d.active_bugs} 待处理</div></div>
      <div class="stat-card"><div class="stat-icon" style="background:rgba(245,158,11,0.12);color:var(--warning)">📋</div><div class="stat-value">${d.my_tasks || 0}</div><div class="stat-label">我的待办 · ${d.my_bugs || 0} Bug</div></div>
      <div class="stat-card"><div class="stat-icon" style="background:rgba(59,130,246,0.12);color:var(--info)">📝</div><div class="stat-value">${d.total_stories}</div><div class="stat-label">用户需求 · ${d.active_stories} 活跃</div></div>
      <div class="stat-card"><div class="stat-icon" style="background:rgba(139,92,246,0.12);color:#8b5cf6">👥</div><div class="stat-value">${d.total_users}</div><div class="stat-label">团队成员</div></div>`;
    
    // 项目进度图
    renderProjectChart(d.project_progress || []);
    // 周完成图
    renderWeeklyChart(d.weekly_completed || []);
    // Bug分布
    renderBugChart(d.bug_severity || {});
    // 动态
    renderActivity(d.recent_activities || []);
  } catch (e) {
    document.getElementById('statsGrid').innerHTML = `<div class="loading">❌ ${e.message}</div>`;
  }
}

function renderProjectChart(data) {
  const el = document.getElementById('chartProject');
  if (!el) return;
  el.innerHTML = '<div class="card-header"><div class="card-title">项目进度</div></div><div class="chart-container" id="projectChart"></div>';
  if (!data.length) return;
  const chart = echarts.init(document.getElementById('projectChart'));
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 20, right: 30, top: 10, bottom: 20 },
    xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
    yAxis: { type: 'category', data: data.map(d => d.name), inverse: true, axisLabel: { fontSize: 11 } },
    series: [{
      type: 'bar', data: data.map(d => ({
        value: d.progress,
        itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{offset:0,color:'#6366f1'},{offset:1,color:'#818cf8'}]), borderRadius: [0, 4, 4, 0] }
      })), barWidth: 16, label: { show: true, position: 'right', formatter: '{c}%', fontSize: 11 }
    }]
  });
}

function renderWeeklyChart(data) {
  const el = document.getElementById('chartWeekly');
  if (!el) return;
  el.innerHTML = '<div class="card-header"><div class="card-title">近7天完成情况</div></div><div class="chart-container" id="weeklyChart"></div>';
  if (!data.length) return;
  const chart = echarts.init(document.getElementById('weeklyChart'));
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['完成任务', '解决Bug'], bottom: 0, textStyle: { fontSize: 11 } },
    grid: { left: 10, right: 10, top: 10, bottom: 30 },
    xAxis: { type: 'category', data: data.map(d => d.date) },
    yAxis: { type: 'value' },
    series: [
      { name: '完成任务', type: 'line', data: data.map(d => d.tasks_done), smooth: true, lineStyle: { color: '#22c55e' }, itemStyle: { color: '#22c55e' } },
      { name: '解决Bug', type: 'line', data: data.map(d => d.bugs_resolved), smooth: true, lineStyle: { color: '#ef4444' }, itemStyle: { color: '#ef4444' } }
    ]
  });
}

function renderBugChart(data) {
  const el = document.getElementById('chartBug');
  if (!el) return;
  if (!Object.keys(data).length) { el.innerHTML = '<div class="empty-state"><div class="empty-icon">📊</div>暂无数据</div>'; return; }
  const chart = echarts.init(el);
  const colors = { '致命': '#ef4444', '严重': '#f97316', '一般': '#f59e0b', '轻微': '#3b82f6', '建议': '#22c55e' };
  chart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie', radius: ['45%', '75%'], center: ['50%', '55%'],
      data: Object.entries(data).map(([k, v]) => ({ name: k, value: v, itemStyle: { color: colors[k] || '#6366f1' } })),
      label: { show: true, formatter: '{b}\n{c}' }
    }]
  });
}

function renderActivity(data) {
  const el = document.getElementById('activityList');
  if (!el) return;
  if (!data.length) { el.innerHTML = '<div class="empty-state"><div class="empty-icon">📭</div>暂无动态</div>'; return; }
  el.innerHTML = data.map(a => `
    <div class="activity-item">
      <div class="activity-dot"></div>
      <div>
        <div class="activity-text">${a.action}: ${a.object_name || ''}</div>
        <div class="activity-time">${a.created_at}</div>
      </div>
    </div>`).join('');
}

// ===== 通用页面框架 =====
function renderTopBar(title, breadcrumb) {
  return `<div class="top-bar">
    <div class="top-bar-left">
      <button class="menu-toggle" onclick="document.getElementById('sidebar').classList.toggle('open')">☰</button>
      <div>
        <div class="page-title">${title}</div>
        <div class="breadcrumb">${breadcrumb}</div>
      </div>
    </div>
    <div class="top-bar-right">
      <button class="theme-toggle" onclick="toggleTheme()" id="themeToggle">🌙</button>
    </div>
  </div>`;
}

function pageWrapper(title, breadcrumb, contentHtml) {
  return renderTopBar(title, breadcrumb) + `<div class="page-content">${contentHtml}</div>`;
}

// ===== 项目管理页 =====
async function showProjects() {
  app.innerHTML = pageWrapper('项目管理', '项目 / 全部项目', `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:10px">
      <div class="filter-bar" id="projectFilters">
        <span class="filter-chip active" data-filter="all" onclick="filterProjects('all',this)">全部</span>
        <span class="filter-chip" data-filter="doing" onclick="filterProjects('doing',this)">进行中</span>
        <span class="filter-chip" data-filter="waiting" onclick="filterProjects('waiting',this)">待启动</span>
        <span class="filter-chip" data-filter="done" onclick="filterProjects('done',this)">已完成</span>
        <span class="filter-chip" data-filter="closed" onclick="filterProjects('closed',this)">已关闭</span>
      </div>
      <button class="btn btn-primary" onclick="openProjectModal()">+ 新建项目</button>
    </div>
    <div id="projectList"><div class="loading"><div class="spinner"></div>加载中...</div></div>`);
  loadProjects();
}

async function loadProjects(status = '') {
  try {
    let url = '/projects?page_size=100';
    if (status && status !== 'all') url += '&status=' + status;
    const res = await api(url);
    const items = res.items || [];
    if (!items.length) {
      document.getElementById('projectList').innerHTML = '<div class="empty-state"><div class="empty-icon">📁</div>暂无项目</div>';
      return;
    }
    const statusMap = { waiting: '待启动', doing: '进行中', suspended: '已暂停', closed: '已关闭', done: '已完成' };
    const statusClass = { waiting: 'warning', doing: 'info', suspended: 'warning', closed: 'success', done: 'success' };
    document.getElementById('projectList').innerHTML = `
      <div class="table-wrapper">
        <table>
          <thead><tr><th>项目名称</th><th>项目代号</th><th>状态</th><th>进度</th><th>任务(完成/总数)</th><th>日期</th><th>操作</th></tr></thead>
          <tbody>${items.map(p => `
            <tr>
              <td style="font-weight:600;cursor:pointer;color:var(--primary)" onclick="navigate('tasks');projectTaskFilter=${p.id};setTimeout(()=>{showTasks();projectTaskFilter=null},100)">${p.name}</td>
              <td style="color:var(--text-muted);font-size:12px">${p.code}</td>
              <td><span class="badge badge-${statusClass[p.status]||'info'}">${statusMap[p.status]||p.status}</span></td>
              <td>
                <div>${p.progress||0}%</div>
                <div class="progress-bar"><div class="progress-fill" style="width:${p.progress||0}%"></div></div>
              </td>
              <td>${p.task_done||0} / ${p.task_count||0}</td>
              <td style="font-size:12px;color:var(--text-muted)">${p.start_date||''} ~ ${p.end_date||''}</td>
              <td><button class="btn btn-outline btn-xs" onclick="navigate('tasks');projectTaskFilter=${p.id}">任务</button></td>
            </tr>`).join('')}</tbody>
        </table>
      </div>`;
  } catch (e) {
    document.getElementById('projectList').innerHTML = `<div class="loading">❌ ${e.message}</div>`;
  }
}

window.filterProjects = function(status, el) {
  document.querySelectorAll('#projectFilters .filter-chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  loadProjects(status);
};

window.openProjectModal = function() {
  showModal('新建项目', `
    <div class="form-group"><label class="form-label">项目名称</label><input class="form-input" id="projName" placeholder="输入项目名称"></div>
    <div class="form-group"><label class="form-label">项目代号</label><input class="form-input" id="projCode" placeholder="如 SOP-V3"></div>
    <div class="form-group"><label class="form-label">描述</label><textarea class="form-textarea" id="projDesc"></textarea></div>
    <div class="grid-2"><div class="form-group"><label class="form-label">开始日期</label><input type="date" class="form-input" id="projStart"></div><div class="form-group"><label class="form-label">结束日期</label><input type="date" class="form-input" id="projEnd"></div></div>
    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" onclick="createProject()">创建</button>
    </div>`);
};

window.createProject = async function() {
  const data = {
    name: document.getElementById('projName').value,
    code: document.getElementById('projCode').value,
    description: document.getElementById('projDesc').value,
    start_date: document.getElementById('projStart').value || null,
    end_date: document.getElementById('projEnd').value || null
  };
  if (!data.name || !data.code) { alert('名称和代号必填'); return; }
  try {
    await api('/projects', { method: 'POST', body: JSON.stringify(data) });
    closeModal();
    loadProjects();
  } catch (e) { alert('创建失败: ' + e.message); }
};

// ===== 任务管理 =====
async function showTasks() {
  app.innerHTML = pageWrapper('任务管理', '项目 / 任务列表', `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:10px">
      <div class="filter-bar" id="taskFilters">
        <span class="filter-chip active" data-filter="all" onclick="loadTasks('',this)">全部</span>
        <span class="filter-chip" data-filter="todo" onclick="loadTasks('todo',this)">待办</span>
        <span class="filter-chip" data-filter="doing" onclick="loadTasks('doing',this)">进行中</span>
        <span class="filter-chip" data-filter="done" onclick="loadTasks('done',this)">已完成</span>
      </div>
      <div style="display:flex;gap:8px">
        <div class="search-box"><span>🔍</span><input id="taskSearch" placeholder="搜索任务..." onkeyup="searchTasks()"></div>
        <button class="btn btn-primary" onclick="openTaskModal()">+ 新建任务</button>
      </div>
    </div>
    <div id="taskStatusBar" style="display:flex;gap:8px;margin-bottom:16px"></div>
    <div id="taskList"><div class="loading"><div class="spinner"></div>加载中...</div></div>`);
  loadTasks();
}

async function loadTasks(status = '', triggerEl = null) {
  if (triggerEl) {
    document.querySelectorAll('#taskFilters .filter-chip').forEach(c => c.classList.remove('active'));
    triggerEl.classList.add('active');
  }
  try {
    let url = '/projects/1/tasks?page_size=200';
    if (status && status !== 'all') url += '&status=' + status;
    const res = await api(url);
    renderTasks(res);
  } catch (e) {
    document.getElementById('taskList').innerHTML = `<div class="loading">❌ ${e.message}</div>`;
  }
}

function renderTasks(res) {
  const items = res.items || [];
  const counts = res.status_counts || {};
  
  // 状态条
  const statusMap = { todo: '📋 待办', doing: '🔄 进行中', done: '✅ 已完成', closed: '🔒 已关闭' };
  document.getElementById('taskStatusBar').innerHTML = Object.entries(statusMap).map(([k, v]) => `
    <div style="flex:1;background:var(--bg-glass);border:1px solid var(--border);border-radius:10px;padding:10px;text-align:center;cursor:pointer" onclick="loadTasks('${k}',null)">
      <div style="font-size:20px;font-weight:700;color:var(--text)">${counts[k] || 0}</div>
      <div style="font-size:11px;color:var(--text-muted)">${v}</div>
    </div>`).join('');
  
  if (!items.length) {
    document.getElementById('taskList').innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div>暂无任务</div>';
    return;
  }
  
  const priorityMap = { high: '高', medium: '中', low: '低' };
  const statusBadge = { todo: 'warning', doing: 'info', done: 'success', closed: 'success' };
  const statusText = { todo: '待办', doing: '进行中', done: '已完成', closed: '已关闭' };
  
  document.getElementById('taskList').innerHTML = `
    <div class="table-wrapper">
      <table>
        <thead><tr><th>任务名称</th><th>优先级</th><th>状态</th><th>负责人</th><th>工时(预估/已耗)</th><th>截止日期</th><th>操作</th></tr></thead>
        <tbody>${items.map(t => `
          <tr>
            <td style="font-weight:500">${t.name}</td>
            <td><span class="badge badge-${t.priority==='high'?'danger':t.priority==='medium'?'warning':'info'}">${priorityMap[t.priority]||t.priority}</span></td>
            <td><span class="badge badge-${statusBadge[t.status]}">${statusText[t.status]||t.status}</span></td>
            <td style="font-size:13px">${t.assignee_name||'<span style="color:var(--text-muted)">未分配</span>'}</td>
            <td style="font-size:12px">${t.estimate}h / ${t.consumed}h</td>
            <td style="font-size:12px;color:${t.deadline&&t.status!=='done'?'var(--danger)':'var(--text-muted)'}">${t.deadline||''}</td>
            <td>
              ${t.status!=='done'?`<button class="btn btn-success btn-xs" onclick="updateTaskStatus(${t.id},'done')">完成</button>`:''}
              <button class="btn btn-outline btn-xs" onclick="updateTaskStatus(${t.id},'${t.status==='todo'?'doing':t.status==='doing'?'done':'todo'}')">⇄</button>
            </td>
          </tr>`).join('')}</tbody>
      </table>
    </div>`;
}

window.updateTaskStatus = async function(id, status) {
  try {
    await api(`/projects/tasks/${id}`, { method: 'PUT', body: JSON.stringify({ status }) });
    loadTasks();
  } catch (e) { alert(e.message); }
};

window.openTaskModal = async function() {
  let projectOptions = '<option value="">选择项目</option>';
  try {
    const res = await api('/projects?page_size=100');
    projectOptions += (res.items||[]).map(p => `<option value="${p.id}">${p.name}</option>`).join('');
  } catch(e) {}
  
  showModal('新建任务', `
    <div class="form-group"><label class="form-label">任务名称</label><input class="form-input" id="taskName" placeholder="输入任务名称"></div>
    <div class="form-group"><label class="form-label">项目</label><select class="form-select" id="taskProject">${projectOptions}</select></div>
    <div class="grid-2">
      <div class="form-group"><label class="form-label">优先级</label><select class="form-select" id="taskPriority"><option value="high">高</option><option value="medium" selected>中</option><option value="low">低</option></select></div>
      <div class="form-group"><label class="form-label">预估工时(h)</label><input type="number" class="form-input" id="taskEstimate" value="8"></div>
    </div>
    <div class="form-group"><label class="form-label">截止日期</label><input type="date" class="form-input" id="taskDeadline"></div>
    <div class="form-group"><label class="form-label">描述</label><textarea class="form-textarea" id="taskDesc"></textarea></div>
    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" onclick="createTask()">创建</button>
    </div>`);
};

window.createTask = async function() {
  const projectId = document.getElementById('taskProject').value;
  if (!projectId) { alert('请选择项目'); return; }
  const data = {
    name: document.getElementById('taskName').value,
    project_id: parseInt(projectId),
    priority: document.getElementById('taskPriority').value,
    estimate: parseFloat(document.getElementById('taskEstimate').value) || 0,
    deadline: document.getElementById('taskDeadline').value || null,
    description: document.getElementById('taskDesc').value || ''
  };
  if (!data.name) { alert('任务名称必填'); return; }
  try {
    await api(`/projects/${projectId}/tasks`, { method: 'POST', body: JSON.stringify(data) });
    closeModal();
    loadTasks();
  } catch (e) { alert('创建失败: ' + e.message); }
};

// ===== 产品管理 =====
async function showProducts() {
  app.innerHTML = pageWrapper('产品管理', '产品 / 全部产品', `
    <div style="display:flex;justify-content:flex-end;margin-bottom:16px">
      <button class="btn btn-primary" onclick="openProductModal()">+ 新建产品</button>
    </div>
    <div id="productList"><div class="loading"><div class="spinner"></div>加载中...</div></div>`);
  try {
    const res = await api('/products?page_size=100');
    const items = res.items || [];
    if (!items.length) {
      document.getElementById('productList').innerHTML = '<div class="empty-state"><div class="empty-icon">📦</div>暂无产品</div>';
    } else {
      document.getElementById('productList').innerHTML = items.map(p => `
        <div class="card" style="margin-bottom:12px">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <div style="font-weight:700;font-size:15px">${p.name}</div>
              <div style="font-size:12px;color:var(--text-muted);margin-top:4px">代号: ${p.code} · 状态: <span class="badge badge-success">${p.status}</span></div>
            </div>
            <button class="btn btn-outline btn-sm" onclick="navigate('tasks')">查看需求</button>
          </div>
        </div>`).join('');
    }
  } catch (e) {
    document.getElementById('productList').innerHTML = `<div class="loading">❌ ${e.message}</div>`;
  }
}

window.openProductModal = function() {
  showModal('新建产品', `
    <div class="form-group"><label class="form-label">产品名称</label><input class="form-input" id="pdName"></div>
    <div class="form-group"><label class="form-label">产品代号</label><input class="form-input" id="pdCode"></div>
    <div class="form-group"><label class="form-label">描述</label><textarea class="form-textarea" id="pdDesc"></textarea></div>
    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" onclick="createProduct()">创建</button>
    </div>`);
};

window.createProduct = async function() {
  const d = { name: document.getElementById('pdName').value, code: document.getElementById('pdCode').value, description: document.getElementById('pdDesc').value };
  if (!d.name || !d.code) { alert('名称和代号必填'); return; }
  await api('/products', { method: 'POST', body: JSON.stringify(d) });
  closeModal();
  showProducts();
};

// ===== Bug管理 =====
async function showBugs() {
  app.innerHTML = pageWrapper('Bug管理', '测试 / Bug列表', `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:10px">
      <div class="filter-bar" id="bugFilters">
        <span class="filter-chip active" onclick="filterBugs('',this)">全部</span>
        <span class="filter-chip" onclick="filterBugs('active',this)">未解决</span>
        <span class="filter-chip" onclick="filterBugs('resolved',this)">已解决</span>
        <span class="filter-chip" onclick="filterBugs('closed',this)">已关闭</span>
      </div>
      <button class="btn btn-primary" onclick="openBugModal()">+ 提交Bug</button>
    </div>
    <div id="bugList"><div class="loading"><div class="spinner"></div>加载中...</div></div>`);
  loadBugs();
}

async function loadBugs(filter = '') {
  try {
    let url = '/bugs?page_size=200';
    if (filter) url += '&status=' + filter;
    const res = await api(url);
    renderBugs(res);
  } catch (e) {
    document.getElementById('bugList').innerHTML = `<div class="loading">❌ ${e.message}</div>`;
  }
}

window.filterBugs = function(filter, el) {
  document.querySelectorAll('#bugFilters .filter-chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  loadBugs(filter);
};

function renderBugs(res) {
  const items = res.items || [];
  if (!items.length) { document.getElementById('bugList').innerHTML = '<div class="empty-state"><div class="empty-icon">🐛</div>暂无Bug</div>'; return; }
  const sevMap = { fatal: '致命', serious: '严重', normal: '一般', minor: '轻微' };
  const sevBadge = { fatal: 'danger', serious: 'danger', normal: 'warning', minor: 'info' };
  const statusBadge = { active: 'danger', resolved: 'success', closed: 'success' };
  const statusText = { active: '未解决', resolved: '已解决', closed: '已关闭' };
  document.getElementById('bugList').innerHTML = `
    <div class="table-wrapper"><table>
      <thead><tr><th>Bug标题</th><th>严重程度</th><th>状态</th><th>负责人</th><th>所属产品</th><th>创建时间</th><th>操作</th></tr></thead>
      <tbody>${items.map(b => `
        <tr>
          <td style="font-weight:500">${b.title}</td>
          <td><span class="badge badge-${sevBadge[b.severity]||'info'}">${sevMap[b.severity]||b.severity}</span></td>
          <td><span class="badge badge-${statusBadge[b.status]}">${statusText[b.status]||b.status}</span></td>
          <td>${b.assignee_name||'<span style="color:var(--text-muted)">未分配</span>'}</td>
          <td style="font-size:12px">${b.product_name||'-'}</td>
          <td style="font-size:12px;color:var(--text-muted)">${b.created_at?b.created_at.substring(0,10):''}</td>
          <td>
            <select class="form-select" style="width:auto;padding:4px 8px;font-size:11px" onchange="updateBugStatus(${b.id},this.value)"><option>操作</option><option value="resolved">已解决</option><option value="closed">关闭</option></select>
          </td>
        </tr>`).join('')}</tbody>
    </table></div>`;
}

window.updateBugStatus = async function(id, status) {
  if (!status || status === '操作') return;
  await api(`/bugs/${id}`, { method: 'PUT', body: JSON.stringify({ status }) });
  loadBugs();
};

window.openBugModal = async function() {
  let prodOpts = '<option value="">选择产品</option>';
  try { const r = await api('/products?page_size=100'); prodOpts += (r.items||[]).map(p => `<option value="${p.id}">${p.name}</option>`).join(''); } catch(e) {}
  showModal('提交Bug', `
    <div class="form-group"><label class="form-label">Bug标题</label><input class="form-input" id="bugTitle"></div>
    <div class="form-group"><label class="form-label">所属产品</label><select class="form-select" id="bugProduct">${prodOpts}</select></div>
    <div class="grid-2">
      <div class="form-group"><label class="form-label">严重程度</label><select class="form-select" id="bugSeverity"><option value="fatal">致命</option><option value="serious">严重</option><option value="normal" selected>一般</option><option value="minor">轻微</option></select></div>
      <div class="form-group"><label class="form-label">优先级</label><select class="form-select" id="bugPriority"><option value="5">最高</option><option value="4">高</option><option value="3" selected>中</option><option value="2">低</option><option value="1">最低</option></select></div>
    </div>
    <div class="form-group"><label class="form-label">复现步骤</label><textarea class="form-textarea" id="bugSteps"></textarea></div>
    <div class="form-group"><label class="form-label">描述</label><textarea class="form-textarea" id="bugDesc"></textarea></div>
    <div class="modal-actions"><button class="btn btn-outline" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="createBug()">提交</button></div>`);
};

window.createBug = async function() {
  const d = {
    title: document.getElementById('bugTitle').value,
    product_id: parseInt(document.getElementById('bugProduct').value) || null,
    severity: document.getElementById('bugSeverity').value,
    priority: parseInt(document.getElementById('bugPriority').value),
    steps: document.getElementById('bugSteps').value,
    description: document.getElementById('bugDesc').value
  };
  if (!d.title) { alert('标题必填'); return; }
  await api('/bugs', { method: 'POST', body: JSON.stringify(d) });
  closeModal();
  loadBugs();
};

// ===== 用户管理 =====
async function showUsers() {
  app.innerHTML = pageWrapper('用户管理', '组织 / 成员列表', `
    <div id="userList"><div class="loading"><div class="spinner"></div>加载中...</div></div>`);
  try {
    const res = await api('/users?page_size=100');
    const items = res.items || [];
    const roleMap = { admin: '管理员', pm: '项目经理', dev: '开发', qa: '测试', po: '产品' };
    if (!items.length) {
      document.getElementById('userList').innerHTML = '<div class="empty-state"><div class="empty-icon">👥</div>暂无用户</div>';
    } else {
      document.getElementById('userList').innerHTML = `
        <div class="table-wrapper"><table>
          <thead><tr><th>用户</th><th>账号</th><th>角色</th><th>部门</th><th>邮箱</th></tr></thead>
          <tbody>${items.map(u => `
            <tr>
              <td>
                <div style="display:flex;align-items:center;gap:10px">
                  <div class="user-avatar" style="width:32px;height:32px;font-size:13px;background:${u.avatar_color||'#6366f1'}">${u.realname[0]}</div>
                  <span style="font-weight:600">${u.realname}</span>
                </div>
              </td>
              <td style="color:var(--text-muted)">${u.account}</td>
              <td><span class="badge badge-info">${roleMap[u.role]||u.role}</span></td>
              <td>${u.department_name||'-'}</td>
              <td style="font-size:12px;color:var(--text-muted)">${u.email||'-'}</td>
            </tr>`).join('')}</tbody>
        </table></div>`;
    }
  } catch(e) {
    document.getElementById('userList').innerHTML = `<div class="loading">❌ ${e.message}</div>`;
  }
}

// ===== 报表 =====
async function showReports() {
  app.innerHTML = pageWrapper('统计报表', '报表 / 数据概览', `
    <div class="grid-2" style="margin-bottom:16px">
      <div class="card"><div class="card-header"><div class="card-title">任务完成统计</div></div><div class="chart-container" id="reportsTaskChart"></div></div>
      <div class="card"><div class="card-header"><div class="card-title">Bug严重程度</div></div><div class="chart-container" id="reportsBugChart"></div></div>
    </div>
    <div id="reportsLoading" class="loading"><div class="spinner"></div>加载中...</div>`);
  try {
    const [taskRes, dashboardRes] = await Promise.all([api('/users/reports/task-by-user'), api('/dashboard/stats')]);
    document.getElementById('reportsLoading').innerHTML = '';
    
    const tasks = taskRes.items || [];
    const chart1 = echarts.init(document.getElementById('reportsTaskChart'));
    chart1.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['总任务', '已完成'], bottom: 0 },
      grid: { left: 10, right: 10, top: 10, bottom: 30 },
      xAxis: { type: 'category', data: tasks.map(t => t.name), axisLabel: { rotate: 30, fontSize: 10 } },
      yAxis: { type: 'value' },
      series: [
        { name: '总任务', type: 'bar', data: tasks.map(t => t.total), itemStyle: { color: '#6366f1' } },
        { name: '已完成', type: 'bar', data: tasks.map(t => t.done), itemStyle: { color: '#22c55e' } }
      ]
    });
    
    const d = dashboardRes.data;
    const sevColors = { '致命': '#ef4444', '严重': '#f97316', '一般': '#f59e0b', '轻微': '#3b82f6' };
    const chart2 = echarts.init(document.getElementById('reportsBugChart'));
    chart2.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie', radius: ['45%', '75%'], center: ['50%','55%'],
        data: Object.entries(d.bug_severity).map(([k,v]) => ({ name: k, value: v, itemStyle: { color: sevColors[k] || '#6366f1' } })),
        label: { formatter: '{b}\n{c}' }
      }]
    });
  } catch(e) {
    document.getElementById('reportsLoading').innerHTML = `<div class="loading">❌ ${e.message}</div>`;
  }
}

// ===== 模态框 =====
function showModal(title, bodyHtml) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.id = 'modalOverlay';
  overlay.innerHTML = `<div class="modal">
    <div class="modal-title">${title}</div>
    ${bodyHtml}
  </div>`;
  overlay.onclick = function(e) { if (e.target === overlay) closeModal(); };
  document.body.appendChild(overlay);
}

function closeModal() {
  const el = document.getElementById('modalOverlay');
  if (el) el.remove();
}

// ===== 主题切换 =====
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? '' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  document.getElementById('themeToggle').textContent = next === 'dark' ? '☀️' : '🌙';
  localStorage.setItem('zentao_theme', next);
}

// ===== 搜索 =====
window.searchTasks = function() {
  // 搜索延迟
  clearTimeout(window._searchTimer);
  window._searchTimer = setTimeout(async () => {
    const val = document.getElementById('taskSearch').value.trim();
    if (!val) { loadTasks(); return; }
    // 简单前端过滤
    try {
      const res = await api('/projects/1/tasks?page_size=200&status=all');
      const filtered = (res.items||[]).filter(t => t.name.includes(val));
      renderTasks({ items: filtered, status_counts: res.status_counts });
    } catch(e) {}
  }, 300);
};

// ===== 初始化 =====
function init() {
  // 主题
  const saved = localStorage.getItem('zentao_theme');
  if (saved) { document.documentElement.setAttribute('data-theme', saved); }
  document.getElementById('themeToggle').textContent = saved === 'dark' ? '☀️' : '🌙';
  
  // 侧边栏导航
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', function(e) {
      e.preventDefault();
      const page = this.dataset.page;
      if (page) navigate(page);
    });
  });
  
  // 恢复会话
  if (restoreSession()) {
    sidebar.style.display = 'flex';
    mainContent.style.marginLeft = '240px';
    updateSidebarUser();
    navigate('dashboard');
  } else {
    showLogin();
  }
}

document.addEventListener('DOMContentLoaded', init);
