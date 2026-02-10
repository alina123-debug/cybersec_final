/* global Chart */
window.MONITOR = (() => {
  let ws;
  let charts = {};

  // ===== GLOBAL CHART THEME =====
  Chart.defaults.color = "#E6EAF2";
  Chart.defaults.borderColor = "rgba(255,255,255,0.15)";
  Chart.defaults.font.family = "Inter, system-ui, -apple-system, sans-serif";

  function toast(title, body, variant="primary"){
    const area = document.getElementById("toast-area");
    if(!area) return;
    const id = "t" + Math.random().toString(16).slice(2);
    const html = `
      <div class="toast text-bg-${variant} border-0" role="alert" id="${id}" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
          <div class="toast-body">
            <div class="fw-semibold">${title}</div>
            <div class="small">${body}</div>
          </div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
      </div>`;
    area.insertAdjacentHTML("beforeend", html);
    const el = document.getElementById(id);
    const t = new bootstrap.Toast(el, {delay: 3500});
    t.show();
    el.addEventListener("hidden.bs.toast", () => el.remove());
  }

  function connectWS(){
    const proto = (location.protocol === "https:") ? "wss" : "ws";
    ws = new WebSocket(`${proto}://${location.host}/ws/monitor/`);
    const badge = document.getElementById("ws-status");

    ws.onopen = () => { if(badge) badge.textContent = "online"; };
    ws.onclose = () => { if(badge) badge.textContent = "offline"; setTimeout(connectWS, 1200); };
    ws.onerror = () => { if(badge) badge.textContent = "offline"; };

    ws.onmessage = (msg) => {
      try{
        const data = JSON.parse(msg.data);
        if(data.event === "new_case"){
          toast("New case", `${data.severity} • ${data.incident_type}: ${data.title}`, "danger");
          refreshDashboard();
          if(location.pathname.startsWith("/cases/") || location.pathname.startsWith("/alerts/")){
            if(location.pathname.startsWith("/cases/")) loadCases();
            if(location.pathname.startsWith("/alerts/")) loadAlerts();
          }
        }else if(data.event === "new_alert"){
          toast("New alert", `${data.severity} • ${data.incident_type}: ${data.title}`, "info");
          refreshDashboard();
          if(location.pathname.startsWith("/alerts/")) loadAlerts();
        }
      }catch(e){ /* ignore */ }
    };
  }

  async function fetchJSON(url, opts={}){
    const r = await fetch(url, opts);
    if(!r.ok) throw new Error(await r.text());
    return await r.json();
  }

  // ---------- DASHBOARD ----------
  async function refreshDashboard(){
    if(!document.getElementById("timelineChart")) return;
    const data = await fetchJSON("/api/dashboard/");

    document.getElementById("totalAlerts").textContent = data.total_alerts_today;
    document.getElementById("lastScan").textContent = `${data.last_scan_seconds_ago}s ago`;
    document.getElementById("pCritical").textContent = `${data.severity_percent.CRITICAL}%`;
    document.getElementById("pHigh").textContent = `${data.severity_percent.HIGH}%`;
    document.getElementById("pMedium").textContent = `${data.severity_percent.MEDIUM}%`;
    document.getElementById("pLow").textContent = `${data.severity_percent.LOW}%`;

    // Timeline chart
    const hours = data.timeline_hourly.map(x => x.hour);
    const cases = data.timeline_hourly.map(x => x.cases);
    if(!charts.timeline){
      charts.timeline = new Chart(document.getElementById("timelineChart"), {
        type: "line",
        data: { labels: hours, datasets: [{label:"Cases", data: cases, tension:.35}]},
        options: {
          interaction: {mode: "index", intersect: false},
          plugins: { legend: {display:false} },
          scales: {
            x: {title:{display:true, text:"Hour"}, ticks:{color:"#E6EAF2"}},
            y: {beginAtZero:true, ticks:{color:"#E6EAF2"}}
          }
        }
      });
    } else {
      charts.timeline.data.labels = hours;
      charts.timeline.data.datasets[0].data = cases;
      charts.timeline.update();
    }

    // Severity donut
    const sevLabels = ["CRITICAL","HIGH","MEDIUM","LOW"];
    const sevVals = sevLabels.map(k => data.severity_percent[k]);
    if(!charts.severity){
      charts.severity = new Chart(document.getElementById("severityChart"), {
        type:"doughnut",
        data:{
          labels: sevLabels,
          datasets:[{ data: sevVals, borderWidth: 1 }]
        },
        options:{
          responsive:true,
          cutout:"60%",
          plugins:{
            legend:{
              position:"bottom",
              labels:{
                color:"#FFFFFF",
                boxWidth:14,
                padding:16,
                font:{ size:12, weight:"600" }
              }
            },
            tooltip:{
              titleColor:"#FFFFFF",
              bodyColor:"#FFFFFF",
              backgroundColor:"rgba(10,14,24,0.95)",
              borderColor:"rgba(255,255,255,0.15)",
              borderWidth:1
            }
          }
        }
      });
    } else {
      charts.severity.data.datasets[0].data = sevVals;
      charts.severity.update();
    }

    // Incidents bar (click label => filter cases)
    const incLabels = data.incidents_today.map(x => x.incident_type);
    const incVals = data.incidents_today.map(x => x.count);
    if(!charts.incidents){
      charts.incidents = new Chart(document.getElementById("incidentsChart"), {
        type:"bar",
        data:{ labels: incLabels, datasets:[{label:"Count", data: incVals}]},
        options:{
          plugins:{legend:{display:false}},
          onClick: (_evt, els) => {
            if(!els.length) return;
            const idx = els[0].index;
            const t = incLabels[idx];
            window.location.href = `/cases/?incident_type=${encodeURIComponent(t)}&today=1`;
          }
        }
      });
    } else {
      charts.incidents.data.labels = incLabels;
      charts.incidents.data.datasets[0].data = incVals;
      charts.incidents.update();
    }

    // Threat map scatter
    const pts = data.threat_map_points.map(p => ({x:p.x, y:p.y}));
    if(!charts.threat){
      charts.threat = new Chart(document.getElementById("threatChart"), {
        type:"scatter",
        data:{ datasets:[{label:"Signals", data: pts}]},
        options:{
          scales:{
            x:{title:{display:true,text:"Origin zone"}, ticks:{color:"#E6EAF2"}},
            y:{title:{display:true,text:"Target cluster"}, ticks:{color:"#E6EAF2"}}
          }
        }
      });
    } else {
      charts.threat.data.datasets[0].data = pts;
      charts.threat.update();
    }
  }

  function initDashboard(){
    connectWS();
    refreshDashboard();
    setInterval(refreshDashboard, 5000);
  }

  // ---------- ALERTS ----------
  function readFormParams(formId){
    const form = document.getElementById(formId);
    const params = new URLSearchParams(new FormData(form));
    for (const [k,v] of [...params.entries()]) if(!v) params.delete(k);
    return params;
  }

  async function loadAlerts(){
    const tbody = document.getElementById("alertsTbody");
    if(!tbody) return;
    const params = readFormParams("alertFilterForm");
    const url = "/api/alerts/?" + params.toString();
    const data = await fetchJSON(url);
    const rows = data.map(a => `
      <tr>
        <td>${a.id}</td>
        <td>${new Date(a.created_at).toLocaleTimeString()}</td>
        <td>${a.severity}</td>
        <td>${a.incident_type}</td>
        <td>${a.title}</td>
      </tr>
    `).join("");
    tbody.innerHTML = rows || `<tr><td colspan="5" class="text-secondary">No alerts</td></tr>`;
  }

  function initAlertsPage(){
    connectWS();
    const f = document.getElementById("alertFilterForm");
    if(f) f.addEventListener("submit", (e) => {e.preventDefault(); loadAlerts();});
    loadAlerts();
  }

  // ---------- CASES ----------
  async function loadCases(){
    const tbody = document.getElementById("casesTbody");
    if(!tbody) return;
    const params = readFormParams("caseFilterForm");
    const qs = new URLSearchParams(location.search);
    for(const [k,v] of qs.entries()){
      if(!params.has(k) && v) params.set(k,v);
    }
    const url = "/api/cases/?" + params.toString();
    const data = await fetchJSON(url);
    const rows = data.map(c => `
      <tr>
        <td><a class="link-light" href="/cases/${c.id}/">CASE-${c.id}</a></td>
        <td>${new Date(c.created_at).toLocaleTimeString()}</td>
        <td>${c.severity}</td>
        <td>${c.incident_type}</td>
        <td>${c.title}</td>
        <td>${c.status}</td>
        <td>${c.verdict}</td>
      </tr>
    `).join("");
    tbody.innerHTML = rows || `<tr><td colspan="7" class="text-secondary">No cases</td></tr>`;
  }

  function initCasesPage(){
    connectWS();
    const f = document.getElementById("caseFilterForm");
    if(f) f.addEventListener("submit", (e) => {e.preventDefault(); loadCases();});
    loadCases();
  }

  // ---------- CASE DETAIL ----------
  function initCaseDetail(_caseId){
    connectWS();
  }

  async function saveCase(caseId){
    const payload = {
      title: document.getElementById("caseTitle").value,
      description: document.getElementById("caseDesc").value,
      analyst_name: document.getElementById("analystName").value,
      analyst_group: document.getElementById("analystGroup").value,
      status: document.getElementById("caseStatus").value,
      verdict: document.getElementById("caseVerdict").value,
    };
    await fetchJSON(`/api/cases/${caseId}/`, {
      method:"PATCH",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });
    toast("Saved", `CASE-${caseId} updated`, "success");
  }

  async function toggleTask(caseId, taskId){
    await fetchJSON(`/api/cases/${caseId}/tasks/${taskId}/toggle/`, {method:"POST"});
    location.reload();
  }

  async function addTask(caseId){
    const title = document.getElementById("newTaskTitle").value.trim();
    if(!title) return;
    await fetchJSON(`/api/cases/${caseId}/tasks/add/`, {
      method:"POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({title})
    });
    location.reload();
  }

  async function dispatchCase(caseId){
    const channel = document.getElementById("dispatchChannel").value;
    const sel = document.getElementById("dispatchRecipients");
    const recipients = [...sel.selectedOptions].map(o => o.value);
    await fetchJSON(`/api/cases/${caseId}/dispatch/`, {
      method:"POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({channel, recipients})
    });
    toast("Dispatched", `CASE-${caseId} sent via ${channel}`, "success");
  }

  return {
    initDashboard,
    initAlertsPage,
    initCasesPage,
    initCaseDetail,
    refreshDashboard,
    loadAlerts,
    loadCases,
    saveCase,
    toggleTask,
    addTask,
    dispatchCase,
  };
})();
