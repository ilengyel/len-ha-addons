(function () {
    var root = document.documentElement;
    var toggle = document.querySelector('[data-theme-toggle]');
    var toggleLabel = document.querySelector('[data-theme-toggle-label]');
    var themeColor = document.querySelector('[data-theme-color]');
    var storageKey = 'task-solver-theme';

    if (!toggle) {
        return;
    }

    function setTheme(theme) {
        var isDark = theme === 'dark';

        if (isDark) {
            root.setAttribute('data-theme', 'dark');
        } else {
            root.removeAttribute('data-theme');
        }

        toggle.setAttribute('aria-pressed', isDark ? 'true' : 'false');
        toggle.setAttribute('aria-label', isDark ? 'Use light theme' : 'Use dark theme');
        toggle.setAttribute('title', isDark ? 'Use light theme' : 'Use dark theme');
        if (toggleLabel) {
            toggleLabel.textContent = isDark ? 'Use light theme' : 'Use dark theme';
        }
        if (themeColor) {
            themeColor.setAttribute('content', isDark ? '#17120f' : '#7f3018');
        }
    }

    function saveTheme(theme) {
        window.localStorage.setItem(storageKey, theme);
    }

    setTheme(root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light');

    toggle.addEventListener('click', function () {
        var nextTheme = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        setTheme(nextTheme);
        saveTheme(nextTheme);
    });
}());

(function () {
    var timestamps = document.querySelectorAll('[data-local-datetime]');

    function pad(value) {
        return String(value).padStart(2, '0');
    }

    function formatLocalDateTime(date) {
        return [
            date.getFullYear(),
            pad(date.getMonth() + 1),
            pad(date.getDate())
        ].join('-') + ' ' + [pad(date.getHours()), pad(date.getMinutes())].join(':');
    }

    for (var i = 0; i < timestamps.length; i += 1) {
        var timestamp = timestamps[i];
        var date = new Date(timestamp.getAttribute('datetime'));

        if (!Number.isNaN(date.getTime())) {
            timestamp.textContent = formatLocalDateTime(date);
            timestamp.title = 'UTC: ' + timestamp.getAttribute('datetime');
        }
    }
}());

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
        if (expanded) {
            section.classList.add('is-open');
        } else {
            section.classList.remove('is-open');
        }
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
    var buttons = document.querySelectorAll('[data-completion-button]');

    if (!panels.length) {
        return;
    }

    function setPanelOpen(panel, open) {
        panel.style.display = open ? '' : 'none';
        panel.setAttribute('aria-hidden', open ? 'false' : 'true');
        if (panel.parentNode) {
            if (open) {
                panel.parentNode.classList.add('is-open');
            } else {
                panel.parentNode.classList.remove('is-open');
            }
        }
    }

    function scrollToTop() {
        window.scrollTo(0, 0);
    }

    function scrollPanelCardIntoView(panel) {
        var card = panel.closest ? panel.closest('.task-card') : panel.parentNode;
        var target = card || panel;

        if (target.scrollIntoView) {
            target.scrollIntoView();
        }
    }

    function openPanelById(targetId) {
        var targetPanel = document.getElementById(targetId);
        var shouldOpen;

        if (!targetPanel || !targetPanel.hasAttribute('data-completion-panel')) {
            return;
        }

        shouldOpen = targetPanel.style.display === 'none' || targetPanel.getAttribute('aria-hidden') === 'true';

        for (var i = 0; i < panels.length; i += 1) {
            setPanelOpen(panels[i], shouldOpen && panels[i] === targetPanel);
        }

        if (shouldOpen) {
            scrollPanelCardIntoView(targetPanel);
        } else {
            scrollToTop();
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
            if (isCompletionHash && panels[i].id === targetId) {
                scrollPanelCardIntoView(panels[i]);
            }
        }
    }

    for (var buttonIndex = 0; buttonIndex < buttons.length; buttonIndex += 1) {
        var button = buttons[buttonIndex];
        button.addEventListener('click', function () {
            openPanelById(this.getAttribute('data-completion-target'));
        });
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

    function focusFirstEditorField(popup) {
        var field = popup.querySelector('.editor-panel input:not([type="hidden"]), .editor-panel textarea, .editor-panel select');

        if (!field) {
            return;
        }

        window.setTimeout(function () {
            field.focus();
            if (field.select) {
                field.select();
            }
        }, 0);
    }

    for (var i = 0; i < popups.length; i += 1) {
        var popup = popups[i];
        popup.addEventListener('toggle', function () {
            if (this.open) {
                closeAllExcept(this);
                focusFirstEditorField(this);
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
