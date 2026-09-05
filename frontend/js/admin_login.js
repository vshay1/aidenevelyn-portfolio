document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorEl = document.getElementById('errorMessage');
    
    errorEl.classList.remove('show');
    
    try {
        const response = await fetch('/api/admin-login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.location.href = data.redirectTo;
        } else {
            errorEl.textContent = data.error || "Oops! That's not riiiight!";
            errorEl.classList.add('show');
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.classList.add('show');
    }
});

document.getElementById('username').focus();