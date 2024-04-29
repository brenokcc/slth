import { React } from "react";
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
  return func ? func(props.data) : <div>{JSON.stringify(props.data)}</div>;
}
ComponentFactory.register = function (type, func) {
  COMPONENT_REGISTRY[type] = func;
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

ComponentFactory.register("counter", (data) => <Counter data={data} />);
ComponentFactory.register("form", (data) => <Form data={data} />);
ComponentFactory.register("queryset", (data) => <QuerySet data={data} />);
ComponentFactory.register("fieldset", (data) => <Fieldset data={data} />);
ComponentFactory.register("field", (data) => <Field data={data} />);
ComponentFactory.register("object", (data) => <Object2 data={data} />);
ComponentFactory.register("section", (data) => <Section data={data} />);
ComponentFactory.register("group", (data) => <Group data={data} />);
ComponentFactory.register("statistics", (data) => <Statistics data={data} />);
ComponentFactory.register("image", (data) => <Image data={data} />);
ComponentFactory.register("banner", (data) => <Banner data={data} />);
ComponentFactory.register("map", (data) => <Map data={data} />);
ComponentFactory.register("steps", (data) => <Steps data={data} />);
ComponentFactory.register("qrcode", (data) => <QrCode data={data} />);
ComponentFactory.register("badge", (data) => <Badge data={data} />);
ComponentFactory.register("status", (data) => <Status data={data} />);
ComponentFactory.register("progress", (data) => <Progress data={data} />);
ComponentFactory.register("color", (data) => <Color data={data} />);
ComponentFactory.register("boxes", (data) => <Boxes data={data} />);
ComponentFactory.register("shell", (data) => <Shell data={data} />);
ComponentFactory.register("file_link", (data) => <FileLink data={data} />);
ComponentFactory.register("file_viewer", (data) => <FilePreview data={data} />);
ComponentFactory.register("response", (data) => <Response data={data} />);
ComponentFactory.register("application", (data) => <Application data={data} />);
ComponentFactory.register("iconset", (data) => <IconSet data={data} />);
ComponentFactory.register("grid", (data) => <Grid data={data} />);
ComponentFactory.register("rows", (data) => <Rows data={data} />);
ComponentFactory.register("timeline", (data) => <Timeline data={data} />);

window.addEventListener("popstate", (e) => {
  window.reload(e.currentTarget.location.href);
});

window.reload = function (url) {
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
