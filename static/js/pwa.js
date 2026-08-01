(() => {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/sw.js').catch((error) => {
        console.error('Service worker registration failed:', error);
      });
    });
  }

  let deferredPrompt = null;

  const showInstallButton = () => {
    if (document.getElementById('pwa-install-btn')) return;

    const button = document.createElement('button');
    button.id = 'pwa-install-btn';
    button.type = 'button';
    button.textContent = 'تثبيت التطبيق';
    button.style.position = 'fixed';
    button.style.left = '16px';
    button.style.bottom = '16px';
    button.style.zIndex = '9999';
    button.style.padding = '12px 16px';
    button.style.border = 'none';
    button.style.borderRadius = '999px';
    button.style.background = '#5f7ea8';
    button.style.color = '#fff';
    button.style.fontWeight = '700';
    button.style.boxShadow = '0 8px 18px rgba(0, 0, 0, 0.18)';
    button.style.cursor = 'pointer';

    button.addEventListener('click', async () => {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      if (outcome === 'accepted') {
        button.remove();
      }
      deferredPrompt = null;
    });

    document.body.appendChild(button);
  };

  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    deferredPrompt = event;
    showInstallButton();
  });

  window.addEventListener('appinstalled', () => {
    const button = document.getElementById('pwa-install-btn');
    if (button) button.remove();
  });
})();
