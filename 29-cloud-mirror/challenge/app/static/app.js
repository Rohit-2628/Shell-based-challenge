document.addEventListener('DOMContentLoaded', () => {
    const fetchForm = document.getElementById('fetchForm');
    const targetUrlInput = document.getElementById('targetUrl');
    const toggleHeadersBtn = document.getElementById('toggleHeadersBtn');
    const headersContainer = document.getElementById('headersContainer');
    const customHeadersInput = document.getElementById('customHeaders');
    const fetchBtn = document.getElementById('fetchBtn');

    const statusBadge = document.getElementById('statusBadge');
    const resContentType = document.getElementById('resContentType');
    const resHttpStatus = document.getElementById('resHttpStatus');
    const resSize = document.getElementById('resSize');
    const imagePreviewContainer = document.getElementById('imagePreviewContainer');
    const imagePreview = document.getElementById('imagePreview');
    const responseBody = document.getElementById('responseBody');

    // Preset buttons
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            targetUrlInput.value = btn.getAttribute('data-url');
        });
    });

    // Toggle custom headers box
    toggleHeadersBtn.addEventListener('click', () => {
        headersContainer.classList.toggle('hidden');
        if (headersContainer.classList.contains('hidden')) {
            toggleHeadersBtn.textContent = '+ Advanced: Add Custom Headers (JSON)';
        } else {
            toggleHeadersBtn.textContent = '- Hide Custom Headers';
        }
    });

    // Form submission
    fetchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const targetUrl = targetUrlInput.value.trim();
        if (!targetUrl) return;

        let headers = {};
        const headersRaw = customHeadersInput.value.trim();
        if (headersRaw) {
            try {
                headers = JSON.parse(headersRaw);
            } catch (err) {
                alert('Invalid JSON in custom headers field!');
                return;
            }
        }

        // Set Loading state
        statusBadge.className = 'badge loading';
        statusBadge.textContent = 'FETCHING...';
        fetchBtn.disabled = true;
        responseBody.textContent = 'Contacting remote asset server...';
        imagePreviewContainer.classList.add('hidden');
        resContentType.textContent = '-';
        resHttpStatus.textContent = '-';
        resSize.textContent = '-';

        try {
            const resp = await fetch('/api/v1/fetch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: targetUrl,
                    headers: headers
                })
            });

            const data = await resp.json();

            if (data.http_status) {
                resHttpStatus.textContent = `HTTP ${data.http_status}`;
            } else if (data.status) {
                resHttpStatus.textContent = data.status.toUpperCase();
            }

            resContentType.textContent = data.content_type || '-';
            resSize.textContent = data.size_bytes ? `${data.size_bytes} bytes` : '-';

            if (data.status === 'success' || data.http_status === 200) {
                statusBadge.className = 'badge success';
                statusBadge.textContent = 'SUCCESS (200 OK)';
            } else if (data.http_status === 401 || data.http_status === 403) {
                statusBadge.className = 'badge error';
                statusBadge.textContent = `ACCESS RESTRICTED (${data.http_status})`;
            } else {
                statusBadge.className = 'badge error';
                statusBadge.textContent = (data.status || 'ERROR').toUpperCase();
            }

            // Body rendering
            if (data.image_preview) {
                imagePreview.src = data.image_preview;
                imagePreviewContainer.classList.remove('hidden');
            }

            if (data.is_json && data.json_data) {
                responseBody.textContent = JSON.stringify(data.json_data, null, 2);
            } else if (data.body) {
                responseBody.textContent = data.body;
            } else if (data.error) {
                responseBody.textContent = `[Error] ${data.error}\n${data.message || ''}`;
            } else {
                responseBody.textContent = JSON.stringify(data, null, 2);
            }

        } catch (err) {
            statusBadge.className = 'badge error';
            statusBadge.textContent = 'NETWORK FAILURE';
            responseBody.textContent = `Fetch error: ${err.message}`;
        } finally {
            fetchBtn.disabled = false;
        }
    });
});
