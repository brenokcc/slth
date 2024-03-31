import React from "react";
import ReactDOM from "react-dom/client";
import Root from "./lib/Root.jsx";
import request from "./lib/Request.jsx";

const URL = "/api/application/";

const application = localStorage.getItem("application");
if (application) {
  const data = JSON.parse(application);
  ReactDOM.createRoot(document.getElementById("root")).render(
    <Root data={data} />
  );
} else {
  request("GET", URL, function callback(data) {
    localStorage.setItem("application", JSON.stringify(data));
    ReactDOM.createRoot(document.getElementById("root")).render(
      <Root data={data} />
    );
  });
}
