const API_BASE = "http://127.0.0.1:8000/api";

// Toggle password field in Hide section
document.getElementById('use-encryption').addEventListener('change', function() {
    const pwdGroup = document.getElementById('hide-password-group');
    if(this.checked) {
        pwdGroup.style.display = 'block';
    } else {
        pwdGroup.style.display = 'none';
        document.getElementById('hide-password').value = '';
    }
});

function setStatus(id, msg) {
    document.getElementById(id).textContent = msg;
}

function setLoading(btnId, isLoading) {
    const btn = document.getElementById(btnId);
    if(isLoading) {
        btn.classList.add('loading');
        btn.disabled = true;
    } else {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

// ------------------- HIDE -------------------
document.getElementById('hide-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const coverImage = document.getElementById('cover-image').files[0];
    const secretText = document.getElementById('secret-text').value.trim();
    const secretFile = document.getElementById('secret-file').files[0];
    const useEncryption = document.getElementById('use-encryption').checked;
    const password = document.getElementById('hide-password').value;
    
    if(!secretText && !secretFile) {
        alert('Please provide secret text or a secret file to hide.');
        return;
    }
    if(useEncryption && password.length < 4) {
        alert('Password must be at least 4 characters.');
        return;
    }
    
    const formData = new FormData();
    formData.append('cover_image', coverImage);
    if(secretText) formData.append('secret_text', secretText);
    if(secretFile) formData.append('secret_file', secretFile);
    if(useEncryption && password) formData.append('password', password);
    
    setLoading('hide-btn', true);
    setStatus('hide-status', 'Processing. This might take a moment...');
    
    try {
        const response = await fetch(`${API_BASE}/hide`, {
            method: 'POST',
            body: formData
        });
        
        if(!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to hide message');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `stego_${coverImage.name}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        
        setStatus('hide-status', 'Success! Downloaded stego image.');
    } catch(err) {
        setStatus('hide-status', 'Error: ' + err.message);
    } finally {
        setLoading('hide-btn', false);
    }
});

// ------------------- EXTRACT -------------------
document.getElementById('extract-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const stegoImage = document.getElementById('stego-image').files[0];
    const password = document.getElementById('extract-password').value;
    
    const formData = new FormData();
    formData.append('stego_image', stegoImage);
    if(password) formData.append('password', password);
    
    setLoading('extract-btn', true);
    setStatus('extract-status', 'Extracting...');
    
    // reset UI
    document.getElementById('extract-result').classList.add('hidden');
    document.getElementById('extracted-text-container').classList.add('hidden');
    document.getElementById('extracted-file-container').classList.add('hidden');
    
    try {
        const response = await fetch(`${API_BASE}/extract`, {
            method: 'POST',
            body: formData
        });
        
        if(!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to extract message');
        }
        
        const data = await response.json();
        
        document.getElementById('extract-result').classList.remove('hidden');
        
        if(data.text) {
            document.getElementById('extracted-text').textContent = data.text;
            document.getElementById('extracted-text-container').classList.remove('hidden');
        }
        
        if(data.file) {
            const fileContainer = document.getElementById('extracted-file-container');
            const fileLink = document.getElementById('extracted-file-link');
            
            // Reconstruct file from base64
            const byteCharacters = atob(data.file.data);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray]);
            
            const objectUrl = URL.createObjectURL(blob);
            fileLink.href = objectUrl;
            fileLink.download = data.file.filename;
            
            fileContainer.classList.remove('hidden');
        }
        
        setStatus('extract-status', 'Success! Secret revealed.');
    } catch(err) {
        setStatus('extract-status', 'Error: ' + err.message);
    } finally {
        setLoading('extract-btn', false);
    }
});

// ------------------- COMPARE -------------------
document.getElementById('compare-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const orig = document.getElementById('comp-original').files[0];
    const stego = document.getElementById('comp-stego').files[0];
    
    const formData = new FormData();
    formData.append('original_image', orig);
    formData.append('stego_image', stego);
    
    setLoading('compare-btn', true);
    setStatus('compare-status', 'Analyzing differences...');
    
    document.getElementById('compare-result').classList.add('hidden');
    
    try {
        const response = await fetch(`${API_BASE}/compare`, {
            method: 'POST',
            body: formData
        });
        
        if(!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Comparison failed');
        }
        
        const data = await response.json();
        
        // Render Image
        const img = document.getElementById('diff-image');
        img.src = data.diff_image_b64;
        
        // Render Stats
        document.getElementById('stat-dim').textContent = data.dimensions;
        document.getElementById('stat-px').textContent = data.changed_pixels;
        document.getElementById('stat-pct').textContent = data.percent_changed;
        document.getElementById('stat-lsb').textContent = data.lsb_differences;
        document.getElementById('stat-mse').textContent = data.mse;
        document.getElementById('stat-psnr').textContent = data.psnr;
        
        document.getElementById('compare-result').classList.remove('hidden');
        setStatus('compare-status', 'Analysis complete.');
    } catch(err) {
        setStatus('compare-status', 'Error: ' + err.message);
    } finally {
        setLoading('compare-btn', false);
    }
});
