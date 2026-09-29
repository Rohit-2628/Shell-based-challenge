document.addEventListener('DOMContentLoaded', () => {
    const logSelect = document.getElementById('log-select');
    const customFileInput = document.getElementById('custom-file');
    const btnFetchLog = document.getElementById('btn-fetch-log');
    const logOutput = document.getElementById('log-output');

    const dispatchUrl = document.getElementById('dispatch-url');
    const dispatchMethod = document.getElementById('dispatch-method');
    const dispatchToken = document.getElementById('dispatch-token');
    const dispatchData = document.getElementById('dispatch-data');
    const btnDispatch = document.getElementById('btn-dispatch');
    const dispatchOutput = document.getElementById('dispatch-output');
    const metricCore = document.getElementById('metric-core');

    // 1. Fetch Diagnostic Log
    btnFetchLog.addEventListener('click', async () => {
        let filename = customFileInput.value.trim() || logSelect.value;
        logOutput.textContent = `[FETCHING] /api/diagnostics/log?file=${encodeURIComponent(filename)}...`;

        try {
            const resp = await fetch(`/api/diagnostics/log?file=${encodeURIComponent(filename)}`);
            const data = await resp.json();
            logOutput.textContent = JSON.stringify(data, null, 2);
            if (data.status === 'SUCCESS' && data.content) {
                // If content is pure string, also show formatted text
                logOutput.textContent = `[FILE: ${data.file}]\n${data.content}`;
            }
        } catch (err) {
            logOutput.textContent = `[ERROR] Failed to fetch log: ${err.message}`;
        }
    });

    // 2. Dispatch Mesh Request
    btnDispatch.addEventListener('click', async () => {
        const url = dispatchUrl.value.trim();
        const method = dispatchMethod.value;
        const token = dispatchToken.value.trim();
        let payloadData = null;

        if (dispatchData.value.trim()) {
            try {
                payloadData = JSON.parse(dispatchData.value.trim());
            } catch (e) {
                payloadData = dispatchData.value.trim();
            }
        }

        const headers = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        if (payloadData && typeof payloadData === 'object') {
            headers['Content-Type'] = 'application/json';
        }

        dispatchOutput.textContent = `[DISPATCHING] ${method} ${url}...\n`;

        try {
            const resp = await fetch('/api/mesh/dispatch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: url,
                    method: method,
                    headers: headers,
                    data: payloadData
                })
            });

            const result = await resp.json();
            dispatchOutput.textContent = JSON.stringify(result, null, 2);

            // Update core metric if response gives indication
            if (result.response && result.response.workload_status === 'ACTIVE') {
                metricCore.textContent = 'ONLINE';
                metricCore.className = 'metric-val green';
            }
        } catch (err) {
            dispatchOutput.textContent = `[DISPATCH_FAILED] Error: ${err.message}`;
        }
    });
});
