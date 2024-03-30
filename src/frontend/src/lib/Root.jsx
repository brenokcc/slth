import { ComponentFactory } from "./Factory";
import { Form } from "./Form";
import { QuerySet } from "./QuerySet";
import { Object, Fieldset, Section, Group, Dimension } from "./Viewer";
import { Statistics } from "./Statistics";

ComponentFactory.register("form", (data) => <Form data={data} />);
ComponentFactory.register("queryset", (data) => <QuerySet data={data} />);
ComponentFactory.register("fieldset", (data) => <Fieldset data={data} />);
ComponentFactory.register("object", (data) => <Object data={data} />);
ComponentFactory.register("section", (data) => <Section data={data} />);
ComponentFactory.register("group", (data) => <Group data={data} />);
ComponentFactory.register("dimension", (data) => <Dimension data={data} />);
ComponentFactory.register("statistics", (data) => <Statistics data={data} />);

function Root(props) {
  console.log(props.data);
  return (
    <>
      <ComponentFactory data={props.data} />
    </>
  );
}

export default Root;
