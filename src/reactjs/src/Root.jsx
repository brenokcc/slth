import React from "react";
import { Cards, Rows, Timeline } from "./Viewer";
import { Form } from "./Form";
import { QuerySet } from "./QuerySet";
import { Object as Object2, Fieldset, Field, Section, Group } from "./Viewer";
import { Statistics } from "./Statistics";
import { Color } from "./Theme";
import { Application } from "./Application";
import { Response, request, apiurl } from "./Request";
import { IconSet } from "./Icon";
import { WebConf } from "./Media";
import { ZoomMeet } from "./Meeting";
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
  Indicators,
  Scheduler,
  Html,
} from "./Library";
import Text from "./Text";

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
ComponentFactory.register = function (func, name) {
  COMPONENT_REGISTRY[name.toLowerCase()] = func;
};
ComponentFactory.render = function (element) {
  root = element;
  if (document.location.pathname == "/") {
    localStorage.getItem("token")
      ? window.reload("/app/dashboard/")
      : window.reload("/app/home/");
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

ComponentFactory.register(Counter, "Counter");
ComponentFactory.register(Form, "Form");
ComponentFactory.register(QuerySet, "QuerySet");
ComponentFactory.register(Fieldset, "Fieldset");
ComponentFactory.register(Field, "Field");
ComponentFactory.register(Object2, "Object");
ComponentFactory.register(Section, "Section");
ComponentFactory.register(Group, "Group");
ComponentFactory.register(Statistics, "Statistics");
ComponentFactory.register(Image, "Image");
ComponentFactory.register(Banner, "Banner");
ComponentFactory.register(Map, "Map");
ComponentFactory.register(Steps, "Steps");
ComponentFactory.register(QrCode, "QrCode");
ComponentFactory.register(Badge, "Badge");
ComponentFactory.register(Status, "Status");
ComponentFactory.register(Progress, "Progress");
ComponentFactory.register(Color, "Color");
ComponentFactory.register(Boxes, "Boxes");
ComponentFactory.register(Indicators, "Indicators");
ComponentFactory.register(Shell, "Shell");
ComponentFactory.register(FileLink, "FileLink");
ComponentFactory.register(FilePreview, "FilePreview");
ComponentFactory.register(Response, "Response");
ComponentFactory.register(Application, "Application");
ComponentFactory.register(IconSet, "IconSet");
ComponentFactory.register(Grid, "Grid");
ComponentFactory.register(Rows, "Rows");
ComponentFactory.register(Cards, "Cards");
ComponentFactory.register(Timeline, "Timeline");
ComponentFactory.register(Scheduler, "Scheduler");
ComponentFactory.register(WebConf, "WebConf");
ComponentFactory.register(Text, "Text");
ComponentFactory.register(Html, "Html");
ComponentFactory.register(ZoomMeet, "ZoomMeet");

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
      window.scrollTo({ top: 0,  behavior: 'smooth' });
    });
  } else {
    document.location.href = url;
  }
};

export { ComponentFactory };
export default ComponentFactory;
