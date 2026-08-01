(() => {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/sw.js').catch((error) => {
        console.error('Service worker registration failed:', error);
      });
    });
  }

  let deferredPrompt = null;

  const showInstallBanner = () => {
    if (document.getElementById('pwa-install-banner')) return;

    const banner = document.createElement('div');
    banner.id = 'pwa-install-banner';
    banner.style.position = 'fixed';
    banner.style.left = '50%';
    banner.style.bottom = '18px';
    banner.style.transform = 'translateX(-50%)';
    banner.style.zIndex = '9999';
    banner.style.width = 'calc(100% - 32px)';
    banner.style.maxWidth = '520px';
    banner.style.background = 'rgba(255,255,255,0.98)';
    banner.style.border = '1px solid rgba(95, 126, 168, 0.18)';
    banner.style.borderRadius = '18px';
    banner.style.boxShadow = '0 24px 60px rgba(15, 23, 42, 0.14)';
    banner.style.padding = '16px 18px';
    banner.style.display = 'grid';
    banner.style.gridTemplateColumns = '1fr auto';
    banner.style.gap = '12px';
    banner.style.alignItems = 'center';
    banner.style.fontFamily = '"Cairo", "Arial", sans-serif';
    banner.style.color = '#1f2d3d';

    const text = document.createElement('div');
    text.innerHTML = '<strong>ثبّت التطبيق على جوالك</strong><br>للوصول السريع والسهل إلى لوحة التحكم والطلاب.';
    text.style.lineHeight = '1.5';
    text.style.fontSize = '15px';

    const actions = document.createElement('div');
    actions.style.display = 'flex';
    actions.style.gap = '10px';
    actions.style.flexWrap = 'wrap';
    actions.style.justifyContent = 'flex-end';

    const installButton = document.createElement('button');
    installButton.type = 'button';
    installButton.textContent = 'تثبيت التطبيق';
    installButton.style.border = 'none';
    installButton.style.background = '#5f7ea8';
    installButton.style.color = '#fff';
    installButton.style.padding = '11px 16px';
    installButton.style.borderRadius = '12px';
    installButton.style.fontWeight = '700';
    installButton.style.cursor = 'pointer';
    installButton.style.minWidth = '120px';

    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.textContent = 'إغلاق';
    closeButton.style.border = '1px solid rgba(95, 126, 168, 0.25)';
    closeButton.style.background = 'transparent';
    closeButton.style.color = '#5f7ea8';
    closeButton.style.padding = '11px 14px';
    closeButton.style.borderRadius = '12px';
    closeButton.style.fontWeight = '700';
    closeButton.style.cursor = 'pointer';

    installButton.addEventListener('click', async () => {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      if (outcome === 'accepted') {
        banner.remove();
      }
      deferredPrompt = null;
    });

    closeButton.addEventListener('click', () => {
      banner.remove();
    });

    actions.appendChild(installButton);
    actions.appendChild(closeButton);
    banner.appendChild(text);
    banner.appendChild(actions);

    document.body.appendChild(banner);
  };

  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    deferredPrompt = event;
    showInstallBanner();
  });

  window.addEventListener('appinstalled', () => {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) banner.remove();
  });
})();
