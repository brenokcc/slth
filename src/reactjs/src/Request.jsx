import { showMessage } from "./Message";

function Response(props) {
  const data = props.data;
  if (data.store) store(data.store);
  if (data.redirect && data.redirect.length > 2) {
    if (data.message) localStorage.setItem("message", data.message);
    document.location.href = appurl(data.redirect);
  } else {
    if (data.message) showMessage(data.message);
  }
}

function store(data){
  Object.keys(data).map(function (k) {
    if (data[k]){
      localStorage.setItem(k, data[k]);
      if(k=='token'){
        document.cookie = "token="+data[k]+";path=/"
      }
    }
    else{
      localStorage.removeItem(k, data[k]);
      if(k=='token'){
        document.cookie = "token=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
      }
    }
  });
}

function buildurl(path) {
  return path;
}

function apiurl(path) {
  return buildurl(path.replace("/app/", "/api/"));
}

function appurl(path) {
  return path.replaceAll("/api/", "/app/");
}

function request(method, path, callback, data) {
  const token = localStorage.getItem("token");
  var headers = { Accept: "application/json", 'TZ': Intl.DateTimeFormat().resolvedOptions().timeZone };
  if (token) headers["Authorization"] = "Token " + token;
  const url = apiurl(path);
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
      if (contentType == "application/json"){
        return response.text();
      } else if (
        contentType.indexOf("text") < 0 ||
        contentType.indexOf("csv") >= 0 ||
        contentType.indexOf("pdf") >= 0
      ) {
        return response.arrayBuffer();
      } else {
        response.text();
      }
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
        contentType.indexOf("csv") >= 0 ||
        contentType.indexOf("pdf") >= 0
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
      } else {
        if (callback) callback(result, httpResponse);
      }
    });
}

export { Response, apiurl, appurl, request, store };
export default request;
