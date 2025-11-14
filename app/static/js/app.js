// API base URL
const API_BASE = '/api';

// Global state
let currentPage = 1;
let pageSize = 10;
let currentFilters = {};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadProducts();
    loadWebhooks();
});

// Event Listeners Setup
function initializeEventListeners() {
    // File upload
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('csv-file-input');
    const uploadBtn = document.getElementById('upload-btn');

    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('drop', handleFileDrop);
    fileInput.addEventListener('change', handleFileSelect);
    uploadBtn.addEventListener('click', handleFileUpload);

    // Products
    document.getElementById('create-product-btn').addEventListener('click', () => openProductModal());
    document.getElementById('refresh-products').addEventListener('click', loadProducts);
    document.getElementById('apply-filters').addEventListener('click', applyFilters);
    document.getElementById('bulk-delete-btn').addEventListener('click', handleBulkDelete);

    // Modals
    document.getElementById('close-product-modal').addEventListener('click', closeProductModal);
    document.getElementById('close-webhook-modal').addEventListener('click', closeWebhookModal);
    document.getElementById('cancel-product').addEventListener('click', closeProductModal);
    document.getElementById('cancel-webhook').addEventListener('click', closeWebhookModal);
    document.getElementById('product-form').addEventListener('submit', handleProductSubmit);
    document.getElementById('webhook-form').addEventListener('submit', handleWebhookSubmit);

    // Webhooks
    document.getElementById('create-webhook-btn').addEventListener('click', () => openWebhookModal());
}

// File Upload Functions
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.style.background = '#f0f0f0';
}

function handleFileDrop(e) {
    e.preventDefault();
    e.currentTarget.style.background = '';
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].name.endsWith('.csv')) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
}

function handleFile(file) {
    const uploadPrompt = document.getElementById('upload-prompt');
    const uploadBtn = document.getElementById('upload-btn');
    
    uploadPrompt.innerHTML = `<p>📄 Selected: ${file.name}</p>`;
    uploadBtn.style.display = 'block';
    uploadBtn.dataset.file = file.name;
    uploadBtn.dataset.fileContent = null;
    
    // Read file content
    const reader = new FileReader();
    reader.onload = (e) => {
        uploadBtn.dataset.fileContent = e.target.result;
    };
    reader.readAsText(file);
}

async function handleFileUpload() {
    const uploadBtn = document.getElementById('upload-btn');
    const fileContent = uploadBtn.dataset.fileContent;
    
    if (!fileContent) {
        alert('Please select a CSV file first');
        return;
    }

    const formData = new FormData();
    const blob = new Blob([fileContent], { type: 'text/csv' });
    formData.append('file', blob, 'products.csv');

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Upload failed');

        const data = await response.json();
        startProgressTracking(data.task_id);
    } catch (error) {
        alert('Upload failed: ' + error.message);
    }
}

function startProgressTracking(taskId) {
    const uploadPrompt = document.getElementById('upload-prompt');
    const uploadProgress = document.getElementById('upload-progress');
    const uploadBtn = document.getElementById('upload-btn');
    
    uploadPrompt.style.display = 'none';
    uploadProgress.style.display = 'block';
    uploadBtn.style.display = 'none';

    // Use SSE for real-time updates
    const eventSource = new EventSource(`${API_BASE}/upload/stream/${taskId}`);
    
    eventSource.onmessage = (event) => {
        const progress = JSON.parse(event.data);
        updateProgressUI(progress);
        
        if (progress.status === 'completed' || progress.status === 'failed') {
            eventSource.close();
            setTimeout(() => {
                uploadPrompt.style.display = 'block';
                uploadProgress.style.display = 'none';
                uploadPrompt.innerHTML = '<p>Click to select CSV file or drag and drop</p><p class="hint">Supports up to 500,000 products</p>';
                loadProducts(); // Refresh product list
            }, 3000);
        }
    };

    eventSource.onerror = () => {
        eventSource.close();
        // Fallback to polling
        pollProgress(taskId);
    };
}

function pollProgress(taskId) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/upload/status/${taskId}`);
            const progress = await response.json();
            updateProgressUI(progress);
            
            if (progress.status === 'completed' || progress.status === 'failed') {
                clearInterval(interval);
                setTimeout(() => {
                    document.getElementById('upload-prompt').style.display = 'block';
                    document.getElementById('upload-progress').style.display = 'none';
                    loadProducts();
                }, 3000);
            }
        } catch (error) {
            console.error('Progress polling error:', error);
        }
    }, 1000);
}

function updateProgressUI(progress) {
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressStatus = document.getElementById('progress-status');
    
    const percentage = progress.percentage || 0;
    progressFill.style.width = `${percentage}%`;
    progressFill.textContent = `${percentage}%`;
    progressText.textContent = progress.message || 'Processing...';
    progressStatus.textContent = progress.status || '';
}

// Product Functions
async function loadProducts() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize,
            ...currentFilters
        });
        
        const response = await fetch(`${API_BASE}/products?${params}`);
        const data = await response.json();
        
        renderProducts(data.items);
        renderPagination(data);
    } catch (error) {
        console.error('Error loading products:', error);
    }
}

function renderProducts(products) {
    const tbody = document.getElementById('products-tbody');
    tbody.innerHTML = '';
    
    if (products.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">No products found</td></tr>';
        return;
    }
    
    products.forEach(product => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${product.id}</td>
            <td>${product.sku}</td>
            <td>${product.name}</td>
            <td>${product.description || '-'}</td>
            <td><span class="badge ${product.active ? 'badge-success' : 'badge-danger'}">${product.active ? 'Active' : 'Inactive'}</span></td>
            <td>
                <button class="btn-secondary" onclick="editProduct(${product.id})">Edit</button>
                <button class="btn-danger" onclick="deleteProduct(${product.id})">Delete</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderPagination(data) {
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    
    if (data.total_pages <= 1) return;
    
    for (let i = 1; i <= data.total_pages; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.className = i === currentPage ? 'active' : '';
        btn.addEventListener('click', () => {
            currentPage = i;
            loadProducts();
        });
        pagination.appendChild(btn);
    }
}

function applyFilters() {
    currentFilters = {
        sku: document.getElementById('filter-sku').value,
        name: document.getElementById('filter-name').value,
        active: document.getElementById('filter-active').value
    };
    
    // Remove empty filters
    Object.keys(currentFilters).forEach(key => {
        if (!currentFilters[key]) delete currentFilters[key];
    });
    
    currentPage = 1;
    loadProducts();
}

function openProductModal(product = null) {
    const modal = document.getElementById('product-modal');
    const form = document.getElementById('product-form');
    const title = document.getElementById('product-modal-title');
    
    form.reset();
    
    if (product) {
        title.textContent = 'Edit Product';
        document.getElementById('product-id').value = product.id;
        document.getElementById('product-sku').value = product.sku;
        document.getElementById('product-name').value = product.name;
        document.getElementById('product-description').value = product.description || '';
        document.getElementById('product-active').checked = product.active;
    } else {
        title.textContent = 'Create Product';
    }
    
    modal.classList.add('show');
}

async function editProduct(id) {
    try {
        const response = await fetch(`${API_BASE}/products/${id}`);
        const product = await response.json();
        openProductModal(product);
    } catch (error) {
        alert('Error loading product: ' + error.message);
    }
}

async function handleProductSubmit(e) {
    e.preventDefault();
    
    const formData = {
        sku: document.getElementById('product-sku').value,
        name: document.getElementById('product-name').value,
        description: document.getElementById('product-description').value,
        active: document.getElementById('product-active').checked
    };
    
    const productId = document.getElementById('product-id').value;
    const url = productId ? `${API_BASE}/products/${productId}` : `${API_BASE}/products`;
    const method = productId ? 'PUT' : 'POST';
    
    try {
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) throw new Error('Save failed');
        
        closeProductModal();
        loadProducts();
    } catch (error) {
        alert('Error saving product: ' + error.message);
    }
}

async function deleteProduct(id) {
    if (!confirm('Are you sure you want to delete this product?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/products/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Delete failed');
        loadProducts();
    } catch (error) {
        alert('Error deleting product: ' + error.message);
    }
}

async function handleBulkDelete() {
    if (!confirm('⚠️ WARNING: This will delete ALL products. This cannot be undone. Are you absolutely sure?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/products/bulk/all`, { method: 'DELETE' });
        const data = await response.json();
        alert(`Deleted ${data.deleted_count} products`);
        loadProducts();
    } catch (error) {
        alert('Error deleting products: ' + error.message);
    }
}

function closeProductModal() {
    document.getElementById('product-modal').classList.remove('show');
}

// Webhook Functions
async function loadWebhooks() {
    try {
        const response = await fetch(`${API_BASE}/webhooks`);
        const webhooks = await response.json();
        renderWebhooks(webhooks);
    } catch (error) {
        console.error('Error loading webhooks:', error);
    }
}

function renderWebhooks(webhooks) {
    const container = document.getElementById('webhooks-list');
    
    if (webhooks.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">No webhooks configured</p>';
        return;
    }
    
    container.innerHTML = webhooks.map(webhook => `
        <div class="webhook-item">
            <div class="webhook-info">
                <h3>${webhook.url}</h3>
                <p><strong>Event:</strong> ${webhook.event_type}</p>
                <p><strong>Status:</strong> <span class="badge ${webhook.enabled ? 'badge-success' : 'badge-danger'}">${webhook.enabled ? 'Enabled' : 'Disabled'}</span></p>
                ${webhook.description ? `<p>${webhook.description}</p>` : ''}
            </div>
            <div class="webhook-actions">
                <button class="btn-secondary" onclick="testWebhook(${webhook.id})">Test</button>
                <button class="btn-secondary" onclick="editWebhook(${webhook.id})">Edit</button>
                <button class="btn-danger" onclick="deleteWebhook(${webhook.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

function openWebhookModal(webhook = null) {
    const modal = document.getElementById('webhook-modal');
    const form = document.getElementById('webhook-form');
    const title = document.getElementById('webhook-modal-title');
    
    form.reset();
    
    if (webhook) {
        title.textContent = 'Edit Webhook';
        document.getElementById('webhook-id').value = webhook.id;
        document.getElementById('webhook-url').value = webhook.url;
        document.getElementById('webhook-event-type').value = webhook.event_type;
        document.getElementById('webhook-secret').value = webhook.secret || '';
        document.getElementById('webhook-description').value = webhook.description || '';
        document.getElementById('webhook-enabled').checked = webhook.enabled;
    } else {
        title.textContent = 'Create Webhook';
    }
    
    modal.classList.add('show');
}

async function editWebhook(id) {
    try {
        const response = await fetch(`${API_BASE}/webhooks/${id}`);
        const webhook = await response.json();
        openWebhookModal(webhook);
    } catch (error) {
        alert('Error loading webhook: ' + error.message);
    }
}

async function handleWebhookSubmit(e) {
    e.preventDefault();
    
    const formData = {
        url: document.getElementById('webhook-url').value,
        event_type: document.getElementById('webhook-event-type').value,
        secret: document.getElementById('webhook-secret').value || null,
        description: document.getElementById('webhook-description').value || null,
        enabled: document.getElementById('webhook-enabled').checked
    };
    
    const webhookId = document.getElementById('webhook-id').value;
    const url = webhookId ? `${API_BASE}/webhooks/${webhookId}` : `${API_BASE}/webhooks`;
    const method = webhookId ? 'PUT' : 'POST';
    
    try {
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Save failed');
        }
        
        closeWebhookModal();
        loadWebhooks();
    } catch (error) {
        alert('Error saving webhook: ' + error.message);
    }
}

async function testWebhook(id) {
    try {
        const response = await fetch(`${API_BASE}/webhooks/${id}/test`, { method: 'POST' });
        const result = await response.json();
        
        const message = result.success
            ? `✅ Success! Status: ${result.status_code}, Response time: ${result.response_time_ms}ms`
            : `❌ Failed: ${result.error || result.message}`;
        
        alert(message);
    } catch (error) {
        alert('Error testing webhook: ' + error.message);
    }
}

async function deleteWebhook(id) {
    if (!confirm('Are you sure you want to delete this webhook?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/webhooks/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Delete failed');
        loadWebhooks();
    } catch (error) {
        alert('Error deleting webhook: ' + error.message);
    }
}

function closeWebhookModal() {
    document.getElementById('webhook-modal').classList.remove('show');
}

