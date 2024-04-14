'use strict';

self.addEventListener('push', function (event) {
    console.log('[Service Worker] Push Received.');
    console.log(`[Service Worker] Push had this data: "${event.data.text()}"`);
    var tokens = event.data.text().split('>>>');
    const title = tokens[0]
    const options = {
        body: tokens[1],
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function (event) {
    console.log('[Service Worker] Notification click Received.');
    event.notification.close();
    //event.waitUntil(clients.openWindow('http://petshop.aplicativo.click/app/login/'));
});

