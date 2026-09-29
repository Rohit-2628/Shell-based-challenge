document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("probe-form");
    const urlInput = document.getElementById("url");
    const methodSelect = document.getElementById("method");
    const timeoutInput = document.getElementById("timeout");
    const postDataInput = document.getElementById("post-data");
    const submitBtn = document.getElementById("submit-btn");
    const clearBtn = document.getElementById("clear-btn");
    
    const metaTarget = document.getElementById("meta-target");
    const metaStatus = document.getElementById("meta-status");
    const metaLatency = document.getElementById("meta-latency");
    const responseType = document.getElementById("response-type");
    const responseOutput = document.getElementById("response-output");
    const discoveryLog = document.getElementById("discovery-log");

    // Load Discovery Telemetry
    fetch("/api/discovery")
        .then(res => res.json())
        .then(data => {
            if (data.cluster_topology && data.cluster_topology.mesh_nodes) {
                let html = "<ul style='list-style: none; padding: 0;'>";
                data.cluster_topology.mesh_nodes.forEach(node => {
                    html += `<li style='margin-bottom: 6px;'>
                        <span style='color: #00e5ff; font-weight: bold;'>${node.endpoint}</span> 
                        <span style='color: #64748b;'>// ${node.description}</span>
                    </li>`;
                });
                html += "</ul>";
                discoveryLog.innerHTML = html;
            }
        })
        .catch(() => {
            discoveryLog.innerHTML = "<p style='color: #ff3366;'>Mesh discovery unreachable.</p>";
        });

    // Preset buttons
    document.querySelectorAll(".preset-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            urlInput.value = btn.getAttribute("data-url");
            if (urlInput.value.includes("vault")) {
                methodSelect.value = "GET";
            }
        });
    });

    // Clear output
    clearBtn.addEventListener("click", () => {
        responseOutput.textContent = "/* Cleared */";
        metaTarget.textContent = "--";
        metaStatus.textContent = "IDLE";
        metaLatency.textContent = "-- ms";
        responseType.textContent = "IDLE";
    });

    // Dispatch Probe
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const url = urlInput.value.trim();
        const method = methodSelect.value;
        const timeout = parseFloat(timeoutInput.value) || 3.0;
        const postData = postDataInput.value.trim();

        if (!url) return;

        submitBtn.disabled = true;
        submitBtn.querySelector(".btn-text").textContent = "DISPATCHING...";
        metaTarget.textContent = url;
        metaStatus.textContent = "PROBING...";
        responseType.textContent = "STREAMING";
        responseOutput.textContent = `[*] Connecting to ${url} via SSRF Gateway...`;

        const startTime = performance.now();

        try {
            const res = await fetch("/api/probe", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    url: url,
                    method: method,
                    timeout: timeout,
                    data: postData || null
                })
            });

            const latency = Math.round(performance.now() - startTime);
            metaLatency.textContent = `${latency} ms`;

            const data = await res.json();
            metaStatus.textContent = data.status || (res.ok ? "200 OK" : "ERROR");

            if (data.status === "SECURITY_VIOLATION") {
                responseType.textContent = "SECURITY_VIOLATION";
                responseOutput.textContent = `[!] PERIMETER POLICY VIOLATION:\n${data.error}`;
                responseOutput.style.color = "#ff3366";
            } else if (data.response) {
                responseType.textContent = data.protocol ? data.protocol.toUpperCase() : "RESPONSE";
                responseOutput.textContent = data.response;
                responseOutput.style.color = "#00ff88";
            } else if (data.json) {
                responseType.textContent = "JSON";
                responseOutput.textContent = JSON.stringify(data.json, null, 2);
                responseOutput.style.color = "#00e5ff";
            } else {
                responseType.textContent = "OUTPUT";
                responseOutput.textContent = JSON.stringify(data, null, 2);
                responseOutput.style.color = "#d1d9e6";
            }
        } catch (err) {
            metaStatus.textContent = "DISPATCH_FAILED";
            responseType.textContent = "ERROR";
            responseOutput.textContent = `[!] Network/Client error: ${err.message}`;
            responseOutput.style.color = "#ff3366";
        } finally {
            submitBtn.disabled = false;
            submitBtn.querySelector(".btn-text").textContent = "DISPATCH REFLECTION PROBE";
        }
    });
});
