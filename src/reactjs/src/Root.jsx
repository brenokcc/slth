import React from "react";
import { Rows, Timeline } from "./Viewer";
import { Form } from "./Form";
import { QuerySet } from "./QuerySet";
import { Object as Object2, Fieldset, Field, Section, Group } from "./Viewer";
import { Statistics } from "./Statistics";
import { Color } from "./Theme";
import { Application } from "./Application";
import { Response, request, apiurl } from "./Request";
import { IconSet } from "./Icon";
import {
  Image,
  Banner,
  Map,
  Steps,
  QrCode,
  Badge,
  Status,
  Progress,
  Boxes,
  Shell,
  FileLink,
  Grid,
  FilePreview,
  Counter,
} from "./Library";

var root;
var COMPONENT_REGISTRY = {};
const APPLICATION_URL = "/api/application/";
const APPLICATION_DATA = localStorage.getItem("application");

function ComponentFactory(props) {
  const func = COMPONENT_REGISTRY[props.data.type];
  return func ? (
    React.createElement(func, { data: props.data })
  ) : (
    <div>{JSON.stringify(props.data)}</div>
  );
}
ComponentFactory.register = function (func) {
  COMPONENT_REGISTRY[func.name.toLowerCase()] = func;
};
ComponentFactory.render = function (element) {
  root = element;
  if (document.location.pathname == "/") {
    localStorage.getItem("token")
      ? window.reload("/app/dashboard/")
      : window.reload("/app/login/");
  } else if (
    document.location.pathname == "/app/login/" &&
    (localStorage.getItem("token") || localStorage.getItem("application"))
  ) {
    localStorage.removeItem("token");
    localStorage.removeItem("application");
    document.location.reload();
  } else {
    window.reload(document.location.href);
  }
};

ComponentFactory.register(Counter);
ComponentFactory.register(Form);
ComponentFactory.register(QuerySet);
ComponentFactory.register(Fieldset);
ComponentFactory.register(Field);
ComponentFactory.register(Object2);
ComponentFactory.register(Section);
ComponentFactory.register(Group);
ComponentFactory.register(Statistics);
ComponentFactory.register(Image);
ComponentFactory.register(Banner);
ComponentFactory.register(Map);
ComponentFactory.register(Steps);
ComponentFactory.register(QrCode);
ComponentFactory.register(Badge);
ComponentFactory.register(Status);
ComponentFactory.register(Progress);
ComponentFactory.register(Color);
ComponentFactory.register(Boxes);
ComponentFactory.register(Shell);
ComponentFactory.register(FileLink);
ComponentFactory.register(FilePreview);
ComponentFactory.register(Response);
ComponentFactory.register(Application);
ComponentFactory.register(IconSet);
ComponentFactory.register(Grid);
ComponentFactory.register(Rows);
ComponentFactory.register(Timeline);

window.addEventListener("popstate", (e) => {
  window.reload(e.currentTarget.location.href);
});

window.reload = function (url) {
  const name = url.split("/app/")[1].split("/")[0];
  if (COMPONENT_REGISTRY[name]) {
    request("GET", apiurl(url), function (data) {
      root.render(<ComponentFactory data={{ type: name, data: data }} />);
    });
  } else {
    if (url != document.location.href) {
      window.history.pushState({ url: url }, "", url);
    }
    if (APPLICATION_DATA) {
      window.application = JSON.parse(APPLICATION_DATA);
      request("GET", apiurl(url), function (content) {
        window.application.content = content;
        root.render(
          <ComponentFactory key={Math.random()} data={window.application} />
        );
      });
    } else {
      request("GET", APPLICATION_URL, function callback(data) {
        window.application = data;
        localStorage.setItem("application", JSON.stringify(window.application));
        request("GET", apiurl(url), function (content) {
          window.application.content = content;
          root.render(
            <ComponentFactory key={Math.random()} data={window.application} />
          );
        });
      });
    }
  }
};

window.load = function (url) {
  if (url.indexOf(window.origin) >= 0 || url.startsWith("/")) {
    if (url != document.location.href && url != document.location.pathname) {
      window.history.pushState({ url: url }, "", url);
    }
    request("GET", apiurl(url), function (data) {
      window.loaddata(data);
    });
  } else {
    document.location.href = url;
  }
};

export { ComponentFactory };
export default ComponentFactory;
