const form = document.getElementById('loginForm');
const message = document.getElementById('message');

const showMessage = (text, type = 'success') => {
    message.textContent = text;
    message.className = `message ${type}`;
};

form.addEventListener('submit', async event => {
    event.preventDefault(); // Prevent default form submission
    console.log('Form submit prevented, handling with JavaScript');
    const data = {
        username: form.username.value.trim(),
        password: form.password.value.trim(),
    };

    if (!data.username || !data.password) {
        showMessage('Please enter username and password.', 'error');
        return;
    }

    form.querySelector('button').disabled = true;
    showMessage('Authenticating...', 'success');

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
            credentials: 'include',
        });

        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);

        if (!response.ok) {
            const errorText = await response.text();
            console.log('Error response:', errorText);
            let error;
            try {
                error = JSON.parse(errorText);
            } catch {
                error = { error: errorText };
            }
            throw new Error(error.error || 'Login failed');
        }

        const result = await response.json();
        console.log('Login result:', result);
        showMessage('Login successful! Redirecting...', 'success');
        
        // Redirect to main check-in page with token in URL as backup
        setTimeout(() => {
            window.location.href = `/?token=${result.token}`;
        }, 1000);
    } catch (error) {
        console.error('Login error:', error);
        showMessage(error.message || 'Login failed. Please try again.', 'error');
    } finally {
        form.querySelector('button').disabled = false;
    }
});
