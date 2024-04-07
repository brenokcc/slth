import ReactDOM from "react-dom/client";
import { ComponentFactory } from "./Factory";
import { Form } from "./Form";
import { QuerySet } from "./QuerySet";
import { Object, Fieldset, Field, Section, Group } from "./Viewer";
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
} from "./Library";

const APPLICATION_URL = "/api/application/";
const APPLICATION_DATA = localStorage.getItem("application");
const ROOT = ReactDOM.createRoot(document.getElementById("root"));

ComponentFactory.register("form", (data) => <Form data={data} />);
ComponentFactory.register("queryset", (data) => <QuerySet data={data} />);
ComponentFactory.register("fieldset", (data) => <Fieldset data={data} />);
ComponentFactory.register("field", (data) => <Field data={data} />);
ComponentFactory.register("object", (data) => <Object data={data} />);
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
ComponentFactory.register("link", (data) => <FileLink data={data} />);
ComponentFactory.register("response", (data) => <Response data={data} />);
ComponentFactory.register("application", (data) => <Application data={data} />);
ComponentFactory.register("iconset", (data) => <IconSet data={data} />);
ComponentFactory.register("grid", (data) => <Grid data={data} />);

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
      ROOT.render(
        <ComponentFactory key={Math.random()} data={window.application} />
      );
    });
  } else {
    request("GET", APPLICATION_URL, function callback(data) {
      window.application = data;
      localStorage.setItem("application", JSON.stringify(window.application));
      request("GET", apiurl(url), function (content) {
        window.application.content = content;
        ROOT.render(
          <ComponentFactory key={Math.random()} data={window.application} />
        );
      });
    });
  }
};

window.load = function (url) {
  if (url != document.location.href) {
    window.history.pushState({ url: url }, "", url);
  }
  request("GET", apiurl(url), function (data) {
    window.loaddata(data);
  });
};

export default window;
