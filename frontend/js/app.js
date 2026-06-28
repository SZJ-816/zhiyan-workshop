/**
 * WorkNest - 智能项目协作平台
 * Premium SPA with ECharts visualization
 */
const API_BASE = '/api';
let currentUser = null;
let currentPage = '';
let token = localStorage.getItem('wn_token');

// ===== API Client =====
async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = 'Bearer ' + token;
  const res = await fetch(API_BASE + path, { ...options, headers });
  if (res.status === 401) { logout(); throw new Error('auth_expired'); }
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

// ===== Auth =====
async function login(account, password) {
  const data = await api('/auth/login', {
    method: 'POST', body: JSON.stringify({ account, password })
  });
  if (data.access_token) {
    token = data.access_token;
    localStorage.setItem('wn_token', token);
    currentUser = data.user;
    localStorage.setItem('wn_user', JSON.stringify(data.user));
    return true;
  }
  throw new Error(data.detail || 'login_failed');
}

function logout() {
  token = null; currentUser = null;
  localStorage.removeItem('wn_token');
  localStorage.removeItem('wn_user');
  showLogin();
}

function restoreSession() {
  if (!token) return false;
  const u = localStorage.getItem('wn_user');
  if (u) { try { currentUser = JSON.parse(u); return true; } catch (e) {} }
  return true;
}

// ===== Router =====
const pages = {
  'dashboard': showDashboard,
  'projects': showProjects,
  'tasks': showTasks,
  'products': showProducts,
  'bugs': showBugs,
  'users': showUsers,
  'reports': showReports,
  'ai-chat': showAIChat,
  'ai-analytics': showAIAnalytics,
  'ai-prediction': showAIPrediction,
  'ai-realtime': showAIRealtime,
  'ai-datamanage': showAIDatamanage,
  'launcher': showLauncher,
};

function navigate(page) {
  if (!token && page !== 'login') { showLogin(); return; }
  // Clean up AI page side-effects when leaving
  if (currentPage && currentPage !== page) {
    if (typeof clearAIIntervals === 'function') clearAIIntervals();
  }
  currentPage = page;
  const fn = pages[page];
  if (fn) fn();
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  const nav = document.querySelector('.nav-item[data-page="' + page + '"]');
  if (nav) nav.classList.add('active');
  document.getElementById('sidebar').classList.remove('open');
}

// ===== DOM shortcuts =====
const app = document.getElementById('app');
const sidebar = document.getElementById('sidebar');
const mainArea = document.getElementById('mainArea');

// ===== Theme =====
function initTheme() {
  const saved = localStorage.getItem('wn_theme');
  if (saved === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? '' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('wn_theme', next);
  updateThemeIcon();
}

function updateThemeIcon() {
  // Theme toggle is rendered inside pages, so check existence
  const btn = document.getElementById('themeToggle');
  if (!btn) return;
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  btn.innerHTML = isDark
    ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'
    : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>';
}

// ===== Login =====
function showLogin() {
  sidebar.style.display = 'none';
  mainArea.style.marginLeft = '0';
  app.innerHTML = `
    <div class="login-page">
      <div class="login-card">
        <div class="login-panel">
          <div class="login-header">
            <div class="login-logo">
              <svg viewBox="0 0 56 56" fill="none">
                <rect width="56" height="56" rx="16" fill="url(#loginGrad)"/>
                <path d="M16 40V22l12 9 12-9v18" stroke="#fff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
                <defs><linearGradient id="loginGrad" x1="0" y1="0" x2="56" y2="56"><stop stop-color="#0ea5e9"/><stop offset="1" stop-color="#0284c7"/></linearGradient></defs>
              </svg>
            </div>
            <h1 class="login-title">WorkNest</h1>
            <p class="login-subtitle">智能项目协作平台</p>
          </div>
          <form id="loginForm" onsubmit="handleLogin(event)">
            <div class="form-group">
              <label class="form-label">账号</label>
              <input type="text" class="form-input" id="loginAccount" placeholder="请输入账号" value="admin" autocomplete="username" required>
            </div>
            <div class="form-group">
              <label class="form-label">密码</label>
              <input type="password" class="form-input" id="loginPassword" placeholder="请输入密码" value="123456" autocomplete="current-password" required>
            </div>
            <div id="loginError" style="color:var(--danger);font-size:13px;margin-bottom:12px;display:none"></div>
            <button type="submit" class="btn btn-primary" style="width:100%;padding:12px;font-size:15px">登录系统</button>
          </form>
          <div class="login-hint">演示账号: admin / 123456</div>
        </div>
      </div>
    </div>`;
}

window.handleLogin = async function(e) {
  e.preventDefault();
  const btn = e.target.querySelector('button');
  const errEl = document.getElementById('loginError');
  btn.disabled = true; btn.textContent = '登录中...';
  errEl.style.display = 'none';
  try {
    await login(
      document.getElementById('loginAccount').value,
      document.getElementById('loginPassword').value
    );
    sidebar.style.display = 'flex';
    mainArea.style.marginLeft = 'var(--sidebar-w)';
    updateSidebarUser();
    navigate('dashboard');
  } catch (err) {
    errEl.textContent = err.message === 'auth_expired' ? '请重新登录' : err.message;
    errEl.style.display = 'block';
  } finally {
    btn.disabled = false; btn.textContent = '登录系统';
  }
};

function updateSidebarUser() {
  if (!currentUser) return;
  document.getElementById('sidebarUserName').textContent = currentUser.realname;
  const roleMap = { admin: '系统管理员', pm: '项目经理', dev: '开发工程师', qa: '测试工程师', po: '产品负责人' };
  document.getElementById('sidebarUserRole').textContent = roleMap[currentUser.role] || currentUser.role;
  document.getElementById('sidebarAvatar').textContent = currentUser.realname[0];
  document.getElementById('sidebarAvatar').style.background = currentUser.avatar_color || 'var(--brand-600)';
}

// ===== Top Bar =====
function renderTopBar(title, breadcrumb) {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const moonIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>';
  const sunIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
  return '<div class="topbar">'
    + '<div class="topbar-left">'
    + '<button class="menu-btn" onclick="document.getElementById(\'sidebar\').classList.toggle(\'open\')">'
    + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>'
    + '</button>'
    + '<div>'
    + '<div class="page-heading">' + title + '</div>'
    + '<div class="breadcrumb">' + breadcrumb + '</div>'
    + '</div>'
    + '</div>'
    + '<div class="topbar-right">'
    + '<button class="theme-switch" onclick="toggleTheme()" id="themeToggle">' + (isDark ? sunIcon : moonIcon) + '</button>'
    + '</div>'
    + '</div>';
}

function pageWrap(title, breadcrumb, content) {
  return renderTopBar(title, breadcrumb) + '<div class="page-body">' + content + '</div>';
}

// ===== Dashboard =====
function showDashboard() {
  app.innerHTML = pageWrap('仪表盘', '首页 / 工作概览',
    '<div id="statsRow" class="stats-row"><div class="state-loading"><div class="spin"></div>加载统计...</div></div>'
    + '<div class="chart-grid">'
    + '<div class="card" id="chartProjWrap"><div class="card-hdr"><div class="card-title">项目进度</div></div><div class="chart-box" id="chartProj"></div></div>'
    + '<div class="card" id="chartWeekWrap"><div class="card-hdr"><div class="card-title">近期完成趋势</div></div><div class="chart-box" id="chartWeek"></div></div>'
    + '</div>'
    + '<div class="chart-grid">'
    + '<div class="card"><div class="card-hdr"><div class="card-title">最近动态</div></div><div class="feed-list" id="feedList"></div></div>'
    + '<div class="card"><div class="card-hdr"><div class="card-title">缺陷严重程度分布</div></div><div class="chart-box" id="chartBug"></div></div>'
    + '</div>');
  loadDashboard();
}

async function loadDashboard() {
  try {
    const res = await api('/dashboard/stats');
    const d = res.data;

    document.getElementById('statsRow').innerHTML =
      '<div class="stat-card">'
      + '<div class="stat-icon-wrap" style="background:rgba(14,165,233,0.1);color:var(--brand-500)">'
      + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg></div>'
      + '<div class="stat-number">' + d.total_projects + '</div><div class="stat-label">项目总数</div></div>'
      + '<div class="stat-card">'
      + '<div class="stat-icon-wrap" style="background:var(--success-bg);color:var(--success)">'
      + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg></div>'
      + '<div class="stat-number">' + d.total_tasks + '</div><div class="stat-label">任务总数 &middot; ' + d.active_tasks + ' 进行中</div></div>'
      + '<div class="stat-card">'
      + '<div class="stat-icon-wrap" style="background:var(--danger-bg);color:var(--danger)">'
      + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M4.93 4.93l14.14 14.14"/></svg></div>'
      + '<div class="stat-number">' + d.total_bugs + '</div><div class="stat-label">缺陷总数 &middot; ' + d.active_bugs + ' 待处理</div></div>'
      + '<div class="stat-card">'
      + '<div class="stat-icon-wrap" style="background:var(--warning-bg);color:var(--warning)">'
      + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>'
      + '<div class="stat-number">' + (d.my_tasks || 0) + '</div><div class="stat-label">我的待办</div></div>'
      + '<div class="stat-card">'
      + '<div class="stat-icon-wrap" style="background:rgba(139,92,246,0.1);color:#8b5cf6">'
      + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg></div>'
      + '<div class="stat-number">' + d.total_stories + '</div><div class="stat-label">用户需求 &middot; ' + d.active_stories + ' 活跃</div></div>'
      + '<div class="stat-card">'
      + '<div class="stat-icon-wrap" style="background:rgba(14,165,233,0.1);color:var(--brand-500)">'
      + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg></div>'
      + '<div class="stat-number">' + d.total_users + '</div><div class="stat-label">团队成员</div></div>';

    renderProjChart(d.project_progress || []);
    renderWeekChart(d.weekly_completed || []);
    renderBugPie(d.bug_severity || {});
    renderFeed(d.recent_activities || []);
  } catch (e) {
    document.getElementById('statsRow').innerHTML = '<div class="state-error">加载失败: ' + e.message + '</div>';
  }
}

function renderProjChart(data) {
  var el = document.getElementById('chartProj');
  if (!el) return;
  if (!data.length) { el.innerHTML = '<div class="state-empty">暂无数据</div>'; return; }
  var chart = echarts.init(el);
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 10, right: 40, top: 10, bottom: 10 },
    xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
    yAxis: { type: 'category', data: data.map(function(d) { return d.name; }), inverse: true, axisLabel: { fontSize: 11 } },
    series: [{
      type: 'bar',
      data: data.map(function(d) { return {
        value: d.progress,
        itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0,
          [{ offset: 0, color: '#0ea5e9' }, { offset: 1, color: '#38bdf8' }]),
          borderRadius: [0, 4, 4, 0] }
      }; }),
      barWidth: 16,
      label: { show: true, position: 'right', formatter: '{c}%', fontSize: 11 }
    }]
  });
}

function renderWeekChart(data) {
  var el = document.getElementById('chartWeek');
  if (!el) return;
  if (!data.length) { el.innerHTML = '<div class="state-empty">暂无数据</div>'; return; }
  var chart = echarts.init(el);
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['完成任务', '解决缺陷'], bottom: 0, textStyle: { fontSize: 11 } },
    grid: { left: 10, right: 10, top: 10, bottom: 30 },
    xAxis: { type: 'category', data: data.map(function(d) { return d.date; }) },
    yAxis: { type: 'value' },
    series: [
      { name: '完成任务', type: 'line', data: data.map(function(d) { return d.tasks_done; }), smooth: true,
        lineStyle: { color: '#10b981' }, itemStyle: { color: '#10b981' } },
      { name: '解决缺陷', type: 'line', data: data.map(function(d) { return d.bugs_resolved; }), smooth: true,
        lineStyle: { color: '#ef4444' }, itemStyle: { color: '#ef4444' } }
    ]
  });
}

function renderBugPie(data) {
  var el = document.getElementById('chartBug');
  if (!el) return;
  if (!Object.keys(data).length) { el.innerHTML = '<div class="state-empty">暂无数据</div>'; return; }
  var chart = echarts.init(el);
  var colors = { '致命': '#ef4444', '严重': '#f97316', '一般': '#f59e0b', '轻微': '#3b82f6', '建议': '#10b981' };
  chart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie', radius: ['45%', '75%'], center: ['50%', '55%'],
      data: Object.entries(data).map(function(entry) { return { name: entry[0], value: entry[1], itemStyle: { color: colors[entry[0]] || '#0ea5e9' } }; }),
      label: { show: true, formatter: '{b}\n{c}' }
    }]
  });
}

function renderFeed(data) {
  var el = document.getElementById('feedList');
  if (!el) return;
  if (!data.length) { el.innerHTML = '<div class="state-empty">暂无动态</div>'; return; }
  el.innerHTML = data.map(function(a) {
    return '<div class="feed-item"><div class="feed-dot"></div><div><div class="feed-text">'
      + (a.action || '') + ': ' + (a.object_name || '')
      + '</div><div class="feed-time">' + (a.created_at || '') + '</div></div></div>';
  }).join('');
}

// ===== Projects =====
function showProjects() {
  app.innerHTML = pageWrap('项目管理', '项目 / 全部项目',
    '<div class="flex-between mb-16">'
    + '<div class="filter-row" id="projFilters">'
    + '<span class="chip active" data-filter="all" onclick="filterProj(\'all\',this)">全部</span>'
    + '<span class="chip" data-filter="doing" onclick="filterProj(\'doing\',this)">进行中</span>'
    + '<span class="chip" data-filter="waiting" onclick="filterProj(\'waiting\',this)">待启动</span>'
    + '<span class="chip" data-filter="done" onclick="filterProj(\'done\',this)">已完成</span>'
    + '<span class="chip" data-filter="closed" onclick="filterProj(\'closed\',this)">已关闭</span>'
    + '</div>'
    + '<button class="btn btn-primary" onclick="openProjModal()">+ 新建项目</button>'
    + '</div>'
    + '<div id="projList"><div class="state-loading"><div class="spin"></div>加载中...</div></div>');
  loadProjects();
}
window.filterProj = function(status, el) {
  document.querySelectorAll('#projFilters .chip').forEach(function(c) { c.classList.remove('active'); });
  el.classList.add('active');
  loadProjects(status);
};

async function loadProjects(status) {
  status = status || '';
  try {
    var url = '/projects?page_size=100';
    if (status && status !== 'all') url += '&status=' + status;
    var res = await api(url);
    var items = res.items || [];
    if (!items.length) {
      document.getElementById('projList').innerHTML = '<div class="state-empty">暂无项目数据</div>';
      return;
    }
    var sm = { waiting: '待启动', doing: '进行中', suspended: '已暂停', closed: '已关闭', done: '已完成' };
    var sc = { waiting: 'warning', doing: 'info', suspended: 'warning', closed: 'success', done: 'success' };
    document.getElementById('projList').innerHTML = '<div class="tbl-wrap"><table><thead><tr>'
      + '<th>项目名称</th><th>代号</th><th>状态</th><th>进度</th><th>任务(完成/总数)</th><th>日期</th><th>操作</th>'
      + '</tr></thead><tbody>' + items.map(function(p) {
        return '<tr>'
          + '<td style="font-weight:600;cursor:pointer;color:var(--brand-600)">' + p.name + '</td>'
          + '<td style="color:var(--text-muted);font-size:12px">' + (p.code || '') + '</td>'
          + '<td><span class="badge badge-' + (sc[p.status] || 'info') + '">' + (sm[p.status] || p.status) + '</span></td>'
          + '<td><div style="margin-bottom:2px">' + (p.progress || 0) + '%</div><div class="progress-track"><div class="progress-fill" style="width:' + (p.progress || 0) + '%"></div></div></td>'
          + '<td style="font-size:12px">' + (p.task_done || 0) + ' / ' + (p.task_count || 0) + '</td>'
          + '<td style="font-size:12px;color:var(--text-muted)">' + (p.start_date || '-') + ' ~ ' + (p.end_date || '-') + '</td>'
          + '<td><button class="btn btn-ghost btn-xs" onclick="navigate(\'tasks\')">任务列表</button></td>'
          + '</tr>';
      }).join('') + '</tbody></table></div>';
  } catch (e) {
    document.getElementById('projList').innerHTML = '<div class="state-error">加载失败: ' + e.message + '</div>';
  }
}

window.openProjModal = function() {
  modal('新建项目',
    '<div class="form-group"><label class="form-label">项目名称</label><input class="form-input" id="pfName" placeholder="输入项目名称"></div>'
    + '<div class="form-group"><label class="form-label">项目代号</label><input class="form-input" id="pfCode" placeholder="如 SOP-V3"></div>'
    + '<div class="form-group"><label class="form-label">描述</label><textarea class="form-textarea" id="pfDesc"></textarea></div>'
    + '<div class="chart-grid">'
    + '<div class="form-group"><label class="form-label">开始日期</label><input type="date" class="form-input" id="pfStart"></div>'
    + '<div class="form-group"><label class="form-label">结束日期</label><input type="date" class="form-input" id="pfEnd"></div>'
    + '</div>'
    + '<div class="modal-actions"><button class="btn btn-ghost" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="createProj()">创建</button></div>');
};
window.createProj = async function() {
  var d = {
    name: document.getElementById('pfName').value,
    code: document.getElementById('pfCode').value,
    description: document.getElementById('pfDesc').value,
    start_date: document.getElementById('pfStart').value || null,
    end_date: document.getElementById('pfEnd').value || null
  };
  if (!d.name || !d.code) { alert('名称和代号必填'); return; }
  try { await api('/projects', { method: 'POST', body: JSON.stringify(d) }); closeModal(); loadProjects(); }
  catch (e) { alert('创建失败: ' + e.message); }
};

// ===== Tasks =====
function showTasks() {
  app.innerHTML = pageWrap('任务管理', '项目 / 任务列表',
    '<div class="flex-between mb-16">'
    + '<div class="filter-row" id="taskFilters">'
    + '<span class="chip active" data-filter="all" onclick="loadTasks(\'\',this)">全部</span>'
    + '<span class="chip" data-filter="todo" onclick="loadTasks(\'todo\',this)">待办</span>'
    + '<span class="chip" data-filter="doing" onclick="loadTasks(\'doing\',this)">进行中</span>'
    + '<span class="chip" data-filter="done" onclick="loadTasks(\'done\',this)">已完成</span>'
    + '</div>'
    + '<div class="flex-between gap-8">'
    + '<div class="search-box"><svg viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="2" width="16" height="16"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg><input id="taskSrch" placeholder="搜索任务..." onkeyup="searchTasks()"></div>'
    + '<button class="btn btn-primary" onclick="openTaskModal()">+ 新建任务</button>'
    + '</div>'
    + '</div>'
    + '<div id="taskStatusBar" class="task-stat-bar"></div>'
    + '<div id="taskList"><div class="state-loading"><div class="spin"></div>加载中...</div></div>');
  loadTasks();
}

async function loadTasks(status, triggerEl) {
  if (triggerEl) {
    document.querySelectorAll('#taskFilters .chip').forEach(function(c) { c.classList.remove('active'); });
    triggerEl.classList.add('active');
  }
  try {
    var url = '/projects/1/tasks?page_size=200';
    if (status && status !== 'all') url += '&status=' + status;
    var res = await api(url);
    renderTasks(res);
  } catch (e) {
    document.getElementById('taskList').innerHTML = '<div class="state-error">' + e.message + '</div>';
  }
}

function renderTasks(res) {
  var items = res.items || [];
  var counts = res.status_counts || {};
  var sm = { todo: '待办', doing: '进行中', done: '已完成', closed: '已关闭' };
  var icons = { todo: '📋', doing: '🔄', done: '✅', closed: '🔒' };

  document.getElementById('taskStatusBar').innerHTML = Object.entries(sm).map(function(entry) {
    return '<div class="task-stat-item" onclick="loadTasks(\'' + entry[0] + '\',null)">'
      + '<div class="task-stat-count">' + (counts[entry[0]] || 0) + '</div>'
      + '<div class="task-stat-desc">' + entry[1] + '</div></div>';
  }).join('');

  if (!items.length) {
    document.getElementById('taskList').innerHTML = '<div class="state-empty">暂无任务</div>';
    return;
  }
  var pm = { high: '高', medium: '中', low: '低' };
  var sb = { todo: 'warning', doing: 'info', done: 'success', closed: 'success' };
  var st = { todo: '待办', doing: '进行中', done: '已完成', closed: '已关闭' };
  document.getElementById('taskList').innerHTML = '<div class="tbl-wrap"><table><thead><tr>'
    + '<th>任务名称</th><th>优先级</th><th>状态</th><th>负责人</th><th>工时(预估/已耗)</th><th>截止日期</th><th>操作</th>'
    + '</tr></thead><tbody>' + items.map(function(t) {
      var deadlineColor = (t.deadline && t.status !== 'done') ? 'var(--danger)' : 'var(--text-muted)';
      return '<tr>'
        + '<td style="font-weight:500">' + t.name + '</td>'
        + '<td><span class="badge badge-' + (t.priority === 'high' ? 'danger' : t.priority === 'medium' ? 'warning' : 'info') + '">' + (pm[t.priority] || t.priority) + '</span></td>'
        + '<td><span class="badge badge-' + (sb[t.status] || 'info') + '">' + (st[t.status] || t.status) + '</span></td>'
        + '<td style="font-size:13px">' + (t.assignee_name || '<span style="color:var(--text-muted)">待分配</span>') + '</td>'
        + '<td style="font-size:12px">' + (t.estimate || 0) + 'h / ' + (t.consumed || 0) + 'h</td>'
        + '<td style="font-size:12px;color:' + deadlineColor + '">' + (t.deadline || '-') + '</td>'
        + '<td>'
        + (t.status !== 'done' ? '<button class="btn btn-success btn-xs" onclick="updateTaskStatus(' + t.id + ',\'done\')">完成</button> ' : '')
        + '<button class="btn btn-ghost btn-xs" onclick="updateTaskStatus(' + t.id + ',\'' + (t.status === 'todo' ? 'doing' : t.status === 'doing' ? 'done' : 'todo') + '\')">切换</button>'
        + '</td></tr>';
    }).join('') + '</tbody></table></div>';
}

window.updateTaskStatus = async function(id, status) {
  try { await api('/projects/tasks/' + id, { method: 'PUT', body: JSON.stringify({ status: status }) }); loadTasks(); }
  catch (e) { alert(e.message); }
};

window.openTaskModal = async function() {
  var opts = '<option value="">选择项目</option>';
  try { var r = await api('/projects?page_size=100'); opts += (r.items || []).map(function(p) { return '<option value="' + p.id + '">' + p.name + '</option>'; }).join(''); } catch (e) {}
  modal('新建任务',
    '<div class="form-group"><label class="form-label">任务名称</label><input class="form-input" id="tfName" placeholder="输入任务名称"></div>'
    + '<div class="form-group"><label class="form-label">所属项目</label><select class="form-select" id="tfProj">' + opts + '</select></div>'
    + '<div class="chart-grid">'
    + '<div class="form-group"><label class="form-label">优先级</label><select class="form-select" id="tfPrio"><option value="high">高</option><option value="medium" selected>中</option><option value="low">低</option></select></div>'
    + '<div class="form-group"><label class="form-label">预估工时(h)</label><input type="number" class="form-input" id="tfEst" value="8"></div>'
    + '</div>'
    + '<div class="form-group"><label class="form-label">截止日期</label><input type="date" class="form-input" id="tfDead"></div>'
    + '<div class="form-group"><label class="form-label">描述</label><textarea class="form-textarea" id="tfDesc"></textarea></div>'
    + '<div class="modal-actions"><button class="btn btn-ghost" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="createTask()">创建</button></div>');
};
window.createTask = async function() {
  var pid = document.getElementById('tfProj').value;
  if (!pid) { alert('请选择项目'); return; }
  var d = {
    name: document.getElementById('tfName').value,
    project_id: parseInt(pid),
    priority: document.getElementById('tfPrio').value,
    estimate: parseFloat(document.getElementById('tfEst').value) || 0,
    deadline: document.getElementById('tfDead').value || null,
    description: document.getElementById('tfDesc').value || ''
  };
  if (!d.name) { alert('任务名称必填'); return; }
  try { await api('/projects/' + pid + '/tasks', { method: 'POST', body: JSON.stringify(d) }); closeModal(); loadTasks(); }
  catch (e) { alert('创建失败: ' + e.message); }
};

window.searchTasks = function() {
  clearTimeout(window._st);
  window._st = setTimeout(async function() {
    var val = document.getElementById('taskSrch').value.trim();
    if (!val) { loadTasks(); return; }
    try {
      var res = await api('/projects/1/tasks?page_size=200&status=all');
      var filtered = (res.items || []).filter(function(t) { return t.name.indexOf(val) >= 0; });
      renderTasks({ items: filtered, status_counts: res.status_counts });
    } catch (e) {}
  }, 300);
};

// ===== Products =====
function showProducts() {
  app.innerHTML = pageWrap('产品管理', '产品 / 全部产品',
    '<div style="display:flex;justify-content:flex-end;margin-bottom:16px">'
    + '<button class="btn btn-primary" onclick="openProdModal()">+ 新建产品</button></div>'
    + '<div id="prodList"><div class="state-loading"><div class="spin"></div>加载中...</div></div>');
  loadProducts();
}
async function loadProducts() {
  try {
    var res = await api('/products?page_size=100');
    var items = res.items || [];
    if (!items.length) { document.getElementById('prodList').innerHTML = '<div class="state-empty">暂无产品</div>'; return; }
    document.getElementById('prodList').innerHTML = items.map(function(p) {
      return '<div class="card" style="margin-bottom:12px"><div style="display:flex;justify-content:space-between;align-items:center">'
        + '<div><div style="font-weight:700;font-size:15px">' + p.name + '</div>'
        + '<div style="font-size:12px;color:var(--text-muted);margin-top:4px">代号: ' + (p.code || '') + ' &middot; 状态: <span class="badge badge-success">' + (p.status || '正常') + '</span></div></div>'
        + '<button class="btn btn-ghost btn-sm" onclick="navigate(\'tasks\')">查看需求</button></div></div>';
    }).join('');
  } catch (e) {
    document.getElementById('prodList').innerHTML = '<div class="state-error">' + e.message + '</div>';
  }
}
window.openProdModal = function() {
  modal('新建产品',
    '<div class="form-group"><label class="form-label">产品名称</label><input class="form-input" id="pdName"></div>'
    + '<div class="form-group"><label class="form-label">产品代号</label><input class="form-input" id="pdCode"></div>'
    + '<div class="form-group"><label class="form-label">描述</label><textarea class="form-textarea" id="pdDesc"></textarea></div>'
    + '<div class="modal-actions"><button class="btn btn-ghost" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="createProd()">创建</button></div>');
};
window.createProd = async function() {
  var d = { name: document.getElementById('pdName').value, code: document.getElementById('pdCode').value, description: document.getElementById('pdDesc').value };
  if (!d.name || !d.code) { alert('名称和代号必填'); return; }
  await api('/products', { method: 'POST', body: JSON.stringify(d) }); closeModal(); showProducts();
};

// ===== Bugs =====
function showBugs() {
  app.innerHTML = pageWrap('缺陷管理', '测试 / 缺陷列表',
    '<div class="flex-between mb-16">'
    + '<div class="filter-row" id="bugFilters">'
    + '<span class="chip active" onclick="filterBugs(\'\',this)">全部</span>'
    + '<span class="chip" onclick="filterBugs(\'active\',this)">未解决</span>'
    + '<span class="chip" onclick="filterBugs(\'resolved\',this)">已解决</span>'
    + '<span class="chip" onclick="filterBugs(\'closed\',this)">已关闭</span>'
    + '</div>'
    + '<button class="btn btn-primary" onclick="openBugModal()">+ 提交缺陷</button>'
    + '</div>'
    + '<div id="bugList"><div class="state-loading"><div class="spin"></div>加载中...</div></div>');
  loadBugs();
}
async function loadBugs(filter) {
  filter = filter || '';
  try {
    var url = '/bugs?page_size=200';
    if (filter) url += '&status=' + filter;
    var res = await api(url);
    renderBugs(res);
  } catch (e) {
    document.getElementById('bugList').innerHTML = '<div class="state-error">' + e.message + '</div>';
  }
}
window.filterBugs = function(filter, el) {
  document.querySelectorAll('#bugFilters .chip').forEach(function(c) { c.classList.remove('active'); });
  el.classList.add('active');
  loadBugs(filter);
};
function renderBugs(res) {
  var items = res.items || [];
  if (!items.length) { document.getElementById('bugList').innerHTML = '<div class="state-empty">暂无缺陷</div>'; return; }
  var sevMap = { fatal: '致命', serious: '严重', normal: '一般', minor: '轻微' };
  var sevBadge = { fatal: 'danger', serious: 'danger', normal: 'warning', minor: 'info' };
  var stBadge = { active: 'danger', resolved: 'success', closed: 'success' };
  var stText = { active: '未解决', resolved: '已解决', closed: '已关闭' };
  document.getElementById('bugList').innerHTML = '<div class="tbl-wrap"><table><thead><tr>'
    + '<th>缺陷标题</th><th>严重程度</th><th>状态</th><th>负责人</th><th>所属产品</th><th>创建时间</th><th>操作</th>'
    + '</tr></thead><tbody>' + items.map(function(b) {
      return '<tr>'
        + '<td style="font-weight:500">' + b.title + '</td>'
        + '<td><span class="badge badge-' + (sevBadge[b.severity] || 'info') + '">' + (sevMap[b.severity] || b.severity) + '</span></td>'
        + '<td><span class="badge badge-' + (stBadge[b.status] || 'info') + '">' + (stText[b.status] || b.status) + '</span></td>'
        + '<td>' + (b.assignee_name || '<span style="color:var(--text-muted)">未分配</span>') + '</td>'
        + '<td style="font-size:12px">' + (b.product_name || '-') + '</td>'
        + '<td style="font-size:12px;color:var(--text-muted)">' + (b.created_at ? b.created_at.substring(0, 10) : '') + '</td>'
        + '<td><select class="form-select" style="width:auto;padding:4px 8px;font-size:11px" onchange="updateBugStatus(' + b.id + ',this.value)"><option value="">操作</option><option value="resolved">已解决</option><option value="closed">关闭</option></select></td>'
        + '</tr>';
    }).join('') + '</tbody></table></div>';
}
window.updateBugStatus = async function(id, status) {
  if (!status) return;
  await api('/bugs/' + id, { method: 'PUT', body: JSON.stringify({ status: status }) });
  loadBugs();
};
window.openBugModal = async function() {
  var popts = '<option value="">选择产品</option>';
  try { var r = await api('/products?page_size=100'); popts += (r.items || []).map(function(p) { return '<option value="' + p.id + '">' + p.name + '</option>'; }).join(''); } catch (e) {}
  modal('提交缺陷',
    '<div class="form-group"><label class="form-label">缺陷标题</label><input class="form-input" id="bfTitle"></div>'
    + '<div class="form-group"><label class="form-label">所属产品</label><select class="form-select" id="bfProd">' + popts + '</select></div>'
    + '<div class="chart-grid">'
    + '<div class="form-group"><label class="form-label">严重程度</label><select class="form-select" id="bfSev"><option value="fatal">致命</option><option value="serious">严重</option><option value="normal" selected>一般</option><option value="minor">轻微</option></select></div>'
    + '<div class="form-group"><label class="form-label">优先级</label><select class="form-select" id="bfPrio"><option value="5">最高</option><option value="4">高</option><option value="3" selected>中</option><option value="2">低</option><option value="1">最低</option></select></div>'
    + '</div>'
    + '<div class="form-group"><label class="form-label">重现步骤</label><textarea class="form-textarea" id="bfSteps"></textarea></div>'
    + '<div class="form-group"><label class="form-label">描述</label><textarea class="form-textarea" id="bfDesc"></textarea></div>'
    + '<div class="modal-actions"><button class="btn btn-ghost" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="createBug()">提交</button></div>');
};
window.createBug = async function() {
  var d = {
    title: document.getElementById('bfTitle').value,
    product_id: parseInt(document.getElementById('bfProd').value) || null,
    severity: document.getElementById('bfSev').value,
    priority: parseInt(document.getElementById('bfPrio').value),
    steps: document.getElementById('bfSteps').value,
    description: document.getElementById('bfDesc').value
  };
  if (!d.title) { alert('标题必填'); return; }
  await api('/bugs', { method: 'POST', body: JSON.stringify(d) }); closeModal(); loadBugs();
};

// ===== Users =====
function showUsers() {
  app.innerHTML = pageWrap('团队成员', '组织 / 成员列表',
    '<div id="userList"><div class="state-loading"><div class="spin"></div>加载中...</div></div>');
  loadUsers();
}
async function loadUsers() {
  try {
    var res = await api('/users?page_size=100');
    var items = res.items || [];
    var rm = { admin: '管理员', pm: '项目经理', dev: '开发', qa: '测试', po: '产品' };
    if (!items.length) { document.getElementById('userList').innerHTML = '<div class="state-empty">暂无成员</div>'; return; }
    document.getElementById('userList').innerHTML = '<div class="tbl-wrap"><table><thead><tr>'
      + '<th>成员</th><th>账号</th><th>角色</th><th>部门</th><th>邮箱</th>'
      + '</tr></thead><tbody>' + items.map(function(u) {
        return '<tr>'
          + '<td><div style="display:flex;align-items:center;gap:10px">'
          + '<div class="sidebar-avatar" style="width:32px;height:32px;font-size:13px;background:' + (u.avatar_color || 'var(--brand-600)') + '">' + (u.realname ? u.realname[0] : '?') + '</div>'
          + '<span style="font-weight:600">' + u.realname + '</span></div></td>'
          + '<td style="color:var(--text-muted)">' + (u.account || '') + '</td>'
          + '<td><span class="badge badge-info">' + (rm[u.role] || u.role) + '</span></td>'
          + '<td>' + (u.department_name || '-') + '</td>'
          + '<td style="font-size:12px;color:var(--text-muted)">' + (u.email || '-') + '</td>'
          + '</tr>';
      }).join('') + '</tbody></table></div>';
  } catch (e) {
    document.getElementById('userList').innerHTML = '<div class="state-error">' + e.message + '</div>';
  }
}

// ===== Reports =====
function showReports() {
  app.innerHTML = pageWrap('数据报表', '报表 / 数据概览',
    '<div class="chart-grid">'
    + '<div class="card"><div class="card-hdr"><div class="card-title">成员任务统计</div></div><div class="chart-box" id="repTask"></div></div>'
    + '<div class="card"><div class="card-hdr"><div class="card-title">缺陷严重程度</div></div><div class="chart-box" id="repBug"></div></div>'
    + '</div>'
    + '<div id="repLoad" class="state-loading"><div class="spin"></div>加载中...</div>');
  loadReports();
}
async function loadReports() {
  try {
    var results = await Promise.all([api('/users/reports/task-by-user'), api('/dashboard/stats')]);
    document.getElementById('repLoad').innerHTML = '';
    var tasks = results[0].items || [];
    var c1 = echarts.init(document.getElementById('repTask'));
    c1.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['总任务', '已完成'], bottom: 0 },
      grid: { left: 10, right: 10, top: 10, bottom: 30 },
      xAxis: { type: 'category', data: tasks.map(function(t) { return t.name; }), axisLabel: { rotate: 30, fontSize: 10 } },
      yAxis: { type: 'value' },
      series: [
        { name: '总任务', type: 'bar', data: tasks.map(function(t) { return t.total; }), itemStyle: { color: '#0ea5e9' } },
        { name: '已完成', type: 'bar', data: tasks.map(function(t) { return t.done; }), itemStyle: { color: '#10b981' } }
      ]
    });
    var d = results[1].data;
    var sc = { '致命': '#ef4444', '严重': '#f97316', '一般': '#f59e0b', '轻微': '#3b82f6' };
    var c2 = echarts.init(document.getElementById('repBug'));
    c2.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie', radius: ['45%', '75%'], center: ['50%', '55%'],
        data: Object.entries(d.bug_severity).map(function(entry) { return { name: entry[0], value: entry[1], itemStyle: { color: sc[entry[0]] || '#0ea5e9' } }; }),
        label: { formatter: '{b}\n{c}' }
      }]
    });
  } catch (e) {
    document.getElementById('repLoad').innerHTML = '<div class="state-error">' + e.message + '</div>';
  }
}

// ===== Modal =====
function modal(title, body) {
  var overlay = document.createElement('div');
  overlay.className = 'modal-shield';
  overlay.id = 'modalOverlay';
  overlay.innerHTML = '<div class="modal-box"><div class="modal-title">' + title + '</div>' + body + '</div>';
  overlay.onclick = function(e) { if (e.target === overlay) closeModal(); };
  document.body.appendChild(overlay);
}
function closeModal() { var el = document.getElementById('modalOverlay'); if (el) el.remove(); }

// ===== Init =====
function init() {
  initTheme();

  // Nav click handlers
  document.querySelectorAll('.nav-item').forEach(function(item) {
    item.addEventListener('click', function(e) {
      e.preventDefault();
      var page = this.dataset.page;
      if (page) {
        navigate(page);
      }
    });
  });

  // Session restore
  if (restoreSession()) {
    sidebar.style.display = 'flex';
    mainArea.style.marginLeft = 'var(--sidebar-w)';
    updateSidebarUser();
    navigate('dashboard');
  } else {
    showLogin();
  }
}

document.addEventListener('DOMContentLoaded', init);

// ===================================================
// ============= AI 工作台 SPA 内嵌页面 ==============
// ===================================================

// ---- topbar helper ----
function aiTopbar(title, icon) {
  return '<div class="topbar"><div class="topbar-left">'
    + '<button class="menu-btn" onclick="document.getElementById(\'sidebar\').classList.toggle(\'open\')">'
    + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg></button>'
    + '<h1 class="page-title">' + icon + ' ' + title + '</h1></div>'
    + '<div class="topbar-right">'
    + '<button class="theme-switch" onclick="toggleTheme()" id="themeToggle"></button>'
    + '</div></div><div class="page-body">';
}

// ===================== AI 对话 =====================
var aiChatMessages = [];
var aiChatStreaming = false;
var aiChatInterval = null;

function showAIChat() {
  clearAIIntervals();
  app.innerHTML = aiTopbar('AI 智能助手', '🧠')
    + '<style>'
    + '.ai-chat-wrap{display:flex;flex-direction:column;height:calc(100vh - 130px);}'
    + '.ai-chat-topbar{display:flex;align-items:center;gap:12px;padding:12px 0 16px;border-bottom:1px solid var(--border-color);margin-bottom:0}'
    + '.ai-model-badge{font-size:11px;padding:3px 12px;border-radius:20px;background:linear-gradient(135deg,#7c3aed,#a855f7);color:#fff;cursor:pointer;font-weight:600}'
    + '.ai-msgs{flex:1;overflow-y:auto;padding:16px 0;display:flex;flex-direction:column;gap:14px;}'
    + '.ai-msg{display:flex;gap:10px;max-width:80%;animation:fadeUp .3s ease}'
    + '@keyframes fadeUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}'
    + '.ai-msg.user{align-self:flex-end;flex-direction:row-reverse}'
    + '.ai-msg.assistant{align-self:flex-start}'
    + '.ai-avatar{width:32px;height:32px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff}'
    + '.ai-avatar.user{background:var(--primary-color)}'
    + '.ai-avatar.assistant{background:linear-gradient(135deg,#7c3aed,#a855f7)}'
    + '.ai-bubble{padding:11px 16px;border-radius:16px;font-size:14px;line-height:1.65;word-break:break-word;max-width:100%}'
    + '.ai-msg.user .ai-bubble{background:var(--primary-color);color:#fff;border-bottom-right-radius:4px}'
    + '.ai-msg.assistant .ai-bubble{background:var(--card-bg);color:var(--text-color);border:1px solid var(--border-color);border-bottom-left-radius:4px}'
    + '.ai-bubble code{background:rgba(0,0,0,.08);padding:2px 6px;border-radius:4px;font-family:monospace;font-size:13px}'
    + '.ai-bubble pre{background:#1e293b;color:#e2e8f0;padding:12px;border-radius:8px;overflow-x:auto;margin:8px 0;font-size:12px}'
    + '.ai-bubble strong{font-weight:700}'
    + '.ai-msg.user .ai-bubble code{background:rgba(255,255,255,.2)}'
    + '.dot{display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--text-secondary);animation:dotBounce 1.4s infinite;margin:0 2px}'
    + '.dot:nth-child(2){animation-delay:.2s}.dot:nth-child(3){animation-delay:.4s}'
    + '@keyframes dotBounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-6px)}}'
    + '.ai-input-area{padding:12px 0 4px;border-top:1px solid var(--border-color)}'
    + '.ai-input-row{display:flex;gap:10px;align-items:flex-end}'
    + '.ai-textarea{flex:1;padding:10px 16px;border-radius:14px;border:1px solid var(--border-color);background:var(--bg-color);color:var(--text-color);font-size:14px;font-family:inherit;resize:none;outline:none;min-height:44px;max-height:130px;line-height:1.5;transition:border .2s}'
    + '.ai-textarea:focus{border-color:var(--primary-color);box-shadow:0 0 0 3px rgba(14,165,233,.12)}'
    + '.ai-send{width:44px;height:44px;border-radius:14px;border:none;background:linear-gradient(135deg,var(--primary-color),#7c3aed);color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all .2s}'
    + '.ai-send:hover{transform:scale(1.06);box-shadow:0 4px 16px rgba(14,165,233,.35)}'
    + '.ai-send:disabled{opacity:.45;cursor:not-allowed;transform:none}'
    + '.quick-pills{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 4px;}'
    + '.quick-pill{padding:7px 14px;border-radius:20px;border:1px solid var(--border-color);background:var(--card-bg);color:var(--text-color);cursor:pointer;font-size:12px;transition:all .2s}'
    + '.quick-pill:hover{border-color:var(--primary-color);color:var(--primary-color)}'
    + '.ai-welcome{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:200px;text-align:center;gap:10px;margin:auto 0}'
    + '.ai-welcome .wico{width:60px;height:60px;background:linear-gradient(135deg,var(--primary-color),#7c3aed);border-radius:18px;display:flex;align-items:center;justify-content:center;font-size:26px;color:#fff;margin-bottom:4px}'
    + '.ai-key-btn{padding:6px 14px;border-radius:8px;border:1px solid var(--border-color);background:var(--card-bg);color:var(--text-secondary);font-size:12px;cursor:pointer;transition:all .2s}'
    + '.ai-key-btn:hover{border-color:var(--primary-color);color:var(--primary-color)}'
    + '.ai-modal{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center}'
    + '.ai-modal-panel{background:var(--card-bg);border-radius:16px;padding:28px;width:520px;max-width:92vw;max-height:80vh;overflow-y:auto;border:1px solid var(--border-color);box-shadow:0 20px 60px rgba(0,0,0,.2)}'
    + '.key-card{display:flex;align-items:center;gap:12px;padding:11px 14px;border-radius:10px;border:1px solid var(--border-color);cursor:pointer;transition:all .2s;margin-bottom:8px}'
    + '.key-card:hover{border-color:var(--primary-color)}'
    + '.key-card.kactive{border-color:var(--primary-color);background:rgba(14,165,233,.06)}'
    + '.key-radio{width:18px;height:18px;border-radius:50%;border:2px solid var(--border-color);flex-shrink:0;display:flex;align-items:center;justify-content:center}'
    + '.key-card.kactive .key-radio{border-color:var(--primary-color)}'
    + '.key-card.kactive .key-radio::after{content:"";width:9px;height:9px;border-radius:50%;background:var(--primary-color)}'
    + '.key-del{width:26px;height:26px;border-radius:6px;border:none;background:transparent;color:var(--text-secondary);cursor:pointer;font-size:14px}'
    + '.key-del:hover{background:rgba(239,68,68,.1);color:#ef4444}'
    + '.addkey-form{display:flex;flex-direction:column;gap:8px;margin-top:12px;padding-top:12px;border-top:1px solid var(--border-color)}'
    + '.addkey-form input{padding:8px 12px;border:1px solid var(--border-color);border-radius:8px;background:var(--bg-color);color:var(--text-color);font-size:13px;outline:none}'
    + '.addkey-form input:focus{border-color:var(--primary-color)}'
    + '</style>'
    + '<div class="ai-chat-wrap">'
    + '<div class="ai-chat-topbar">'
    + '<span id="aiModelBadge" class="ai-model-badge" onclick="aiOpenKeyModal()" title="切换 API Key">MiniMax M2.7</span>'
    + '<div style="flex:1"></div>'
    + '<button class="ai-key-btn" onclick="aiOpenKeyModal()">⚙️ API Key 管理</button>'
    + '</div>'
    + '<div class="ai-msgs" id="aiMsgs">'
    + '<div class="ai-welcome" id="aiWelcome">'
    + '<div class="wico">🧠</div>'
    + '<h2 style="font-size:20px;font-weight:700">你好，我是 WorkNest AI 助手</h2>'
    + '<p style="color:var(--text-secondary);font-size:14px;max-width:400px">帮你分析项目、解读数据、拆解任务、排查Bug。点击下方快捷提问开始吧 👇</p>'
    + '<div class="quick-pills" id="aiQuickPills">'
    + '<span class="quick-pill" onclick="aiQuickSend(this)" data-p="分析当前项目整体健康状况">📊 项目健康分析</span>'
    + '<span class="quick-pill" onclick="aiQuickSend(this)" data-p="根据平台数据生成本周工作报告">📝 本周工作报告</span>'
    + '<span class="quick-pill" onclick="aiQuickSend(this)" data-p="帮我分析最近常见的Bug类型和修复建议">🐛 Bug 趋势分析</span>'
    + '<span class="quick-pill" onclick="aiQuickSend(this)" data-p="任务延期了怎么办？给出3条应对策略">⚠️ 风险评估建议</span>'
    + '<span class="quick-pill" onclick="aiQuickSend(this)" data-p="如何提升团队开发效率？">🚀 效率提升方案</span>'
    + '</div>'
    + '</div>'
    + '</div>'
    + '<div class="ai-input-area">'
    + '<div class="ai-input-row">'
    + '<textarea class="ai-textarea" id="aiInput" placeholder="输入问题，Enter 发送…" rows="1" onkeydown="aiKeyDown(event)" oninput="this.style.height=\'auto\';this.style.height=this.scrollHeight+\'px\'"></textarea>'
    + '<button class="ai-send" id="aiSendBtn" onclick="aiSend()">'
    + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>'
    + '</button>'
    + '</div>'
    + '</div>'
    + '</div>'
    + '</div>';

  aiChatMessages = [];
  aiChatStreaming = false;
  aiLoadKeys();
}

window.aiKeyDown = function(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); aiSend(); }
};
window.aiQuickSend = function(el) {
  var ta = document.getElementById('aiInput');
  if (ta) { ta.value = el.dataset.p; aiSend(); }
};

window.aiSend = async function() {
  var ta = document.getElementById('aiInput');
  var text = ta ? ta.value.trim() : '';
  if (!text || aiChatStreaming) return;
  var welcome = document.getElementById('aiWelcome');
  if (welcome) welcome.style.display = 'none';
  aiAppendMsg('user', text);
  aiChatMessages.push({ role: 'user', content: text });
  ta.value = ''; ta.style.height = 'auto';
  var aiEl = aiAppendMsg('assistant', '<span class="dot"></span><span class="dot"></span><span class="dot"></span>', true);
  aiChatStreaming = true;
  var btn = document.getElementById('aiSendBtn'); if (btn) btn.disabled = true;
  try {
    var resp = await fetch('/api/ai/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
      body: JSON.stringify({ messages: aiChatMessages.slice(-10), stream: true })
    });
    if (!resp.ok) { var e = await resp.json(); throw new Error(e.detail || '请求失败'); }
    var reader = resp.body.getReader();
    var decoder = new TextDecoder();
    var full = '';
    while (true) {
      var _a = await reader.read(), done = _a.done, value = _a.value;
      if (done) break;
      var chunk = decoder.decode(value, { stream: true });
      chunk.split('\n').forEach(function(line) {
        if (!line.startsWith('data: ')) return;
        var d = line.slice(6);
        if (d === '[DONE]') return;
        try { var p = JSON.parse(d); if (p.token) { full += p.token; aiEl.innerHTML = aiRenderMd(full); var msgs = document.getElementById('aiMsgs'); if (msgs) msgs.scrollTop = msgs.scrollHeight; } } catch(ex) {}
      });
    }
    if (full) aiChatMessages.push({ role: 'assistant', content: full });
    else aiEl.textContent = 'AI 助手暂时无法回应，请稍后再试。';
  } catch(err) {
    aiEl.innerHTML = '<span style="color:#ef4444">⚠️ ' + err.message + '</span>';
  } finally {
    aiChatStreaming = false;
    var btn2 = document.getElementById('aiSendBtn'); if (btn2) btn2.disabled = false;
  }
};

function aiAppendMsg(role, content, isHtml) {
  var msgs = document.getElementById('aiMsgs');
  if (!msgs) return document.createElement('div');
  var div = document.createElement('div');
  div.className = 'ai-msg ' + role;
  var initial = role === 'user' ? (currentUser ? currentUser.realname.charAt(0) : 'U') : 'AI';
  div.innerHTML = '<div class="ai-avatar ' + role + '">' + initial + '</div>'
    + '<div class="ai-bubble" id="aibub' + Date.now() + '">' + (isHtml ? content : aiRenderMd(content)) + '</div>';
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  return div.querySelector('.ai-bubble');
}

function aiRenderMd(text) {
  return text
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/```([\s\S]*?)```/g,'<pre><code>$1</code></pre>')
    .replace(/`([^`]+)`/g,'<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g,'<em>$1</em>')
    .replace(/^### (.+)$/gm,'<h3 style="font-size:14px;font-weight:700;margin:8px 0 4px">$1</h3>')
    .replace(/^## (.+)$/gm,'<h2 style="font-size:15px;font-weight:700;margin:8px 0 4px">$1</h2>')
    .replace(/^# (.+)$/gm,'<h1 style="font-size:16px;font-weight:700;margin:8px 0 4px">$1</h1>')
    .replace(/^\* (.+)$/gm,'<li>$1</li>')
    .replace(/^\d+\. (.+)$/gm,'<li>$1</li>')
    .replace(/\n/g,'<br>');
}

async function aiLoadKeys() {
  try {
    var resp = await fetch('/api/ai/keys', { headers: { Authorization: 'Bearer ' + token } });
    if (!resp.ok) return;
    var data = await resp.json();
    var badge = document.getElementById('aiModelBadge');
    if (badge && data.active_key) badge.textContent = data.active_key.name || 'MiniMax M2.7';
  } catch(e) {}
}

window.aiOpenKeyModal = async function() {
  var data = { keys: [], active_index: 0 };
  try {
    var resp = await fetch('/api/ai/keys', { headers: { Authorization: 'Bearer ' + token } });
    if (resp.ok) data = await resp.json();
  } catch(e) {}

  var panel = document.createElement('div');
  panel.className = 'ai-modal';
  panel.id = 'aiKeyModal';
  panel.onclick = function(e) { if (e.target === panel) panel.remove(); };

  var keyListHtml = (data.keys || []).map(function(k, i) {
    var isActive = i === data.active_index;
    return '<div class="key-card ' + (isActive ? 'kactive' : '') + '" onclick="aiSwitchKey(' + i + ')">'
      + '<div class="key-radio"></div>'
      + '<div style="flex:1;min-width:0"><div style="font-size:14px;font-weight:600">' + k.name + '</div>'
      + '<div style="font-size:11px;color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + k.base_url + ' · ' + k.model + '</div></div>'
      + '<button class="key-del" onclick="event.stopPropagation();aiDelKey(\'' + k.id + '\')" title="删除">✕</button>'
      + '</div>';
  }).join('');

  panel.innerHTML = '<div class="ai-modal-panel">'
    + '<h3 style="font-size:17px;font-weight:700;margin-bottom:18px;display:flex;align-items:center;justify-content:space-between">'
    + '🔑 API Key 管理 <button onclick="document.getElementById(\'aiKeyModal\').remove()" style="width:28px;height:28px;border-radius:8px;border:none;background:var(--border-color);cursor:pointer;font-size:14px">✕</button></h3>'
    + '<div id="akeyList">' + (keyListHtml || '<p style="color:var(--text-secondary);font-size:13px;text-align:center;padding:20px 0">暂无 API Key，请添加</p>') + '</div>'
    + '<button onclick="document.getElementById(\'addKeyFormWrap\').style.display=\'flex\'" style="width:100%;padding:9px;border-radius:10px;border:1px solid var(--border-color);background:var(--bg-color);color:var(--text-color);font-size:13px;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px">+ 添加 API Key</button>'
    + '<div id="addKeyFormWrap" class="addkey-form">'
    + '<input id="aknName" placeholder="名称，如 OpenAI GPT-4o">'
    + '<input id="aknUrl" placeholder="API Base URL，如 https://api.minimax.chat/v1">'
    + '<input id="aknKey" placeholder="API Key">'
    + '<input id="aknModel" placeholder="模型名，如 MiniMax-Text-01">'
    + '<div style="display:flex;gap:8px"><input id="aknTokens" placeholder="max_tokens" value="4096" style="flex:1"><input id="aknTemp" placeholder="temperature" value="0.7" style="flex:1"><input id="aknTopP" placeholder="top_p" value="0.95" style="flex:1"></div>'
    + '<button onclick="aiSaveKey()" style="padding:9px;border-radius:10px;border:none;background:var(--primary-color);color:#fff;font-size:13px;font-weight:600;cursor:pointer">保存</button>'
    + '</div>'
    + '</div>';
  document.body.appendChild(panel);
};

window.aiSwitchKey = async function(idx) {
  try {
    await fetch('/api/ai/keys/switch', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token }, body: JSON.stringify({ index: idx }) });
    var m = document.getElementById('aiKeyModal'); if (m) m.remove();
    aiLoadKeys();
    aiOpenKeyModal();
  } catch(e) {}
};
window.aiDelKey = async function(id) {
  if (!confirm('确认删除这个 API Key？')) return;
  try { await fetch('/api/ai/keys/' + id, { method: 'DELETE', headers: { Authorization: 'Bearer ' + token } }); var m = document.getElementById('aiKeyModal'); if (m) m.remove(); aiOpenKeyModal(); } catch(e) {}
};
window.aiSaveKey = async function() {
  var body = { name: document.getElementById('aknName').value, base_url: document.getElementById('aknUrl').value, api_key: document.getElementById('aknKey').value, model: document.getElementById('aknModel').value, max_tokens: +document.getElementById('aknTokens').value || 4096, temperature: +document.getElementById('aknTemp').value || 0.7, top_p: +document.getElementById('aknTopP').value || 0.95 };
  if (!body.name || !body.api_key || !body.model) { alert('请填写名称、API Key 和模型名'); return; }
  try { await fetch('/api/ai/keys/add', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token }, body: JSON.stringify(body) }); var m = document.getElementById('aiKeyModal'); if (m) m.remove(); aiOpenKeyModal(); aiLoadKeys(); } catch(e) { alert('保存失败: ' + e.message); }
};

// ===================== 数据分析 =====================
var _aiAnalyticsCharts = [];
function showAIAnalytics() {
  clearAIIntervals();
  _aiAnalyticsCharts.forEach(function(c) { try { c.dispose(); } catch(e) {} });
  _aiAnalyticsCharts = [];
  app.innerHTML = aiTopbar('数据分析中心', '📊')
    + '<div style="font-size:12px;color:var(--text-secondary);margin-bottom:14px">'
    + '<span style="background:rgba(34,197,94,.12);color:#16a34a;padding:2px 10px;border-radius:20px;font-weight:600;margin-right:8px">✓ 实时数据</span>'
    + '来源: MySQL · 版本 v3.0</div>'
    + '<style>'
    + '.ana-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px}'
    + '.ana-stat{background:var(--card-bg);border:1px solid var(--border-color);border-radius:14px;padding:18px;transition:all .2s}'
    + '.ana-stat:hover{transform:translateY(-2px);box-shadow:var(--shadow-md)}'
    + '.ana-stat .lbl{font-size:12px;color:var(--text-secondary)}'
    + '.ana-stat .val{font-size:26px;font-weight:700;margin-top:6px}'
    + '.ana-charts{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px}'
    + '.ana-panel{background:var(--card-bg);border:1px solid var(--border-color);border-radius:14px;padding:22px}'
    + '.ana-panel h3{font-size:14px;font-weight:600;margin-bottom:14px}'
    + '.ana-chart-box{height:300px}'
    + '@media(max-width:768px){.ana-stats{grid-template-columns:1fr 1fr}.ana-charts{grid-template-columns:1fr}}'
    + '</style>'
    + '<div class="ana-stats" id="anaStats"><div class="ana-stat"><div class="lbl">加载中...</div><div class="val">--</div></div></div>'
    + '<div class="ana-charts">'
    + '<div class="ana-panel"><h3>📊 任务状态分布</h3><div class="ana-chart-box" id="anaTaskDist"></div></div>'
    + '<div class="ana-panel"><h3>🐛 Bug 严重度分布</h3><div class="ana-chart-box" id="anaBugSev"></div></div>'
    + '<div class="ana-panel"><h3>📈 项目进度</h3><div class="ana-chart-box" id="anaProjBar"></div></div>'
    + '<div class="ana-panel"><h3>📅 近7天完成趋势</h3><div class="ana-chart-box" id="anaWeekly"></div></div>'
    + '</div></div>';

  loadAnalytics();
}

async function loadAnalytics() {
  var statsEl = document.getElementById('anaStats');
  try {
    var [dashResp, insightsResp] = await Promise.all([
      fetch('/api/dashboard/stats', {headers:{'Authorization':'Bearer '+token}}).then(r=>r.json()),
      fetch('/api/ai/insights').then(r=>r.json())
    ]);
    var d = dashResp.data || dashResp;
    var ins = (insightsResp.success ? insightsResp.data : null) || {};

    // Summary cards
    statsEl.innerHTML = [
      {v:d.total_projects||0, l:'项目总数', c:'#6366f1'},
      {v:d.total_tasks||0, l:'任务总数', c:'#0ea5e9', sub:'进行中 '+(d.active_tasks||0)},
      {v:d.total_bugs||0, l:'Bug总数', c:'#f97316', sub:'未解决 '+(d.active_bugs||0)},
      {v:d.total_users||0, l:'团队成员', c:'#10b981'}
    ].map(function(s){return '<div class="ana-stat"><div class="lbl">'+s.lbl+'</div><div class="val" style="color:'+s.c+'">'+s.v+'</div>'+(s.sub?'<div style="font-size:11px;color:var(--text-secondary);margin-top:2px">'+s.sub+'</div>':'')+'</div>';}).join('');

    // Render charts
    setTimeout(function() {
      // Task distribution pie
      var td = d.task_distribution || ins.task_distribution || {};
      var tdData = Object.keys(td).map(function(k){return {name:k,value:td[k]};});
      if (tdData.length === 0) tdData = [{name:'无数据',value:1}];
      var c1 = echarts.init(document.getElementById('anaTaskDist'));
      c1.setOption({tooltip:{trigger:'item'},legend:{bottom:0,textStyle:{color:'#94a3b8',fontSize:10}},series:[{type:'pie',radius:['42%','70%'],center:['50%','44%'],data:tdData,label:{color:'#94a3b8',fontSize:11},itemStyle:{borderColor:'var(--bg-color)',borderWidth:2}}],color:['#0ea5e9','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899']});
      _aiAnalyticsCharts.push(c1);

      // Bug severity bar
      var bs = d.bug_severity || ins.bug_severity_distribution || {};
      var bsKeys = Object.keys(bs), bsVals = Object.values(bs);
      if (bsKeys.length === 0) { bsKeys = ['无数据']; bsVals = [0]; }
      var c2 = echarts.init(document.getElementById('anaBugSev'));
      c2.setOption({tooltip:{trigger:'axis'},grid:{left:10,right:30,top:10,bottom:28},xAxis:{type:'category',data:bsKeys,axisLabel:{color:'#94a3b8',fontSize:10}},yAxis:{type:'value',axisLabel:{color:'#94a3b8',fontSize:10}},series:[{type:'bar',data:bsVals,itemStyle:{borderRadius:[6,6,0,0],color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#f97316'},{offset:1,color:'#fdba74'}])}}]});
      _aiAnalyticsCharts.push(c2);

      // Project progress bar
      var pp = d.project_progress || [];
      var ppNames = pp.map(function(p){return p.name||'?';});
      var ppVals = pp.map(function(p){return p.progress||0;});
      if (ppNames.length === 0) { ppNames = ['暂无项目']; ppVals = [0]; }
      var c3 = echarts.init(document.getElementById('anaProjBar'));
      c3.setOption({tooltip:{trigger:'axis'},grid:{left:80,right:30,top:10,bottom:28},xAxis:{type:'value',max:100,axisLabel:{color:'#94a3b8',fontSize:10,formatter:'{value}%'}},yAxis:{type:'category',data:ppNames.reverse(),axisLabel:{color:'#94a3b8',fontSize:10}},series:[{type:'bar',data:ppVals.reverse(),itemStyle:{borderRadius:[0,6,6,0],color:new echarts.graphic.LinearGradient(0,0,1,0,[{offset:0,color:'#6366f1'},{offset:1,color:'#a5b4fc'}])},label:{show:true,position:'right',color:'#94a3b8',fontSize:10,formatter:'{c}%'}}]});
      _aiAnalyticsCharts.push(c3);

      // Weekly completed line
      var wc = d.weekly_completed || [];
      var wcDates = wc.map(function(w){return (w.date||'').substring(5);});
      var wcTasks = wc.map(function(w){return w.tasks||0;});
      var wcBugs = wc.map(function(w){return w.bugs||0;});
      if (wcDates.length === 0) { wcDates = ['6/22','6/23','6/24','6/25','6/26','6/27','6/28']; wcTasks = [0,0,0,0,0,0,0]; wcBugs = [0,0,0,0,0,0,0]; }
      var c4 = echarts.init(document.getElementById('anaWeekly'));
      c4.setOption({tooltip:{trigger:'axis'},legend:{data:['完成任务','解决Bug'],bottom:0,textStyle:{color:'#94a3b8',fontSize:10}},grid:{left:10,right:20,top:20,bottom:40},xAxis:{type:'category',data:wcDates,axisLabel:{color:'#94a3b8',fontSize:10}},yAxis:{type:'value',axisLabel:{color:'#94a3b8',fontSize:10}},series:[{name:'完成任务',type:'line',data:wcTasks,smooth:true,lineStyle:{color:'#0ea5e9',width:2},itemStyle:{color:'#0ea5e9'},areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(14,165,233,.2)'},{offset:1,color:'rgba(14,165,233,.02)'}])}},{name:'解决Bug',type:'line',data:wcBugs,smooth:true,lineStyle:{color:'#f97316',width:2},itemStyle:{color:'#f97316'},areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(249,115,22,.2)'},{offset:1,color:'rgba(249,115,22,.02)'}])}}]});
      _aiAnalyticsCharts.push(c4);

      window.addEventListener('resize', function() { _aiAnalyticsCharts.forEach(function(c){try{c.resize();}catch(e){}}); });
    }, 80);
  } catch(e) {
    statsEl.innerHTML = '<div class="ana-stat" style="grid-column:1/-1;text-align:center;color:#ef4444">⚠️ 加载失败 — ' + e.message + '<br><small>请检查网络连接并确保已登录</small></div>';
    console.error('Analytics load error:', e);
  }
}

// ===================== AI 预测 =====================
var _aiPredChart = null;
function showAIPrediction() {
  clearAIIntervals();
  if (_aiPredChart) { try { _aiPredChart.dispose(); } catch(e) {} _aiPredChart = null; }
  app.innerHTML = aiTopbar('AI 预测引擎', '🧠')
    + '<style>'
    + '.pred-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}'
    + '.pred-mcard{background:var(--card-bg);border:1px solid var(--border-color);border-radius:12px;padding:16px;text-align:center}'
    + '.pred-mcard .r2{font-size:22px;font-weight:700;color:var(--primary-color)}'
    + '.pred-mcard .mname{font-size:12px;color:var(--text-secondary);margin-top:4px}'
    + '.pred-panels{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:20px}'
    + '.pred-panel{background:var(--card-bg);border:1px solid var(--border-color);border-radius:14px;padding:22px}'
    + '.pred-panel h3{font-size:15px;font-weight:600;margin-bottom:14px;display:flex;align-items:center;gap:8px}'
    + '.pred-form{display:grid;grid-template-columns:1fr 1fr;gap:12px}'
    + '.pred-fg{display:flex;flex-direction:column;gap:4px}'
    + '.pred-fg label{font-size:12px;color:var(--text-secondary);font-weight:500}'
    + '.pred-fg input{padding:8px 12px;border:1px solid var(--border-color);border-radius:8px;background:var(--bg-color);color:var(--text-color);font-size:14px;outline:none;transition:border .2s}'
    + '.pred-fg input:focus{border-color:var(--primary-color)}'
    + '.pred-result{margin-top:16px;padding:18px;background:var(--bg-color);border-radius:12px;border:1px solid var(--border-color);display:none}'
    + '.pred-val{font-size:32px;font-weight:700;color:var(--primary-color)}'
    + '.pred-meta{font-size:12px;color:var(--text-secondary);margin-top:6px;display:flex;gap:18px;flex-wrap:wrap}'
    + '.pred-ai-box{margin-top:12px;padding:12px;border-radius:10px;background:linear-gradient(135deg,rgba(124,58,237,.05),rgba(14,165,233,.05));border:1px solid rgba(14,165,233,.12);font-size:13px;line-height:1.6;display:none}'
    + '.pred-chart-panel{background:var(--card-bg);border:1px solid var(--border-color);border-radius:14px;padding:22px;margin-bottom:4px}'
    + '.pred-chart-box{height:300px}'
    + '@media(max-width:768px){.pred-grid{grid-template-columns:1fr 1fr}.pred-panels{grid-template-columns:1fr}}'
    + '</style>'
    + '<div class="pred-grid" id="predGrid">'
    + '<div class="pred-mcard"><div class="r2">--</div><div class="mname">LinearRegression</div></div>'
    + '<div class="pred-mcard"><div class="r2">--</div><div class="mname">Ridge</div></div>'
    + '<div class="pred-mcard"><div class="r2">--</div><div class="mname">RandomForest</div></div>'
    + '<div class="pred-mcard"><div class="r2">--</div><div class="mname">GradientBoosting</div></div>'
    + '</div>'
    + '<div class="pred-panels">'
    + '<div class="pred-panel"><h3>📚 模型训练</h3>'
    + '<p style="font-size:13px;color:var(--text-secondary);margin-bottom:14px">基于业务数据训练预测模型，数据不足时自动使用示例数据</p>'
    + '<button class="btn btn-primary" onclick="predTrain()">🚀 开始训练</button> <button class="btn btn-ghost" onclick="predLoadInfo()">📋 模型信息</button>'
    + '<div id="predTrainResult" style="margin-top:14px;font-size:13px;color:var(--text-secondary)"></div>'
    + '</div>'
    + '<div class="pred-panel"><h3>🎯 销售预测</h3>'
    + '<div class="pred-form">'
    + '<div class="pred-fg"><label>数量</label><input type="number" id="predQty" value="10" min="1"></div>'
    + '<div class="pred-fg"><label>单价 (¥)</label><input type="number" id="predPrice" value="5999" min="1"></div>'
    + '<div class="pred-fg"><label>折扣 (¥)</label><input type="number" id="predDiscount" value="500" min="0"></div>'
    + '<div class="pred-fg" style="justify-content:flex-end"><button class="btn btn-success" onclick="predRun()" style="width:100%;margin-top:16px">🔮 预测</button></div>'
    + '</div>'
    + '<div class="pred-result" id="predResult">'
    + '<div class="pred-val" id="predVal">--</div>'
    + '<div class="pred-meta"><span id="predMethod"></span><span id="predConf"></span><span id="predModel"></span></div>'
    + '<div class="pred-ai-box" id="predAiBox"><div style="color:#7c3aed;font-weight:600;font-size:12px;margin-bottom:4px">🧠 AI 智能解读</div><div id="predAiText"></div></div>'
    + '</div></div></div>'
    + '<div class="pred-chart-panel">'
    + '<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px"><h3 style="margin:0;font-size:15px;font-weight:600">📈 趋势预测</h3>'
    + '<select id="predDays" style="padding:6px 12px;border:1px solid var(--border-color);border-radius:8px;background:var(--bg-color);color:var(--text-color);font-size:13px"><option value="7">7天</option><option value="30" selected>30天</option><option value="90">90天</option></select>'
    + '<button class="btn btn-primary" onclick="predForecast()">生成预测</button></div>'
    + '<div class="pred-chart-box" id="predChartBox"></div>'
    + '</div></div>';

  predLoadInfo();
  predForecast();
}

window.predLoadInfo = async function() {
  var el = document.getElementById('predTrainResult');
  if (!el) return;
  try {
    var resp = await fetch('/api/ai/model-info');
    var d = await resp.json();
    el.innerHTML = '<div style="padding:10px;background:var(--bg-color);border-radius:8px;border:1px solid var(--border-color)">'
      + '<b>当前模型:</b> ' + d.current_model + '<br><b>训练次数:</b> ' + d.training_count + '<br><b>预测次数:</b> ' + d.prediction_count
      + (d.last_training ? '<br><b>最近训练:</b> R²=' + d.last_training.best_r2 + ' · 模型=' + d.last_training.best_model : '')
      + '</div>';
  } catch(e) { el.textContent = 'API 未连接'; }
};

window.predTrain = async function() {
  var el = document.getElementById('predTrainResult');
  if (!el) return;
  el.innerHTML = '⏳ 训练中…';
  try {
    var resp = await fetch('/api/ai/train', { method: 'POST', headers: {'Content-Type':'application/json'}, body: '[]' });
    var d = await resp.json();
    if (d.error) { el.innerHTML = '❌ ' + d.error; return; }
    el.innerHTML = '<b style="color:#10b981">✅ 训练完成!</b> 最优: <b>' + d.best_model + '</b> (R²=' + d.best_r2 + ')';
    var cards = document.querySelectorAll('#predGrid .pred-mcard');
    ['LinearRegression','Ridge','RandomForest','GradientBoosting'].forEach(function(m, i) {
      var mr = d.model_results && d.model_results[m];
      if (mr && cards[i]) cards[i].innerHTML = '<div class="r2">' + mr.r2_score + '</div><div class="mname">' + m + '</div><div style="font-size:10px;color:var(--text-secondary)">MAE:' + mr.mae + '</div>';
    });
  } catch(e) { el.innerHTML = '❌ 训练失败: ' + e.message; }
};

window.predRun = async function() {
  var qty = +document.getElementById('predQty').value;
  var price = +document.getElementById('predPrice').value;
  var discount = +document.getElementById('predDiscount').value;
  try {
    var resp = await fetch('/api/ai/explain-prediction', {
      method: 'POST', headers: {'Content-Type':'application/json', Authorization: 'Bearer ' + token},
      body: JSON.stringify({ quantity: qty, unit_price: price, discount: discount })
    });
    var d = await resp.json();
    var res = document.getElementById('predResult'); res.style.display = 'block';
    document.getElementById('predVal').textContent = '¥' + (d.prediction || 0).toLocaleString();
    document.getElementById('predMethod').textContent = '方法: ' + (d.method || '-');
    document.getElementById('predConf').textContent = '置信度: ' + Math.round((d.confidence||0.85)*100) + '%';
    document.getElementById('predModel').textContent = '模型: ' + (d.model || '-');
    if (d.ai_explanation) {
      var box = document.getElementById('predAiBox'); box.style.display = 'block';
      document.getElementById('predAiText').textContent = d.ai_explanation;
    }
  } catch(e) { alert('预测失败: ' + e.message); }
};

window.predForecast = async function() {
  var days = (document.getElementById('predDays') || {}).value || 30;
  try {
    var resp = await fetch('/api/ai/forecast?days=' + days + '&generate_demo=true');
    var data = await resp.json();
    setTimeout(function() {
      var el = document.getElementById('predChartBox'); if (!el) return;
      if (_aiPredChart) { try { _aiPredChart.dispose(); } catch(ex) {} }
      _aiPredChart = echarts.init(el);
      _aiPredChart.setOption({
        tooltip:{trigger:'axis'}, grid:{left:56,right:20,top:8,bottom:28},
        xAxis:{type:'category',data:data.map(function(d){return d.date.substring(5);}),axisLabel:{color:'#94a3b8',fontSize:10}},
        yAxis:{type:'value',axisLabel:{color:'#94a3b8',formatter:'¥{value}'}},
        series:[
          {name:'置信区间',type:'line',data:data.map(function(d){return d.upper_bound;}),lineStyle:{opacity:0},symbol:'none',areaStyle:{color:'rgba(14,165,233,.08)'},stack:'ci',silent:true},
          {name:'置信区间',type:'line',data:data.map(function(d){return d.lower_bound;}),lineStyle:{opacity:0},symbol:'none',areaStyle:{color:'rgba(255,255,255,0)'},stack:'ci',silent:true},
          {name:'预测值',type:'line',data:data.map(function(d){return d.predicted_value;}),smooth:true,lineStyle:{color:'#0ea5e9',width:2.5},itemStyle:{color:'#0ea5e9'},areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(14,165,233,.28)'},{offset:1,color:'rgba(14,165,233,.02)'}])}}
        ]
      });
      window.addEventListener('resize', function() { if (_aiPredChart) _aiPredChart.resize(); });
    }, 50);
  } catch(e) { console.error(e); }
};

// ===================== 实时监控 =====================
var _aiRealtimeIntervalId = null;
var _aiRealtimeCharts = [];

function showAIRealtime() {
  clearAIIntervals();
  _aiRealtimeCharts.forEach(function(c) { try { c.dispose(); } catch(e) {} });
  _aiRealtimeCharts = [];
  app.innerHTML = aiTopbar('实时监控', '📡')
    + '<div style="font-size:12px;color:var(--text-secondary);margin-bottom:14px">'
    + '<span class="live-dot" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#10b981;animation:rtPulse 2s infinite;margin-right:6px"></span>'
    + '实时探测 · TCP直连 · 每5秒刷新</div>'
    + '<style>'
    + '.rt-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}'
    + '.rt-metric{background:var(--card-bg);border:1px solid var(--border-color);border-radius:12px;padding:16px;display:flex;align-items:center;gap:12px;transition:all .2s}'
    + '.rt-metric:hover{transform:translateY(-2px);box-shadow:var(--shadow-md)}'
    + '.rt-icon{width:42px;height:42px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}'
    + '.rt-val{font-size:20px;font-weight:700}'
    + '.rt-lbl{font-size:11px;color:var(--text-secondary)}'
    + '.rt-charts{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:18px}'
    + '.rt-panel{background:var(--card-bg);border:1px solid var(--border-color);border-radius:14px;padding:20px}'
    + '.rt-panel h3{font-size:14px;font-weight:600;margin-bottom:12px}'
    + '.rt-chart{height:240px}'
    + '.rt-events{background:var(--card-bg);border:1px solid var(--border-color);border-radius:14px;padding:20px}'
    + '.rt-events h3{font-size:14px;font-weight:600;margin-bottom:12px}'
    + '.rt-event{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--border-color);font-size:13px}'
    + '.rt-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}'
    + '.rt-dot.online{background:#10b981}.rt-dot.offline{background:#ef4444}'
    + '.rt-time{color:var(--text-secondary);font-size:11px;min-width:68px}'
    + '@keyframes rtPulse{0%,100%{opacity:1}50%{opacity:.45}}'
    + '@media(max-width:768px){.rt-strip{grid-template-columns:1fr 1fr}.rt-charts{grid-template-columns:1fr}}'
    + '</style>'
    + '<div class="rt-strip" id="rtMetrics">加载服务状态...</div>'
    + '<div class="rt-charts">'
    + '<div class="rt-panel"><h3>📨 任务/Bug 概览</h3><div class="rt-chart" id="rtTaskBug"></div></div>'
    + '<div class="rt-panel"><h3>🌊 项目健康度</h3><div class="rt-chart" id="rtHealth"></div></div>'
    + '</div>'
    + '<div class="rt-events"><h3><span class="live-dot" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#10b981;animation:rtPulse 2s infinite;margin-right:6px"></span>系统事件</h3><div id="rtEventList">加载中...</div></div>'
    + '</div>';

  loadRealtime();
  _aiRealtimeIntervalId = setInterval(loadRealtime, 5000);
}

var _prevTask = 0, _prevBug = 0;
async function loadRealtime() {
  var metricEl = document.getElementById('rtMetrics');
  var eventEl = document.getElementById('rtEventList');
  try {
    var [pipeResp, dashResp] = await Promise.all([
      fetch('/api/ai/pipeline-status').then(r=>r.json()),
      fetch('/api/dashboard/stats', {headers:{'Authorization':'Bearer '+token}}).then(r=>r.json())
    ]);
    var svc = pipeResp.services || {};
    var d = dashResp.data || dashResp;

    // Service cards
    var services = [
      {key:'kafka',      name:'Kafka',       icon:'📨', color:'#fef3c7', text:'#d97706', port:9092},
      {key:'spark',      name:'Spark',       icon:'✨', color:'#fff7ed', text:'#ea580c', port:7077},
      {key:'flink',      name:'Flink',        icon:'🌊', color:'#ede9fe', text:'#7c3aed', port:6123},
      {key:'mysql',      name:'MySQL',        icon:'🗄️', color:'#fce7f3', text:'#db2777', port:3306},
    ];

    metricEl.innerHTML = services.map(function(serv) {
      var s = svc[serv.key] || {};
      var online = s.status === 'online';
      return '<div class="rt-metric">'
        + '<div class="rt-icon" style="background:'+serv.color+';color:'+serv.text+'">'+serv.icon+'</div>'
        + '<div><div class="rt-val" style="color:'+(online?'#10b981':'#ef4444')+'">'+(online?'在线':'离线')+'</div>'
        + '<div class="rt-lbl">'+serv.name+' · 端口 '+serv.port+'</div>'
        + (online&&s.latency_ms!=null?'<div style="font-size:10px;color:var(--text-secondary);margin-top:2px">延迟 '+s.latency_ms+'ms</div>':'')
        + '</div></div>';
    }).join('');

    // Chart: Task/Bug overview
    setTimeout(function() {
      var ctb = echarts.init(document.getElementById('rtTaskBug'));
      ctb.setOption({tooltip:{trigger:'axis'},legend:{data:['任务','Bug'],bottom:0,textStyle:{color:'#94a3b8',fontSize:10}},xAxis:{type:'category',data:['总数','进行中/未解决','已完成/已解决'],axisLabel:{color:'#94a3b8',fontSize:10}},yAxis:{type:'value',axisLabel:{color:'#94a3b8',fontSize:10}},series:[{name:'任务',type:'bar',data:[d.total_tasks||0,d.active_tasks||0,d.completed_tasks||0],itemStyle:{color:'#0ea5e9',borderRadius:[6,6,0,0]}},{name:'Bug',type:'bar',data:[d.total_bugs||0,d.active_bugs||0,d.resolved_bugs||0],itemStyle:{color:'#f97316',borderRadius:[6,6,0,0]}}]});
      _aiRealtimeCharts.push(ctb);

      // Project health
      var pp = d.project_progress || [];
      var phNames = pp.map(function(p){return (p.name||'?').substring(0,8);});
      var phDone = pp.map(function(p){return p.done||0;});
      var phTotal = pp.map(function(p){return p.total||0;});
      var phRemain = phTotal.map(function(t,i){return Math.max(0,t-(phDone[i]||0));});
      if (phNames.length === 0) { phNames=['暂无']; phDone=[0]; phRemain=[0]; }
      var ch = echarts.init(document.getElementById('rtHealth'));
      ch.setOption({tooltip:{trigger:'axis'},legend:{data:['已完成','剩余'],bottom:0,textStyle:{color:'#94a3b8',fontSize:10}},grid:{left:10,right:20,top:10,bottom:36},xAxis:{type:'category',data:phNames,axisLabel:{color:'#94a3b8',fontSize:9}},yAxis:{type:'value',axisLabel:{color:'#94a3b8',fontSize:10}},series:[{name:'已完成',type:'bar',stack:'total',data:phDone,itemStyle:{color:'#10b981',borderRadius:[0,0,0,0]}},{name:'剩余',type:'bar',stack:'total',data:phRemain,itemStyle:{color:'rgba(148,163,184,.25)',borderRadius:[4,4,0,0]}}]});
      _aiRealtimeCharts.push(ch);

      window.addEventListener('resize', function() { _aiRealtimeCharts.forEach(function(c){try{c.resize();}catch(e){}}); });
    }, 60);

    // Events: detect changes
    var taskDelta = (d.total_tasks||0) - _prevTask;
    var bugDelta = (d.total_bugs||0) - _prevBug;
    _prevTask = d.total_tasks||0;
    _prevBug = d.total_bugs||0;
    var now = new Date();
    var events = [
      {time:now.toLocaleTimeString(), cls:'online', msg:'监控刷新 · '+d.total_tasks+'任务 / '+d.total_bugs+'Bug / '+d.total_projects+'项目'},
    ];
    if (taskDelta !== 0 || bugDelta !== 0) {
      events.unshift({time:now.toLocaleTimeString(), cls:'online', msg:'数据变更检测: 任务'+(taskDelta>=0?'+':'')+taskDelta+' · Bug'+(bugDelta>=0?'+':'')+bugDelta});
    }
    var kafkaS = svc.kafka || {};
    var sparkS = svc.spark || {};
    var flinkS = svc.flink || {};
    if (kafkaS.status !== 'online') events.push({time:now.toLocaleTimeString(), cls:'offline', msg:'⚠️ Kafka 连接异常'});
    if (sparkS.status !== 'online') events.push({time:now.toLocaleTimeString(), cls:'offline', msg:'⚠️ Spark Master 连接异常'});
    if (flinkS.status !== 'online') events.push({time:now.toLocaleTimeString(), cls:'offline', msg:'⚠️ Flink JobManager 连接异常'});
    eventEl.innerHTML = events.map(function(e){return '<div class="rt-event"><span class="rt-dot '+e.cls+'"></span><span class="rt-time">'+e.time+'</span><span>'+e.msg+'</span></div>';}).join('');

  } catch(e) {
    if (metricEl) metricEl.innerHTML = '<div class="rt-metric" style="grid-column:1/-1;color:#ef4444;justify-content:center">⚠️ 监控加载失败 — '+e.message+'</div>';
    if (eventEl) eventEl.innerHTML = '<div style="color:#ef4444;font-size:13px">⚠️ '+e.message+'</div>';
    console.error('Realtime load error:', e);
  }
}

// ===================== 数据管理 =====================
function showAIDatamanage() {
  clearAIIntervals();
  app.innerHTML = aiTopbar('数据管理中心', '🗃️')
    + '<div style="font-size:12px;color:var(--text-secondary);margin-bottom:14px">'
    + '<span style="background:rgba(34,197,94,.12);color:#16a34a;padding:2px 10px;border-radius:20px;font-weight:600;margin-right:8px">✓ 实时数据</span>'
    + '来源: MySQL · 管道直连</div>'
    + '<style>'
    + '.dm-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}'
    + '.dm-stat{background:var(--card-bg);border:1px solid var(--border-color);border-radius:12px;padding:18px;transition:all .2s}'
    + '.dm-stat:hover{transform:translateY(-2px);box-shadow:var(--shadow-md)}'
    + '.dm-stat .lbl{font-size:12px;color:var(--text-secondary)}'
    + '.dm-stat .val{font-size:22px;font-weight:700;margin-top:5px}'
    + '.dm-pipes{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-bottom:20px}'
    + '.dm-pipe{background:var(--card-bg);border:1px solid var(--border-color);border-radius:14px;padding:20px;transition:all .2s}'
    + '.dm-pipe:hover{transform:translateY(-2px);box-shadow:var(--shadow-md)}'
    + '.dm-pipe h4{font-size:14px;font-weight:600;margin-bottom:10px;display:flex;align-items:center;gap:8px}'
    + '.dm-pipe-row{display:flex;justify-content:space-between;padding:6px 0;font-size:12px;border-bottom:1px solid var(--border-color)}'
    + '.dm-pipe-row:last-child{border-bottom:none}'
    + '.dm-pipe-row .k{color:var(--text-secondary)}'
    + '.dm-pipe-row .v{font-weight:600}'
    + '.dm-table-wrap{background:var(--card-bg);border:1px solid var(--border-color);border-radius:14px;overflow:hidden;margin-bottom:4px}'
    + '.dm-table{width:100%;border-collapse:collapse}'
    + '.dm-table th,.dm-table td{padding:10px 14px;text-align:left;font-size:13px;border-bottom:1px solid var(--border-color)}'
    + '.dm-table th{background:var(--bg-color);font-weight:600;color:var(--text-secondary);font-size:11px;text-transform:uppercase;letter-spacing:.5px}'
    + '.dm-table tr:hover td{background:var(--bg-color)}'
    + '.dm-bar{height:6px;border-radius:3px;background:var(--border-color);min-width:80px;overflow:hidden}'
    + '.dm-bar-fill{height:100%;border-radius:3px;transition:width .4s}'
    + '@media(max-width:768px){.dm-stats{grid-template-columns:1fr 1fr}.dm-pipes{grid-template-columns:1fr}}'
    + '</style>'
    + '<div class="dm-stats" id="dmStats">加载中...</div>'
    + '<div class="dm-pipes" id="dmPipes">加载中...</div>'
    + '<div class="dm-table-wrap" id="dmTableWrap" style="display:none"><table class="dm-table"><thead><tr><th>项目名称</th><th>状态</th><th>进度</th><th>已完成</th><th>总任务</th><th>进度条</th></tr></thead><tbody id="dmTbody"></tbody></table></div>'
    + '</div>';

  loadDatamanage();
}

async function loadDatamanage() {
  var statsEl = document.getElementById('dmStats');
  var pipesEl = document.getElementById('dmPipes');
  try {
    var [pipeResp, dashResp] = await Promise.all([
      fetch('/api/ai/pipeline-status').then(r=>r.json()),
      fetch('/api/dashboard/stats', {headers:{'Authorization':'Bearer '+token}}).then(r=>r.json())
    ]);
    var svc = pipeResp.services || {};
    var d = dashResp.data || dashResp;

    // Summary
    statsEl.innerHTML = [
      {v:d.total_projects||0, l:'项目总数', c:'#6366f1'},
      {v:d.total_tasks||0, l:'任务总数', c:'#0ea5e9'},
      {v:d.total_bugs||0, l:'Bug总数', c:'#f97316'},
      {v:d.total_users||0, l:'团队成员', c:'#10b981'}
    ].map(function(s){return '<div class="dm-stat"><div class="lbl">'+s.lbl+'</div><div class="val" style="color:'+s.c+'">'+s.v+'</div></div>';}).join('');

    // Pipeline cards
    var pipes = [
      {key:'kafka',name:'Kafka 消息队列',icon:'📨',color:'#d97706',fields:[{k:'状态',v:function(s){return s.status==='online'?'<span style="color:#10b981">● 在线</span>':'<span style="color:#ef4444">● 离线</span>'}},{k:'端口',v:'9092'},{k:'延迟',v:function(s){return (s.latency_ms!=null?s.latency_ms+'ms':'--')}},{k:'Topics',v:function(s){var t=s.topics;return t?t.join(', '):'--'}}]},
      {key:'spark',name:'Spark 计算引擎',icon:'✨',color:'#ea580c',fields:[{k:'状态',v:function(s){return s.status==='online'?'<span style="color:#10b981">● 在线</span>':'<span style="color:#ef4444">● 离线</span>'}},{k:'端口',v:'7077/8080'},{k:'延迟',v:function(s){return (s.latency_ms!=null?s.latency_ms+'ms':'--')}}]},
      {key:'flink',name:'Flink 流处理',icon:'🌊',color:'#7c3aed',fields:[{k:'状态',v:function(s){return s.status==='online'?'<span style="color:#10b981">● 在线</span>':'<span style="color:#ef4444">● 离线</span>'}},{k:'端口',v:'6123'},{k:'延迟',v:function(s){return (s.latency_ms!=null?s.latency_ms+'ms':'--')}}]},
      {key:'mysql',name:'MySQL 数据库',icon:'🗄️',color:'#db2777',fields:[{k:'状态',v:function(s){return s.status==='online'?'<span style="color:#10b981">● 在线</span>':'<span style="color:#ef4444">● 离线</span>'}},{k:'端口',v:'3306'},{k:'延迟',v:function(s){return (s.latency_ms!=null?s.latency_ms+'ms':'--')}},{k:'数据表',v:function(s){var t=s.tables||{};return Object.keys(t).map(function(k){return k+':'+t[k];}).join(', ') || '--'}}]},
    ];

    pipesEl.innerHTML = pipes.map(function(p){
      var s = svc[p.key] || {};
      return '<div class="dm-pipe"><h4 style="color:'+p.color+'">'+p.icon+' '+p.name+'</h4>'
        + p.fields.map(function(f){return '<div class="dm-pipe-row"><span class="k">'+f.k+'</span><span class="v">'+(typeof f.v==='function'?f.v(s):f.v)+'</span></div>';}).join('')
        + '</div>';
    }).join('');

    // Project table
    var pp = d.project_progress || [];
    if (pp.length > 0) {
      document.getElementById('dmTableWrap').style.display = '';
      document.getElementById('dmTbody').innerHTML = pp.map(function(p){
        var color = p.progress>=80?'#10b981':p.progress>=50?'#f59e0b':p.progress>=20?'#f97316':'#ef4444';
        var statusBadge = p.status==='active'?'<span style="background:rgba(34,197,94,.12);color:#16a34a;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600">活跃</span>':
          p.status==='done'?'<span style="background:rgba(99,102,241,.12);color:#6366f1;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600">已完成</span>':
          '<span style="background:rgba(148,163,184,.12);color:#64748b;padding:2px 8px;border-radius:10px;font-size:11px">'+p.status+'</span>';
        return '<tr><td style="font-weight:600">'+p.name+'</td><td>'+statusBadge+'</td><td style="font-weight:600;color:'+color+'">'+(p.progress||0)+'%</td><td>'+(p.done||0)+'</td><td>'+(p.total||0)+'</td><td><div class="dm-bar"><div class="dm-bar-fill" style="width:'+(p.progress||0)+'%;background:'+color+'"></div></div></td></tr>';
      }).join('');
    }

  } catch(e) {
    if (statsEl) statsEl.innerHTML = '<div class="dm-stat" style="grid-column:1/-1;text-align:center;color:#ef4444">⚠️ 加载失败 — '+e.message+'</div>';
    if (pipesEl) pipesEl.innerHTML = '<div class="dm-pipe" style="grid-column:1/-1;text-align:center;color:#ef4444">⚠️ 管道数据加载失败</div>';
    console.error('Datamanage load error:', e);
  }
}

// ===================== 服务管理 (Launcher) =====================
var _launcherInterval = null;

function showLauncher() {
  clearAIIntervals();
  app.innerHTML = aiTopbar('服务管理', '🚀')
    + '<style>'
    + '.lnc-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px}'
    + '.lnc-card{background:var(--card-bg);border:1px solid var(--border-color);border-radius:14px;padding:20px;transition:all .2s}'
    + '.lnc-card:hover{box-shadow:var(--shadow-md)}'
    + '.lnc-head{display:flex;align-items:center;gap:10px;margin-bottom:12px}'
    + '.lnc-icon{width:42px;height:42px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0}'
    + '.lnc-name{font-size:15px;font-weight:700}'
    + '.lnc-desc{font-size:12px;color:var(--text-secondary)}'
    + '.status-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}'
    + '.status-dot.running{background:#22c55e;box-shadow:0 0 6px rgba(34,197,94,.5)}'
    + '.status-dot.stopped{background:#ef4444}'
    + '.status-dot.unknown{background:#94a3b8}'
    + '.lnc-status-row{display:flex;align-items:center;gap:8px;margin-bottom:14px}'
    + '.lnc-status-txt{font-size:12px;font-weight:500}'
    + '.lnc-btns{display:flex;gap:8px}'
    + '.lnc-btn{padding:6px 14px;border-radius:8px;font-size:12px;font-weight:600;border:none;cursor:pointer;transition:all .2s}'
    + '.lnc-btn.start{background:rgba(34,197,94,.1);color:#16a34a;border:1px solid rgba(34,197,94,.3)}'
    + '.lnc-btn.start:hover{background:#22c55e;color:#fff}'
    + '.lnc-btn.stop{background:rgba(239,68,68,.1);color:#dc2626;border:1px solid rgba(239,68,68,.3)}'
    + '.lnc-btn.stop:hover{background:#ef4444;color:#fff}'
    + '.lnc-all{display:flex;gap:12px;margin-bottom:20px;padding:16px;background:var(--card-bg);border:1px solid var(--border-color);border-radius:14px;align-items:center}'
    + '.lnc-total{flex:1;font-size:14px;color:var(--text-secondary)}'
    + '@media(max-width:768px){.lnc-cards{grid-template-columns:1fr 1fr}}'
    + '</style>'
    + '<div class="lnc-all">'
    + '<div class="lnc-total" id="lncTotal">正在检测服务状态…</div>'
    + '<button class="btn btn-success" style="background:#22c55e;color:#fff" onclick="lncStartAll()">▶ 一键全部启动</button>'
    + '<button class="btn btn-ghost" onclick="lncStopAll()">⏹ 全部停止</button>'
    + '</div>'
    + '<div class="lnc-cards" id="lncCards">加载中…</div>'
    + '</div>';

  lncLoad();
  _launcherInterval = setInterval(lncLoad, 5000);
}

async function lncLoad() {
  try {
    var resp = await fetch('/api/launcher/services', { headers: { Authorization: 'Bearer ' + token } });
    if (!resp.ok) throw new Error('API error ' + resp.status);
    var services = await resp.json();
    var el = document.getElementById('lncCards');
    if (!el) { clearInterval(_launcherInterval); return; }
    var icons = { 'zentao-fastapi':'⚡', 'zentao-mysql':'🗄️', 'zentao-nginx':'🌐', 'zentao-redis':'🔴', 'zentao-postgres':'🐘', 'zookeeper':'🦁', 'kafka':'📨', 'spark-master':'✨', 'flink-jobmanager':'🌊' };
    var colors = { 'zentao-fastapi':'#e0f2fe','zentao-mysql':'#fce7f3','zentao-nginx':'#dcfce7','zentao-redis':'#fee2e2','zentao-postgres':'#dbeafe','zookeeper':'#fef3c7','kafka':'#fdf4ff','spark-master':'#fff7ed','flink-jobmanager':'#ede9fe' };
    var running = services.filter(function(s){return s.status==='running';}).length;
    var total = document.getElementById('lncTotal');
    if (total) total.innerHTML = '<b style="color:#22c55e">'+running+'</b> / '+services.length+' 个服务运行中';
    el.innerHTML = services.map(function(s) {
      var isRun = s.status === 'running';
      return '<div class="lnc-card">'
        + '<div class="lnc-head"><div class="lnc-icon" style="background:'+(colors[s.name]||'#f1f5f9')+'">'+(icons[s.name]||'📦')+'</div>'
        + '<div><div class="lnc-name">'+s.name+'</div><div class="lnc-desc">'+(s.image||'')+'</div></div></div>'
        + '<div class="lnc-status-row"><span class="status-dot '+(isRun?'running':s.status==='stopped'?'stopped':'unknown')+'"></span>'
        + '<span class="lnc-status-txt" style="color:'+(isRun?'#16a34a':s.status==='stopped'?'#dc2626':'#64748b')+'">'+(isRun?'运行中':s.status==='stopped'?'已停止':'未知')+'</span>'
        + (s.uptime ? '<span style="font-size:11px;color:var(--text-secondary);margin-left:auto">'+s.uptime+'</span>' : '')
        + '</div>'
        + '<div class="lnc-btns">'
        + (isRun ? '<button class="lnc-btn stop" onclick="lncAction(\'stop\',\''+s.name+'\')">⏹ 停止</button>' : '<button class="lnc-btn start" onclick="lncAction(\'start\',\''+s.name+'\')">▶ 启动</button>')
        + '<button class="lnc-btn" style="border:1px solid var(--border-color);background:var(--bg-color);color:var(--text-color)" onclick="lncLogs(\''+s.name+'\')">📋 日志</button>'
        + '</div></div>';
    }).join('');
  } catch(e) {
    var el = document.getElementById('lncCards');
    if (el) el.innerHTML = '<div style="padding:20px;color:var(--text-secondary);font-size:13px;grid-column:1/-1">⚠️ 无法获取服务状态 — ' + e.message + '</div>';
  }
}

window.lncAction = async function(action, name) {
  try {
    await fetch('/api/launcher/services/' + name + '/' + action, { method: 'POST', headers: { Authorization: 'Bearer ' + token } });
    setTimeout(lncLoad, 1000);
  } catch(e) { alert(action + ' 失败: ' + e.message); }
};

window.lncStartAll = async function() {
  try { await fetch('/api/launcher/services/start-all', { method: 'POST', headers: { Authorization: 'Bearer ' + token } }); setTimeout(lncLoad, 1500); } catch(e) {}
};
window.lncStopAll = async function() {
  if (!confirm('确认停止所有服务？')) return;
  try { await fetch('/api/launcher/services/stop-all', { method: 'POST', headers: { Authorization: 'Bearer ' + token } }); setTimeout(lncLoad, 1500); } catch(e) {}
};
window.lncLogs = async function(name) {
  try {
    var resp = await fetch('/api/launcher/logs/' + name + '?lines=50', { headers: { Authorization: 'Bearer ' + token } });
    var d = await resp.json();
    showModal('<pre style="font-size:12px;white-space:pre-wrap;max-height:400px;overflow:auto;color:var(--text-color)">' + (d.logs || '暂无日志') + '</pre>', '📋 ' + name + ' 日志');
  } catch(e) { alert('获取日志失败: ' + e.message); }
};

// ===================== 清理 AI 定时器 =====================
function clearAIIntervals() {
  if (_aiRealtimeIntervalId) { clearInterval(_aiRealtimeIntervalId); _aiRealtimeIntervalId = null; }
  if (_launcherInterval) { clearInterval(_launcherInterval); _launcherInterval = null; }
}

