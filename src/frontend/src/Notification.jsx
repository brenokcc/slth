import { Icon } from "./Icon.jsx";
import { request } from "./Request.jsx";

function PushWebNotification(props) {
  var subscriptionJson;
  function urlB64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding)
      .replace(/\-/g, "+")
      .replace(/_/g, "/");
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }
  function onClick() {
    if ("serviceWorker" in navigator && "PushManager" in window) {
      //console.log('Service Worker and Push is supported');
      navigator.serviceWorker
        .register("/service-worker.js", {
          type: "module",
        })
        .then(function (swRegistration) {
          0 / 0;
          console.log("Service Worker is registered");
          const applicationServerKey = urlB64ToUint8Array(
            "BLoLJSopQbe04v_zpegJmayhH2Px0EGzrFIlM0OedSOTYsMpO5YGmHOxbpPXdM09ttIuDaDTI86uC85JXZPpEtA"
          );
          swRegistration.pushManager
            .subscribe({
              userVisibleOnly: true,
              applicationServerKey: applicationServerKey,
            })
            .then(function (subscription) {
              console.log(subscription);
              subscriptionJson = JSON.stringify(subscription);
              console.log(subscriptionJson);
              if (subscription) {
                alert("Notificação ativida com sucesso.");
              } else {
                alert("Problema ao ativar notificações.");
                return;
              }
              var data = new FormData();
              data.append("subscription", subscriptionJson);
              request(
                "POST",
                "/api/pushsubscribe/",
                function (data) {
                  console.log(data);
                },
                data
              );
            })
            .catch(function (err) {
              alert("Problema ao tentar ativar notificações.");
              console.log("Failed to subscribe the user: ", err);
            });
        })
        .catch(function (error) {
          alert("Erro");
          console.error("Service Worker Error", error);
        });
    } else {
      alert("Push messaging is not supported");
    }
  }
  function render() {
    return <Icon onClick={onClick} icon="bell" style={{ cursor: "pointer" }} />;
  }
  return render();
}

export { PushWebNotification };
export default PushWebNotification;
