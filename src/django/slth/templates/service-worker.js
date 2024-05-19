'use strict';

self.addEventListener('push', function (event) {
    console.log('[Service Worker] Push Received.');
    console.log(event.data);
    console.log(`[Service Worker] Push had this data: "${event.data.text()}"`);
    const data = JSON.parse(event.data.text())
    console.log(data);
    const options = {
        body: data.message,
        icon: data.icon,
        data: {url: data.url}
    };
    event.waitUntil(self.registration.showNotification(data.title, options));
});

self.addEventListener('notificationclick', function (event) {
    console.log('[Service Worker] Notification click Received.');
    console.log(event.notification);
    var url = event.notification.data && event.notification.data.url;
    if (url) {
        url = url.replace('/api/', '/app/');
        event.waitUntil(clients.matchAll({ type: 'window' }).then(function (clientList) {
            var matchFound = false;
            for (var client of clientList) {
                var clientUrl = new URL(client.url);
                var targetUrl = new URL(url.startsWith("/") ? clientUrl.origin + url : url);
                if (clientUrl.host === targetUrl.host && 'focus' in client) {
                    client.navigate(url);
                    client.focus();
                    matchFound = true;
                }
            }
            if (!matchFound) event.waitUntil(clients.openWindow(url));
        }));
    }
    event.notification.close();
});

