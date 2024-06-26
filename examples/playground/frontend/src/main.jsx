import ReactDOM from "react-dom/client";
import ComponentFactory from "/Users/breno/Documents/Workspace/slth/src/reactjs/src/Root";
//import "slth/dist/style.css";

function Hello(props) {
  return <p>Hello {props.data.name}!</p>;
}

ComponentFactory.register("hello-world", (data) => <Hello data={data} />);

ComponentFactory.render(ReactDOM.createRoot(document.getElementById("root")));
