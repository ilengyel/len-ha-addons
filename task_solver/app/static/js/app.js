(function () {
    var sections = document.querySelectorAll('[data-collapsible]');

    if (!sections.length) {
        return;
    }

    function setExpanded(section, expanded) {
        var toggle = section.querySelector('[data-collapsible-toggle]');
        var body = section.querySelector('[data-collapsible-body]');

        if (!toggle || !body) {
            return;
        }

        toggle.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        body.hidden = !expanded;
        section.classList.toggle('is-open', expanded);
    }

    function openSectionFromHash() {
        if (!window.location.hash) {
            return;
        }

        var section = document.getElementById(window.location.hash.slice(1));

        if (!section || !section.hasAttribute('data-collapsible')) {
            return;
        }

        setExpanded(section, true);
    }

    sections.forEach(function (section) {
        var toggle = section.querySelector('[data-collapsible-toggle]');
        var body = section.querySelector('[data-collapsible-body]');

        if (!toggle || !body) {
            return;
        }

        setExpanded(section, toggle.getAttribute('aria-expanded') === 'true' && !body.hidden);
        toggle.addEventListener('click', function () {
            setExpanded(section, toggle.getAttribute('aria-expanded') !== 'true');
        });
    });

    openSectionFromHash();
    window.addEventListener('hashchange', openSectionFromHash);
}());

(function () {
    var whoSection = document.querySelector('[data-who-section]');
    if (!whoSection) { return; }

    var whoList = whoSection.querySelector('[data-who-list]');
    var whoToggle = whoSection.querySelector('[data-who-toggle]');
    var whoTitle = whoSection.querySelector('[data-who-title]');
    var radios = whoSection.querySelectorAll('[data-who-radio]');

    if (!whoList || !whoToggle) { return; }

    function collapseWho(name) {
        whoList.hidden = true;
        whoToggle.setAttribute('aria-expanded', 'false');
        if (whoTitle) { whoTitle.textContent = 'Who \u2014 ' + name; }
    }

    function expandWho() {
        whoList.hidden = false;
        whoToggle.setAttribute('aria-expanded', 'true');
        if (whoTitle) { whoTitle.textContent = 'Who'; }
    }

    radios.forEach(function (radio) {
        radio.addEventListener('change', function () {
            if (radio.checked) {
                collapseWho(radio.getAttribute('data-who-name'));
            }
        });
    });

    whoToggle.addEventListener('click', function () {
        if (whoList.hidden) {
            expandWho();
        } else {
            var checked = whoSection.querySelector('[data-who-radio]:checked');
            if (checked) { collapseWho(checked.getAttribute('data-who-name')); }
        }
    });
}());

(function () {
    var popups = document.querySelectorAll('details.editor-menu');

    if (!popups.length) {
        return;
    }

    function closeAllExcept(activePopup) {
        popups.forEach(function (popup) {
            if (popup !== activePopup) {
                popup.removeAttribute('open');
            }
        });
    }

    popups.forEach(function (popup) {
        popup.addEventListener('toggle', function () {
            if (popup.open) {
                closeAllExcept(popup);
            }
        });
    });

    document.addEventListener('click', function (event) {
        popups.forEach(function (popup) {
            if (popup.open && !popup.contains(event.target)) {
                popup.removeAttribute('open');
            }
        });
    });
}());
