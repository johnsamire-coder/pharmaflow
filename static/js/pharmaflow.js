// ============================================
// PharmaFlow SaaS - Main JS
// ============================================

document.addEventListener('DOMContentLoaded', function() {

    // Sidebar Toggle (Mobile)
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('pfSidebar');
    const overlay = document.getElementById('pfOverlay');

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            overlay.classList.toggle('show');
        });
    }

    if (overlay) {
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        });
    }

    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.pf-alert[data-auto-dismiss]');
    alerts.forEach(function(alert) {
        const delay = parseInt(alert.dataset.autoDismiss) || 5000;
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 300);
        }, delay);
    });

    // Tooltips init
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(el) {
        return new bootstrap.Tooltip(el);
    });

    // Confirm dialogs
    document.querySelectorAll('[data-confirm]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // Format numbers
    document.querySelectorAll('.pf-number').forEach(function(el) {
        const num = parseFloat(el.textContent);
        if (!isNaN(num)) {
            el.textContent = num.toLocaleString('ar-EG', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
    });

    // Active sidebar link
    const currentPath = window.location.pathname;
    document.querySelectorAll('.pf-menu-item a').forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.closest('.pf-menu-item').classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.closest('.pf-menu-item').classList.add('active');
        }
    });

    console.log('PharmaFlow UI initialized ✅');
});
