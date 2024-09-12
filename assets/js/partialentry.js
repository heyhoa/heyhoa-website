const form = document.getElementById('dynamicForm');

// Load saved form data from localStorage when the page loads
window.addEventListener('DOMContentLoaded', (event) => {
    const savedFormData = JSON.parse(localStorage.getItem('formData'));
    if (savedFormData) {
        for (let key in savedFormData) {
            const input = form.elements[key];
            if (input) {
                input.value = savedFormData[key];
            }
        }
    }
});

// Save form data to localStorage whenever an input changes
form.addEventListener('input', () => {
    let formData = {};
    for (let i = 0; i < form.elements.length; i++) {
        const input = form.elements[i];
        if (input.name) {
            formData[input.name] = input.value;
        }
    }
    localStorage.setItem('formData', JSON.stringify(formData));
});