# Clear Cache Instructions

If you're experiencing 404 errors for `books.ts` or module loading failures, follow these steps:

## Quick Fix (Recommended)

1. **Open Browser DevTools** (F12)
2. **Go to Application tab** (Chrome) or **Storage tab** (Firefox)
3. **Click "Service Workers"** in the left sidebar
4. **Click "Unregister"** for any registered service workers
5. **Go to "Cache Storage"** and delete all caches
6. **Hard refresh** the page (Ctrl+Shift+R or Cmd+Shift+R)

## Alternative: Clear via Console

Open browser console and run:
```javascript
// Unregister all service workers
navigator.serviceWorker.getRegistrations().then(registrations => {
  registrations.forEach(registration => registration.unregister());
});

// Clear all caches
caches.keys().then(keys => {
  keys.forEach(key => caches.delete(key));
});

// Reload page
location.reload(true);
```

## Restart Dev Server

After clearing cache, restart your Vite dev server:
```bash
# Stop the server (Ctrl+C)
# Then restart
npm run dev
```
