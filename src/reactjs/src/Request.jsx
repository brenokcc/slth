import { showMessage } from "./Message";

const API_URL =
  import.meta.env.VITE_BACKEND_URL ||
  document.location.origin
    .replace(
      (/\:\d+/i.exec(document.location.origin) || ["|"]).join(""),
      ":8000"
    )
    .replace("frontend", "backend");

function Response(props) {
  return response(props.data);
}

function apiurl(url) {
  if (url.startsWith("/")) url = API_URL + url;
  return url.replace("/app/", "/api/");
}

function appurl(url) {
  return url ? document.location.origin + "/app/" + url.split("/api/")[1] : url;
}

function request(method, url, callback, data) {
  const token = localStorage.getItem("token");
  var headers = { Accept: "application/json" };
  if (token) headers["Authorization"] = "Token " + token;
  url = url.replace(document.location.origin, "");
  url = url.replace(document.location.search, "");
  url = apiurl(url);
  url = url + document.location.search;
  if (url.indexOf(API_URL) == -1) url = API_URL + url;
  var params = {
    method: method,
    headers: new Headers(headers),
    ajax: 1,
  };
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
        if (typeof data == "object" && data.type == "redirect") {
          document.location.href = appurl(data.url);
        } else {
          if (callback) callback(data, httpResponse);
        }
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

function response(data) {
  if (data.store) {
    Object.keys(data.store).map(function (k) {
      if (data.store[k]) localStorage.setItem(k, data.store[k]);
      else localStorage.removeItem(k, data.store[k]);
    });
  }
  if (data.redirect) {
    if (data.message) localStorage.setItem("message", data.message);
    document.location.href = appurl(data.redirect);
  } else {
    if (data.message) showMessage(data.message);
  }
}

export { Response, apiurl, appurl, request, response, API_URL };
export default request;
