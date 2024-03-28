import { ComponentFactory } from "./Factory";
import { Layer } from "./Modal";
import { Form } from "./Form";

ComponentFactory.register("form", (data) => <Form data={data} />);

function Root(props) {
  return (
    <>
      <ComponentFactory data={props.data} />
      <Layer />
    </>
  );
}

export default Root;
