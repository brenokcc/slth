import React from "react";
import ReactDOM from "react-dom/client";
import Root from "./lib/Root.jsx";
import request from "./lib/Request.jsx";

const URL = "/api/application/";

request("GET", URL, function callback(data) {
  console.log(data);
  ReactDOM.createRoot(document.getElementById("root")).render(
    <Root data={data} />
  );
});
