import { ComponentFactory } from "./Factory";
import { Form } from "./Form";
import { QuerySet } from "./QuerySet";
import { Object, Fieldset, Field, Section, Group, Dimension } from "./Viewer";
import { Statistics } from "./Statistics";
import { Image, Banner, Map, Steps, QrCode, Badge, Status } from "./Library";

ComponentFactory.register("form", (data) => <Form data={data} />);
ComponentFactory.register("queryset", (data) => <QuerySet data={data} />);
ComponentFactory.register("fieldset", (data) => <Fieldset data={data} />);
ComponentFactory.register("field", (data) => <Field data={data} />);
ComponentFactory.register("object", (data) => <Object data={data} />);
ComponentFactory.register("section", (data) => <Section data={data} />);
ComponentFactory.register("group", (data) => <Group data={data} />);
ComponentFactory.register("dimension", (data) => <Dimension data={data} />);
ComponentFactory.register("statistics", (data) => <Statistics data={data} />);
ComponentFactory.register("image", (data) => <Image data={data} />);
ComponentFactory.register("banner", (data) => <Banner data={data} />);
ComponentFactory.register("map", (data) => <Map data={data} />);
ComponentFactory.register("steps", (data) => <Steps data={data} />);
ComponentFactory.register("qrcode", (data) => <QrCode data={data} />);
ComponentFactory.register("badge", (data) => <Badge data={data} />);
ComponentFactory.register("status", (data) => <Status data={data} />);

function Root(props) {
  console.log(props.data);
  return (
    <>
      <ComponentFactory data={props.data} />
    </>
  );
}

export default Root;
