/**
 * pesz_ara_ ports scanner Web - Frontend Engine
 * File: index.js
 * Description: Client-side orchestrator for batch scanning, logging, UI rendering, and history.
 */

document.addEventListener('DOMContentLoaded', () => {
  // --- UI Elements ---
  const apiStatusDot = document.getElementById('api-status-dot');
  const apiStatusText = document.getElementById('api-status-text');
  
  const targetInput = document.getElementById('target-input');
  const presetCommon = document.getElementById('preset-common');
  const presetWeb = document.getElementById('preset-web');
  const presetDatabase = document.getElementById('preset-database');
  const presetCustom = document.getElementById('preset-custom');
  const customRangeWrapper = document.getElementById('custom-range-wrapper');
  const startPortInput = document.getElementById('start-port');
  const endPortInput = document.getElementById('end-port');
  
  const timeoutSlider = document.getElementById('timeout-slider');
  const timeoutVal = document.getElementById('timeout-val');
  const batchSlider = document.getElementById('batch-slider');
  const batchVal = document.getElementById('batch-val');
  
  const btnStartScan = document.getElementById('btn-start-scan');
  const btnCancelScan = document.getElementById('btn-cancel-scan');
  
  const statResolvedIp = document.getElementById('stat-resolved-ip');
  const statOpenPorts = document.getElementById('stat-open-ports');
  const statScannedPorts = document.getElementById('stat-scanned-ports');
  const statElapsedTime = document.getElementById('stat-elapsed-time');
  
  const progressIndicator = document.getElementById('progress-indicator');
  const progressPercentageText = document.getElementById('progress-percentage-text');
  
  const terminalConsole = document.getElementById('terminal-console-output');
  const btnClearTerminal = document.getElementById('btn-clear-terminal');
  
  const tableSearchInput = document.getElementById('table-search-input');
  const tableStatusFilter = document.getElementById('table-status-filter');
  const resultsTableBody = document.getElementById('results-table-body');
  const btnClearHistory = document.getElementById('btn-clear-history');
  const historyListElement = document.getElementById('history-list-element');
  
  const btnExportCsv = document.getElementById('btn-export-csv');
  const btnExportJson = document.getElementById('btn-export-json');
  
  const thPort = document.getElementById('th-port');

  // --- State Variables ---
  let activeProfile = 'common';
  let isScanning = false;
  let scanCancelled = false;
  let scanResults = []; // Stores all port results from the current scan
  let scanStartTime = null;
  let timerInterval = null;
  let tableSortAscending = true;

  // Port presets definitions
  const PORT_PRESETS = {
    common: [20, 21, 22, 23, 25, 53, 80, 110, 115, 123, 143, 161, 443, 445, 1433, 3306, 3389, 5432, 6379, 8080, 8443],
    web: [80, 443, 8080, 8081, 8443, 3000, 5000, 8000],
    db: [1433, 3306, 5432, 6379, 27017, 1521, 9200]
  };

  // Determine API base URL (relative for Vercel, fallback to localhost for development)
  const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? '' 
    : '';

  // --- Initializers & Event Listeners ---
  initSliders();
  initProfilePresets();
  checkApiStatus();
  loadHistory();

  // Polling API status every 30 seconds
  setInterval(checkApiStatus, 30000);

  // Bind Actions
  btnStartScan.addEventListener('click', startScan);
  btnCancelScan.addEventListener('click', cancelScan);
  btnClearTerminal.addEventListener('click', clearTerminal);
  btnClearHistory.addEventListener('click', clearHistory);
  tableSearchInput.addEventListener('input', filterTable);
  tableStatusFilter.addEventListener('change', filterTable);
  btnExportCsv.addEventListener('click', exportCSV);
  btnExportJson.addEventListener('click', exportJSON);
  thPort.addEventListener('click', toggleSortPorts);

  // --- Helper Functions ---
  
  function getTimestamp() {
    const now = new Date();
    return now.toISOString().split('T')[1].slice(0, 8);
  }

  function addLog(message, type = 'system') {
    const line = document.createElement('div');
    line.className = `terminal-line ${type}-msg`;
    line.innerHTML = `<span style="color: var(--text-muted)">[${getTimestamp()}]</span> ${message}`;
    terminalConsole.appendChild(line);
    terminalConsole.scrollTop = terminalConsole.scrollHeight;
  }

  function clearTerminal() {
    terminalConsole.innerHTML = '<div class="terminal-line system-msg">> Console cleared. Ready.</div>';
  }

  function initSliders() {
    timeoutSlider.addEventListener('input', (e) => {
      timeoutVal.textContent = `${e.target.value}s`;
    });
    batchSlider.addEventListener('input', (e) => {
      batchVal.textContent = e.target.value;
    });
  }

  function initProfilePresets() {
    const buttons = [presetCommon, presetWeb, presetDatabase, presetCustom];
    
    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        buttons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        activeProfile = btn.dataset.profile;
        
        if (activeProfile === 'custom') {
          customRangeWrapper.classList.remove('hidden');
        } else {
          customRangeWrapper.classList.add('hidden');
        }
      });
    });
  }

  // Check backend serverless API status
  async function checkApiStatus() {
    apiStatusDot.className = 'status-indicator-dot loading';
    apiStatusText.textContent = 'CHECKING API STATUS...';
    
    try {
      const response = await fetch(`${API_BASE}/api/status`);
      if (response.ok) {
        const data = await response.json();
        apiStatusDot.className = 'status-indicator-dot online';
        apiStatusText.textContent = `API ONLINE | ${data.version || 'v1'}`;
      } else {
        throw new Error('API returned error response');
      }
    } catch (error) {
      console.warn("API status check failed:", error);
      apiStatusDot.className = 'status-indicator-dot offline';
      apiStatusText.textContent = 'API OFFLINE / DISCONNECTED';
    }
  }

  // --- Scan Orchestration ---
  
  async function startScan() {
    if (isScanning) return;
    
    const target = targetInput.value.trim();
    if (!target) {
      alert("Please specify a target hostname or IP address.");
      targetInput.focus();
      return;
    }

    // Resolve port list based on selected profile
    let ports = [];
    if (activeProfile === 'custom') {
      const startPort = parseInt(startPortInput.value);
      const endPort = parseInt(endPortInput.value);
      
      if (isNaN(startPort) || isNaN(endPort) || startPort < 1 || endPort > 65535 || startPort > endPort) {
        alert("Please enter a valid port range (1 - 65535, start port <= end port).");
        return;
      }
      
      const count = endPort - startPort + 1;
      if (count > 1000) {
        const proceed = confirm(`You are attempting to scan ${count} ports. Scanning large ranges on serverless architectures can trigger rate limits or take longer. We recommend scanning under 1000 ports at a time. Do you want to proceed?`);
        if (!proceed) return;
      }
      
      for (let p = startPort; p <= endPort; p++) {
        ports.push(p);
      }
    } else {
      ports = [...PORT_PRESETS[activeProfile]];
    }

    // Initialize UI states
    isScanning = true;
    scanCancelled = false;
    scanResults = [];
    
    btnStartScan.disabled = true;
    btnCancelScan.disabled = false;
    targetInput.disabled = true;
    presetCommon.disabled = true;
    presetWeb.disabled = true;
    presetDatabase.disabled = true;
    presetCustom.disabled = true;
    startPortInput.disabled = true;
    endPortInput.disabled = true;
    timeoutSlider.disabled = true;
    batchSlider.disabled = true;
    
    statResolvedIp.textContent = "Resolving...";
    statOpenPorts.textContent = "0";
    statScannedPorts.textContent = `0 / ${ports.length}`;
    statElapsedTime.textContent = "0.0s";
    
    progressIndicator.style.width = '0%';
    progressPercentageText.textContent = '0%';
    
    clearTableBody();
    clearTerminal();
    
    addLog(`Initializing scan request against: [${target}]`, 'system');
    addLog(`Configured ports: ${ports.length} | Profile: ${activeProfile.toUpperCase()}`, 'system');
    
    // Start timing
    scanStartTime = Date.now();
    timerInterval = setInterval(() => {
      const elapsed = ((Date.now() - scanStartTime) / 1000).toFixed(1);
      statElapsedTime.textContent = `${elapsed}s`;
    }, 100);

    // Batch settings
    const batchSize = parseInt(batchSlider.value);
    const timeout = parseFloat(timeoutSlider.value);
    
    // Execute scanning in batches
    try {
      await runBatchScheduler(target, ports, batchSize, timeout);
    } catch (err) {
      addLog(`Fatal Error: ${err.message}`, 'warning');
    } finally {
      finishScan(target, ports.length);
    }
  }

  function cancelScan() {
    if (!isScanning || scanCancelled) return;
    scanCancelled = true;
    addLog("Termination signal sent. Wrapping up active batches...", "warning");
    btnCancelScan.disabled = true;
  }

  function finishScan(target, totalPorts) {
    isScanning = false;
    clearInterval(timerInterval);
    
    btnStartScan.disabled = false;
    btnCancelScan.disabled = true;
    targetInput.disabled = false;
    presetCommon.disabled = false;
    presetWeb.disabled = false;
    presetDatabase.disabled = false;
    presetCustom.disabled = false;
    startPortInput.disabled = false;
    endPortInput.disabled = false;
    timeoutSlider.disabled = false;
    batchSlider.disabled = false;
    
    const finalElapsed = ((Date.now() - scanStartTime) / 1000).toFixed(2);
    statElapsedTime.textContent = `${finalElapsed}s`;
    
    const openCount = scanResults.filter(r => r.status === 'Open').length;
    statOpenPorts.textContent = openCount;

    if (scanCancelled) {
      addLog(`Scan aborted by user. Duration: ${finalElapsed}s. Discovered ${openCount} open ports.`, 'warning');
    } else {
      addLog(`Scan completed successfully in ${finalElapsed}s! Found ${openCount} open ports.`, 'finished');
      // Save to local storage history
      saveToHistory(target, totalPorts, openCount);
      loadHistory();
    }
  }

  // Handles sequential calling of Vercel serverless API in batches
  async function runBatchScheduler(target, ports, batchSize, timeout) {
    const totalPorts = ports.length;
    let scannedCount = 0;
    
    // Split port array into batches
    const batches = [];
    for (let i = 0; i < ports.length; i += batchSize) {
      batches.push(ports.slice(i, i + batchSize));
    }
    
    addLog(`Total Batches to scan: ${batches.length} (Batch Size: ${batchSize})`, 'system');
    
    for (let index = 0; index < batches.length; index++) {
      if (scanCancelled) break;
      
      const batchPorts = batches[index];
      addLog(`Scanning Batch ${index + 1}/${batches.length} (Ports: ${batchPorts[0]} - ${batchPorts[batchPorts.length - 1]})...`, 'system');
      
      try {
        const response = await fetch(`${API_BASE}/api/scan`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ target, ports: batchPorts, timeout })
        });
        
        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.error || `HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update resolved IP
        if (data.target_ip) {
          statResolvedIp.textContent = data.target_ip;
        }

        // Process batch results
        data.results.forEach(result => {
          scanResults.push(result);
          
          if (result.status === 'Open') {
            addLog(`DISCOVERY: Port ${result.port} is OPEN (${result.service}) | Banner: ${result.banner || 'None'}`, 'discovery');
          } else {
            // Log closed ports to terminal in a muted fashion
            addLog(`Port ${result.port} is Closed`, 'closed');
          }
        });
        
        // Render updated table & progress
        scannedCount += batchPorts.length;
        statScannedPorts.textContent = `${scannedCount} / ${totalPorts}`;
        const pct = Math.min(Math.round((scannedCount / totalPorts) * 100), 100);
        progressIndicator.style.width = `${pct}%`;
        progressPercentageText.textContent = `${pct}%`;
        
        // Update Open ports telemetry
        const openCount = scanResults.filter(r => r.status === 'Open').length;
        statOpenPorts.textContent = openCount;

        renderResultsTable();
        
      } catch (err) {
        addLog(`Batch ${index + 1} failed: ${err.message}`, 'warning');
      }
      
      // Small pause between batches to prevent overwhelming the serverless rate limiter
      await new Promise(r => setTimeout(r, 100));
    }
  }

  // --- Table Rendering, Filtering & Sorting ---

  function clearTableBody() {
    resultsTableBody.innerHTML = `
      <tr>
        <td colspan="5" class="table-empty">No scanned ports to display. Start scanning to capture active socket listeners.</td>
      </tr>
    `;
  }

  function renderResultsTable() {
    const searchVal = tableSearchInput.value.toLowerCase();
    const statusVal = tableStatusFilter.value;
    
    // Sort array copies
    let sortedList = [...scanResults];
    sortedList.sort((a, b) => {
      return tableSortAscending ? a.port - b.port : b.port - a.port;
    });

    // Filter list
    const filteredList = sortedList.filter(item => {
      const matchesSearch = item.port.toString().includes(searchVal) || 
                            item.service.toLowerCase().includes(searchVal) || 
                            item.banner.toLowerCase().includes(searchVal);
                            
      const matchesStatus = statusVal === 'all' || 
                            (statusVal === 'open' && item.status === 'Open') ||
                            (statusVal === 'closed' && item.status === 'Closed');
                            
      return matchesSearch && matchesStatus;
    });

    if (filteredList.length === 0) {
      resultsTableBody.innerHTML = `
        <tr>
          <td colspan="5" class="table-empty">No ports match the current filter criteria.</td>
        </tr>
      `;
      return;
    }

    resultsTableBody.innerHTML = filteredList.map(item => {
      const isStatusOpen = item.status === 'Open';
      const statusBadge = `<span class="badge-status ${isStatusOpen ? 'open' : 'closed'}">${item.status}</span>`;
      const bannerClass = isStatusOpen && item.banner && !item.banner.startsWith("No banner") ? 'active-banner' : '';
      
      return `
        <tr>
          <td>${item.port}</td>
          <td>TCP</td>
          <td>${item.service}</td>
          <td>${statusBadge}</td>
          <td class="banner-cell ${bannerClass}" title="${escapeHtml(item.banner)}">${escapeHtml(item.banner || '—')}</td>
        </tr>
      `;
    }).join('');
  }

  function filterTable() {
    renderResultsTable();
  }

  function toggleSortPorts() {
    tableSortAscending = !tableSortAscending;
    thPort.querySelector('.sort-icon').innerHTML = tableSortAscending ? '&#9652;' : '&#9662;';
    renderResultsTable();
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // --- Local Storage History ---
  
  function saveToHistory(target, totalPorts, openPorts) {
    const history = JSON.parse(localStorage.getItem('pesz_ara_history') || '[]');
    
    // Add new scan entry
    const entry = {
      id: Date.now(),
      target: target,
      total: totalPorts,
      open: openPorts,
      timestamp: new Date().toLocaleString()
    };
    
    // Prepend to list and keep only top 10
    history.unshift(entry);
    localStorage.setItem('pesz_ara_history', JSON.stringify(history.slice(0, 10)));
  }

  function loadHistory() {
    const history = JSON.parse(localStorage.getItem('pesz_ara_history') || '[]');
    
    if (history.length === 0) {
      historyListElement.innerHTML = '<li class="history-empty">No scanned targets logged in local history.</li>';
      return;
    }
    
    historyListElement.innerHTML = history.map(item => {
      return `
        <li class="history-item" data-target="${escapeHtml(item.target)}">
          <div class="history-host">${escapeHtml(item.target)}</div>
          <div class="history-meta">
            <span class="history-badge">${item.open} Open</span>
            <span class="history-time">${item.timestamp.split(',')[0]}</span>
          </div>
        </li>
      `;
    }).join('');

    // Bind click events to load target into input
    document.querySelectorAll('.history-item').forEach(el => {
      el.addEventListener('click', () => {
        targetInput.value = el.dataset.target;
        addLog(`Loaded target from history: ${el.dataset.target}`, 'system');
      });
    });
  }

  function clearHistory() {
    if (confirm("Are you sure you want to delete all saved scan history?")) {
      localStorage.removeItem('pesz_ara_history');
      loadHistory();
    }
  }

  // --- Exporter Utilities ---

  function exportCSV() {
    if (scanResults.length === 0) {
      alert("No data available to export. Run a scan first.");
      return;
    }
    
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Port,Protocol,Service,Status,Service Banner\n";
    
    scanResults.forEach(item => {
      const bannerClean = (item.banner || '').replace(/"/g, '""');
      csvContent += `${item.port},TCP,${item.service},${item.status},"${bannerClean}"\n`;
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `pesz_ara_scan_${targetInput.value.replace(/[^a-z0-9]/gi, '_')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function exportJSON() {
    if (scanResults.length === 0) {
      alert("No data available to export. Run a scan first.");
      return;
    }
    
    const jsonString = JSON.stringify(scanResults, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `pesz_ara_scan_${targetInput.value.replace(/[^a-z0-9]/gi, '_')}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
});
