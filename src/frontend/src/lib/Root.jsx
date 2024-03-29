import { ComponentFactory } from "./Factory";
import { Form } from "./Form";
import { QuerySet } from "./QuerySet";

ComponentFactory.register("form", (data) => <Form data={data} />);
ComponentFactory.register("queryset", (data) => <QuerySet data={data} />);

function Root(props) {
  console.log(props.data);
  return (
    <>
      <ComponentFactory data={props.data} />
    </>
  );
}

export default Root;
