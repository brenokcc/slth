import { Icon } from "./Icon.jsx";
import { request } from "./Request.jsx";
import Theme from "./Theme.jsx";

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
      navigator.serviceWorker
        .getRegistration()
        .then(function (swRegistration) {
          if (swRegistration) {
            const applicationServerKey = urlB64ToUint8Array(
              "BFvGgHYReJWJuSyOChUCEs1VYqZVs3TLJAvSkMW8jVqqgdWVbArBL4Kd6ibPKWlQo8Q3BuWwomybqwzs-1Ic8GU"
            );
            swRegistration.pushManager.getSubscription(function(subscription){
              if(subscription){
                subscription.unsubscribe();
                console.log('unsubscribed');
              }
            })
            swRegistration.pushManager.subscribe({
              userVisibleOnly: true,
              applicationServerKey: applicationServerKey,
            })
            .then(function (subscription) {
              console.log(subscription);
              subscriptionJson = JSON.stringify(subscription);
              console.log(subscriptionJson);
              if (subscription) {
                alert("Notificação ativada com sucesso.");
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
              } else {
                alert("Problema ao ativar notificações.");
                return;
              }
            })
              .catch(function (err) {
                alert("Problema ao tentar ativar notificações.");
                console.log("Failed to subscribe the user: ", err);
              });
          } else {
            console.log("No registered service worker.");
          }
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
    if (
      true || window.Notification == null ||
      window.Notification.permission !== "granted"
    ) {
      return (
        <Icon
          onClick={onClick}
          icon="bell"
          style={{ cursor: "pointer", color: Theme.colors.primary }}
        />
      );
    }
  }
  return render();
}

export { PushWebNotification };
export default PushWebNotification;
