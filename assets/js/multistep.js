window.addEventListener("DOMContentLoaded", (event) => {
    let currentFieldset = 0; // This keeps track of the current fieldset
    const fieldsets = document.querySelectorAll('.multistep fieldset'); // This selects all the fieldsets
  
    // Initially hide all fieldsets except the first one
    for (let i = 0; i < fieldsets.length; i++) {
        if (i !== currentFieldset) {
            fieldsets[i].style.display = 'none';
        }
    }
  
    // Attach event listeners to the 'next' buttons
    const nextButtons = document.querySelectorAll('.multistep .next');
    nextButtons.forEach((button, index) => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            // Get all the input fields inside the current fieldset
            const inputs = fieldsets[index].querySelectorAll('input, textarea, select');
            let isValid = true;
  
            // Validate each input
            for (let input of inputs) {
                // checkValidity() returns true if the input passes its constraints (like required, type, min, max, etc.)
                if (!input.checkValidity()) {
                    isValid = false;
                    break;
                }
            }
  
            // Only proceed if all inputs are valid
            if (isValid) {
                fieldsets[index].style.display = 'none';
                fieldsets[index + 1].style.display = 'block';
            } else {
                alert('Please complete all required fields correctly before proceeding.');
            }
        });
    });
  
    // Attach event listeners to the 'previous' buttons
    const previousButtons = document.querySelectorAll('.multistep .previous');
    previousButtons.forEach((button, index) => {
        button.addEventListener('click', () => {
            fieldsets[index + 1].style.display = 'none';
            fieldsets[index].style.display = 'block';
        });
    });
  });
  