const form = document.getElementById('checkinForm');
const message = document.getElementById('message');

const showMessage = (text, type = 'success') => {
    message.textContent = text;
    message.className = `message ${type}`;
};

const normalizeTimestamp = () => {
    const input = document.getElementById('timestamp');
    if (!input.value) {
        return new Date().toISOString();
    }
    return new Date(input.value).toISOString();
};

form.addEventListener('submit', async event => {
    event.preventDefault();
    const data = {
        user_id: form.user_id.value.trim(),
        timestamp: normalizeTimestamp(),
    };

    if (!data.user_id) {
        showMessage('Employee ID is required.', 'error');
        return;
    }

    form.querySelector('button').disabled = true;
    showMessage('Submitting check-in...', 'success');

    try {
        const response = await fetch('/submit_checkin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
            credentials: 'include',
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Not authenticated, redirect to login
                window.location.href = '/login.html';
                return;
            }
            const error = await response.json();
            throw new Error(error.error || 'Submission failed');
        }

        const payload = await response.json();
        showMessage('Check-in submitted successfully!', 'success');
        form.reset();
    } catch (error) {
        showMessage(error.message || 'Unable to submit check-in.', 'error');
    } finally {
        form.querySelector('button').disabled = false;
    }
});
