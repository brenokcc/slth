"use strict";

self.addEventListener("push", function (event) {
  var tokens = event.data.text().split(">>>");
  const title = tokens[0];
  const options = {
    body: tokens[1],
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", function (event) {
  event.notification.close();
  //event.waitUntil(clients.openWindow('http://localhost:5173/app/dashboard/'));
});
