import ReactDOM from "react-dom/client";
import ComponentFactory from "slth";
// import ComponentFactory from "/Users/breno/Documents/Workspace/slth/src/reactjs/src/Root";

function Hello(props) {
  return <p>Hello {props.data.name}!</p>;
}

ComponentFactory.register("hello-world", (data) => <Hello data={data} />);

ComponentFactory.render(ReactDOM.createRoot(document.getElementById("root")));
