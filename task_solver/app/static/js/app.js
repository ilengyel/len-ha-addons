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

    for (var i = 0; i < sections.length; i += 1) {
        var section = sections[i];
        var toggle = section.querySelector('[data-collapsible-toggle]');
        var body = section.querySelector('[data-collapsible-body]');

        if (!toggle || !body) {
            continue;
        }

        setExpanded(section, toggle.getAttribute('aria-expanded') === 'true' && !body.hidden);
        (function (currentSection, currentToggle) {
            currentToggle.addEventListener('click', function () {
                setExpanded(currentSection, currentToggle.getAttribute('aria-expanded') !== 'true');
            });
        }(section, toggle));
    }

    openSectionFromHash();
    window.addEventListener('hashchange', openSectionFromHash);
}());

(function () {
    var panels = document.querySelectorAll('[data-completion-panel]');

    if (!panels.length) {
        return;
    }

    function setPanelOpen(panel, open) {
        panel.hidden = !open;
        if (panel.parentNode) {
            panel.parentNode.classList.toggle('is-open', open);
        }
    }

    function openPanelFromHash() {
        if (!window.location.hash) {
            return;
        }

        var targetId = window.location.hash.slice(1);
        var isCompletionHash = targetId.indexOf('complete-task-') === 0;

        for (var i = 0; i < panels.length; i += 1) {
            setPanelOpen(panels[i], isCompletionHash && panels[i].id === targetId);
        }
    }

    openPanelFromHash();
    window.addEventListener('hashchange', openPanelFromHash);
}());

(function () {
    var whoSections = document.querySelectorAll('[data-who-section]');
    if (!whoSections.length) { return; }

    function collapseWho(whoList, whoToggle, whoTitle, name) {
        whoList.hidden = true;
        whoToggle.setAttribute('aria-expanded', 'false');
        if (whoTitle) { whoTitle.textContent = 'Who \u2014 ' + name; }
    }

    function expandWho(whoList, whoToggle, whoTitle) {
        whoList.hidden = false;
        whoToggle.setAttribute('aria-expanded', 'true');
        if (whoTitle) { whoTitle.textContent = 'Who'; }
    }

    for (var sectionIndex = 0; sectionIndex < whoSections.length; sectionIndex += 1) {
        var whoSection = whoSections[sectionIndex];
        var whoList = whoSection.querySelector('[data-who-list]');
        var whoToggle = whoSection.querySelector('[data-who-toggle]');
        var whoTitle = whoSection.querySelector('[data-who-title]');
        var radios = whoSection.querySelectorAll('[data-who-radio]');

        if (!whoList || !whoToggle) { continue; }

        for (var radioIndex = 0; radioIndex < radios.length; radioIndex += 1) {
            var radio = radios[radioIndex];
            (function (currentList, currentToggle, currentTitle, currentRadio) {
                currentRadio.addEventListener('change', function () {
                    if (currentRadio.checked) {
                        collapseWho(currentList, currentToggle, currentTitle, currentRadio.getAttribute('data-who-name'));
                    }
                });
            }(whoList, whoToggle, whoTitle, radio));
        }

        (function (currentSection, currentList, currentToggle, currentTitle) {
            currentToggle.addEventListener('click', function () {
                if (currentList.hidden) {
                    expandWho(currentList, currentToggle, currentTitle);
                } else {
                    var checked = currentSection.querySelector('[data-who-radio]:checked');
                    if (checked) {
                        collapseWho(currentList, currentToggle, currentTitle, checked.getAttribute('data-who-name'));
                    }
                }
            });
        }(whoSection, whoList, whoToggle, whoTitle));
    }
}());

(function () {
    var popups = document.querySelectorAll('details.editor-menu');

    if (!popups.length) {
        return;
    }

    function closeAllExcept(activePopup) {
        for (var i = 0; i < popups.length; i += 1) {
            var popup = popups[i];
            if (popup !== activePopup) {
                popup.removeAttribute('open');
            }
        }
    }

    for (var i = 0; i < popups.length; i += 1) {
        var popup = popups[i];
        popup.addEventListener('toggle', function () {
            if (this.open) {
                closeAllExcept(this);
            }
        });
    }

    document.addEventListener('click', function (event) {
        for (var i = 0; i < popups.length; i += 1) {
            var popup = popups[i];
            if (popup.open && !popup.contains(event.target)) {
                popup.removeAttribute('open');
            }
        }
    });
}());
