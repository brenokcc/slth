const API_URL = "http://localhost:8000";
function request(method, url, callback, data) {
  const token = localStorage.getItem("token");
  var headers = { Accept: "application/json" };
  if (token && url.indexOf("/logout/") == -1)
    headers["Authorization"] = "Token " + token;
  url = url.replace(document.location.origin, "");
  url = url.replace("/app/", "/api/");
  if (url.indexOf(API_URL) == -1) url = API_URL + url;
  var params = { method: method, headers: new Headers(headers), ajax: 1 };
  if (data) params["body"] = data;
  var httpResponse = null;
  var contentType = null;
  fetch(url, params)
    .then(function (response) {
      httpResponse = response;
      contentType = httpResponse.headers.get("Content-Type");
      if (contentType == "application/json") return response.text();
      else if (
        contentType.indexOf("text") < 0 ||
        contentType.indexOf("csv") >= 0
      )
        return response.arrayBuffer();
      else response.text();
    })
    .then((result) => {
      if (contentType == "application/json") {
        var data = JSON.parse(result || "{}");
        if (callback) callback(data, httpResponse);
      } else if (
        contentType.indexOf("text") < 0 ||
        contentType.indexOf("csv") >= 0
      ) {
        var file = window.URL.createObjectURL(
          new Blob([new Uint8Array(result)], { type: contentType })
        );
        var a = document.createElement("a");
        a.href = file;
        if (contentType.indexOf("excel") >= 0) a.download = "Download.xls";
        else if (contentType.indexOf("pdf") >= 0) a.download = "Download.pdf";
        else if (contentType.indexOf("zip") >= 0) a.download = "Download.zip";
        else if (contentType.indexOf("json") >= 0) a.download = "Download.json";
        else if (contentType.indexOf("csv") >= 0) a.download = "Download.csv";
        else if (contentType.indexOf("png") >= 0) a.download = "Download.png";
        document.body.appendChild(a);
        a.click();
        if (callback) callback({}, httpResponse);
      } else {
        if (callback) callback(result, httpResponse);
      }
    });
}

function hideMessages() {}

function showMessage(message) {
  alert(message);
}
