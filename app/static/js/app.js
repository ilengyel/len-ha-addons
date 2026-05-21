(function () {
    var existingUser = document.querySelector('[data-existing-user]');
    var newUser = document.querySelector('[data-new-user]');

    if (!existingUser || !newUser) {
        return;
    }

    function syncFields() {
        if (newUser.value && existingUser.value) {
            existingUser.value = '';
        }
    }

    existingUser.addEventListener('change', function () {
        if (existingUser.value) {
            newUser.placeholder = 'Leave blank to use the selected person';
        } else {
            newUser.placeholder = 'Example: Alex';
        }
    });

    newUser.addEventListener('input', syncFields);
}());
