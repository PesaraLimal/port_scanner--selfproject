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
  const detectedIpWrapper = document.getElementById('detected-ip-wrapper');
  const detectedIpVal = document.getElementById('detected-ip-val');
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

  // Dynamic API Base URL detection.
  // We will initialize it with an empty string, and checkApiStatus() will update it if a local server is present.
  let API_BASE = '';


  // --- Initializers & Event Listeners ---
  initSliders();
  initProfilePresets();
  initDetectedIpShortcut();
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

  // State variable to track API environment
  let apiEnvironment = 'local'; // default fallback
  const localTargetWarning = document.getElementById('local-target-warning');

  // Check backend serverless API status (Hybrid Local/Cloud detector)
  async function checkApiStatus() {
    apiStatusDot.className = 'status-indicator-dot loading';
    apiStatusText.textContent = 'CHECKING API STATUS...';
    
    // Step 1: Probe local backend first
    try {
      const localResponse = await fetch(`http://127.0.0.1:5000/api/status`);
      if (localResponse.ok) {
        const data = await localResponse.json();
        API_BASE = 'http://127.0.0.1:5000';
        apiEnvironment = 'local';
        apiStatusDot.className = 'status-indicator-dot online';
        apiStatusText.textContent = `API ONLINE (LOCAL SERVER) | ${data.version || 'v1'}`;
        hideDetectedIp();
        validateTargetAddress();
        return;
      }
    } catch (e) {
      // Local server is offline or blocked, proceed to check current origin (could be cloud host)
    }

    // Step 2: Fallback to the serving origin API
    try {
      const response = await fetch(`/api/status`);
      if (response.ok) {
        const data = await response.json();
        API_BASE = ''; // Root relative path
        apiEnvironment = data.environment || 'local';
        
        apiStatusDot.className = 'status-indicator-dot online';
        if (apiEnvironment === 'vercel') {
          apiStatusText.textContent = `API ONLINE (CLOUD - VERCEL) | ${data.version || 'v1'}`;
          if (data.client_ip) {
            showDetectedIp(data.client_ip);
          } else {
            hideDetectedIp();
          }
        } else {
          apiStatusText.textContent = `API ONLINE (LOCAL SERVER) | ${data.version || 'v1'}`;
          hideDetectedIp();
        }
        
        validateTargetAddress();
      } else {
        throw new Error('API returned error response');
      }
    } catch (error) {
      console.warn("API status check failed:", error);
      apiStatusDot.className = 'status-indicator-dot offline';
      apiStatusText.textContent = 'API OFFLINE / DISCONNECTED';
      hideDetectedIp();
    }
  }

  function initDetectedIpShortcut() {
    if (detectedIpWrapper) {
      detectedIpWrapper.addEventListener('click', () => {
        const ip = detectedIpVal.textContent;
        if (ip && ip !== '...' && ip !== 'Detecting...') {
          targetInput.value = ip;
          validateTargetAddress();
          addLog(`Target host updated to your public IP: ${ip}`, 'system');
        }
      });
    }
  }

  function showDetectedIp(ip) {
    if (detectedIpWrapper && detectedIpVal) {
      detectedIpVal.textContent = ip;
      detectedIpWrapper.classList.remove('hidden');
      
      // Auto-pre-fill target input if it is still the default 127.0.0.1
      if (targetInput.value === '127.0.0.1') {
        targetInput.value = ip;
        validateTargetAddress();
        addLog(`Cloud mode: Pre-filled target with your detected public IP: ${ip}`, 'system');
      }
    }
  }

  function hideDetectedIp() {
    if (detectedIpWrapper) {
      detectedIpWrapper.classList.add('hidden');
    }
  }

  // Monitor target host to display warning when scanning local from Cloud Vercel API
  function validateTargetAddress() {
    const target = targetInput.value.trim().toLowerCase();
    const warningDescription = document.querySelector('#local-target-warning .warning-description');
    const warningTitle = document.querySelector('#local-target-warning .warning-title');
    
    const isLoopback = target === 'localhost' || target === '127.0.0.1' || target === '0.0.0.0';
    
    const isPrivateIp = target.startsWith('192.168.') || 
                        target.startsWith('10.') || 
                        target.startsWith('172.16.') || 
                        target.startsWith('172.17.') || 
                        target.startsWith('172.18.') || 
                        target.startsWith('172.19.') || 
                        target.startsWith('172.20.') || 
                        target.startsWith('172.21.') || 
                        target.startsWith('172.22.') || 
                        target.startsWith('172.23.') || 
                        target.startsWith('172.24.') || 
                        target.startsWith('172.25.') || 
                        target.startsWith('172.26.') || 
                        target.startsWith('172.27.') || 
                        target.startsWith('172.28.') || 
                        target.startsWith('172.29.') || 
                        target.startsWith('172.30.') || 
                        target.startsWith('172.31.');

    if ((isLoopback || isPrivateIp) && apiEnvironment === 'vercel') {
      if (localTargetWarning) {
        localTargetWarning.classList.remove('hidden');
        if (warningTitle && warningDescription) {
          if (isLoopback) {
            warningTitle.textContent = "Local Loopback Scan Alert";
            warningDescription.innerHTML = `You are connected to the <strong>Cloud API (Vercel)</strong>. Scanning loopback addresses will scan Vercel's container loopback instead of your device. To audit your local machine, run the local backend server using <code>run.bat</code>.`;
          } else {
            warningTitle.textContent = "Private IP Scan Alert";
            warningDescription.innerHTML = `You are connected to the <strong>Cloud API (Vercel)</strong>. Cloud servers cannot reach private IP addresses like <code>${escapeHtml(target)}</code> inside your local network. To scan local devices, run the local backend server using <code>run.bat</code>.`;
          }
        }
      }
    } else {
      if (localTargetWarning) {
        localTargetWarning.classList.add('hidden');
      }
    }
  }

  // Bind keyup and change event on target input to update dynamic alert real-time
  targetInput.addEventListener('input', validateTargetAddress);


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
    
    // Hide vulnerability card on new scan initialization
    if (vulnerabilityCard) {
      vulnerabilityCard.classList.add('hidden');
    }
    
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

  // Vulnerability Reporting DOM elements
  const vulnerabilityCard = document.getElementById('vulnerability-card');
  const vulnReportList = document.getElementById('vuln-report-list');
  const vulnCountHigh = document.getElementById('vuln-count-high');
  const vulnCountMedium = document.getElementById('vuln-count-medium');
  const vulnCountLow = document.getElementById('vuln-count-low');

  // Educational vulnerability lookup catalog
  const PORT_VULNERABILITIES = {
    21: {
      service: "FTP",
      severity: "high",
      vulnerability: "FTP transmits credentials and payload data in unencrypted cleartext. Exposed to eavesdropping and credential sniffing.",
      recommendation: "Migrate to SFTP (SSH File Transfer Protocol) or FTPS (FTP over SSL/TLS). Disable anonymous logins."
    },
    22: {
      service: "SSH",
      severity: "low",
      vulnerability: "Exposed SSH service interface. Susceptible to brute-force credential stuffing and potential zero-day vulnerabilities.",
      recommendation: "Ensure password authentication is disabled in favor of cryptographic key-pair logins. Limit source IPs at the firewall."
    },
    23: {
      service: "Telnet",
      severity: "high",
      vulnerability: "All communications (including root passwords) are transmitted in unencrypted text. Highly vulnerable to MITM attacks.",
      recommendation: "Immediately disable the Telnet daemon. Enforce SSH (Port 22) for all console-based administrative remote sessions."
    },
    25: {
      service: "SMTP",
      severity: "medium",
      vulnerability: "Unencrypted mail transfer. May act as an open mail relay, permitting spam abuse if configured incorrectly.",
      recommendation: "Enable TLS transport encryption (STARTTLS) and enforce SMTP authentication (SASL). Restrict relaying domains."
    },
    53: {
      service: "DNS",
      severity: "medium",
      vulnerability: "Potential exposure to DNS Amplification DDoS attacks, Zone Transfer disclosure (AXFR), or Cache Poisoning spoofing.",
      recommendation: "Configure DNS server to disable open recursion for external networks. Prevent unauthorized zone transfers."
    },
    80: {
      service: "HTTP",
      severity: "medium",
      vulnerability: "Data is transmitted in cleartext. Sessions, cookies, and login credentials can be hijacked over untrusted networks.",
      recommendation: "Deploy SSL/TLS certificates (e.g., Let's Encrypt). Redirect all unencrypted HTTP traffic (Port 80) to HTTPS (Port 443)."
    },
    110: {
      service: "POP3",
      severity: "high",
      vulnerability: "E-mail access is unencrypted by default. Mail content and user account credentials are sent over the wire in plain text.",
      recommendation: "Migrate to POP3S (POP3 over SSL/TLS, typically Port 995) or use secure IMAPS instead."
    },
    123: {
      service: "NTP",
      severity: "low",
      vulnerability: "NTP daemons are historically vulnerable to UDP reflection/amplification denial-of-service attacks.",
      recommendation: "Keep NTP daemon updated. Disable control queries ('noquery' configuration option) in NTP configuration."
    },
    143: {
      service: "IMAP",
      severity: "high",
      vulnerability: "Plaintext retrieval of email messages and credentials. Susceptible to credential harvesting via traffic capture.",
      recommendation: "Enforce IMAPS (IMAP over SSL/TLS, Port 993) and restrict plain authentication protocols."
    },
    443: {
      service: "HTTPS",
      severity: "low",
      vulnerability: "Secure web service. Threat exposure relies on backend software versions, TLS cipher suites, or certificate validity.",
      recommendation: "Disable legacy TLS versions (1.0, 1.1) and weak SSL ciphers. Maintain web server software security updates."
    },
    445: {
      service: "Microsoft-DS (SMB)",
      severity: "high",
      vulnerability: "Direct exposure of Windows file sharing. Historically targeted by critical worm exploits (e.g. WannaCry, EternalBlue).",
      recommendation: "Block Port 445 at the perimeter firewall. Disable outdated SMBv1 protocol. Enforce SMB signing."
    },
    1433: {
      service: "MSSQL",
      severity: "high",
      vulnerability: "Database instance access exposed. Highly targeted for credential brute-forcing and SQL injection payload execution.",
      recommendation: "Bind SQL Server to local interfaces only or restrict via firewall IP whitelisting. Use Windows Integrated Authentication."
    },
    3306: {
      service: "MySQL",
      severity: "high",
      vulnerability: "Direct exposure of relational database. Targets brute force attempts and potential remote code execution via vulnerabilities.",
      recommendation: "Ensure MySQL is bound to 127.0.0.1 or restricted private IPs. Enforce strong password policies and TLS connection encryption."
    },
    3389: {
      service: "RDP",
      severity: "high",
      vulnerability: "Remote desktop portal. High-risk target for brute-force attacks and exploit attempts targeting remote access flaws.",
      recommendation: "Do not expose RDP directly to the public web. Utilize a VPN gateway, enable Multi-Factor Authentication, or configure NLA."
    },
    5432: {
      service: "PostgreSQL",
      severity: "high",
      vulnerability: "PostgreSQL database listener exposed. Vulnerable to dictionary attacks, privilege escalation, and network snooping.",
      recommendation: "Bind server to local loopback. Restrict remote client IPs in `pg_hba.conf` and enforce connection encryption (SSL)."
    },
    6379: {
      service: "Redis",
      severity: "high",
      vulnerability: "In-memory database instance. Redis lacks robust default authentication and is highly vulnerable to remote script execution.",
      recommendation: "Do not expose Redis to the public interface. Enforce binding to 127.0.0.1 and enable password authentication (`requirepass`)."
    },
    8080: {
      service: "HTTP-ALT",
      severity: "medium",
      vulnerability: "Often runs development interfaces, admin dashboards, or unhardened application code in cleartext.",
      recommendation: "Restrict public access. If exposing to users, wrap with an HTTPS reverse proxy and enforce robust user authentication."
    },
    8443: {
      service: "HTTPS-ALT",
      severity: "low",
      vulnerability: "Alternative SSL port. Security depends heavily on the robustness of the underlying web application running on this port.",
      recommendation: "Perform regular vulnerability audits on applications bound to this port. Keep server components updated."
    }
  };

  // Dynamic Vulnerability Assessment Report Generator
  function generateVulnerabilityReport() {
    const openPorts = scanResults.filter(r => r.status === 'Open');
    
    if (openPorts.length === 0) {
      vulnerabilityCard.classList.add('hidden');
      return;
    }
    
    // Count severities
    let highCount = 0;
    let mediumCount = 0;
    let lowCount = 0;
    
    const vulnHtml = openPorts.map(portObj => {
      const port = portObj.port;
      const service = portObj.service;
      
      // Look up vulnerability database
      const vulnInfo = PORT_VULNERABILITIES[port] || {
        service: service,
        severity: "medium",
        vulnerability: `Port is open and listening. Active services represent potential access vectors for scanning or targeting.`,
        recommendation: "Inspect service configuration logs. Disable service if it is not required for production operations."
      };
      
      if (vulnInfo.severity === 'high') highCount++;
      else if (vulnInfo.severity === 'medium') mediumCount++;
      else lowCount++;
      
      const severityClass = vulnInfo.severity;
      const severityText = severityClass.toUpperCase();
      
      return `
        <div class="vuln-entry">
          <div class="vuln-entry-header">
            <div class="vuln-entry-title">
              <span>Port ${port}</span> ${escapeHtml(vulnInfo.service)}
            </div>
            <span class="vuln-severity-badge ${severityClass}">${severityText}</span>
          </div>
          <div class="vuln-details-box">
            <div class="vuln-detail-desc">
              <strong>Risk:</strong> ${escapeHtml(vulnInfo.vulnerability)}
            </div>
            <div class="vuln-detail-recom">
              <strong>Mitigation:</strong> ${escapeHtml(vulnInfo.recommendation)}
            </div>
          </div>
        </div>
      `;
    }).join('');
    
    // Update counters
    vulnCountHigh.textContent = highCount;
    vulnCountMedium.textContent = mediumCount;
    vulnCountLow.textContent = lowCount;
    
    // Render list
    vulnReportList.innerHTML = vulnHtml;
    
    // Unhide the report card
    vulnerabilityCard.classList.remove('hidden');
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

    // Generate vulnerability report
    generateVulnerabilityReport();

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
        
        // Notify user if backend resolved cloud loopback to their client public IP
        if (data.resolved_from_client && index === 0) {
          addLog(`[CLOUD] Resolved loopback target to client public IP: ${data.target_ip} to scan your network border.`, 'warning');
        }

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
