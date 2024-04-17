import ReactDOM from "react-dom/client";
import ComponentFactory from "/Users/breno/Documents/Workspace/slth/src/reactjs/src/Root";
//import "slth/dist/style.css";

function Rota(props) {
  return (
    <div>
      Minha Rota {props.data.a} {props.data.b}
    </div>
  );
}

ComponentFactory.register("xxx", (data) => <Rota data={data} />);

ComponentFactory.render(ReactDOM.createRoot(document.getElementById("root")));
