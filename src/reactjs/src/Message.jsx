import { React } from "react";
import ReactDOM from "react-dom/client";
import Icon from "./Icon";
import Theme from "./Theme";
import Link from "./Link";

function Message(props) {
  function render() {
    const style = {
      position: "fixed",
      color: props.isError ? "white" : "var(--success-color)",
      backgroundColor: props.isError ? "#e52207" : "var(--success-background)",
      width: 300,
      top: 10,
      left: (window.innerWidth - 320) / 2,
      padding: 15,
      border: "var(--success-border)"
    };
    return (
      <div style={style}>
        <Icon
          icon={props.isError ? "xmark-circle" : "circle-check"}
          style={{ marginRight: 5 }}
        />
        {props.text}
      </div>
    );
  }
  return render();
}

function showMessage(text, isError = false) {
  const div = document.createElement("div");
  div.classList.add("message");
  ReactDOM.createRoot(document.body.appendChild(div)).render(
    <Message text={text} isError={isError} />
  );
  setTimeout(function () {
    div.remove();
  }, 10000);
}

function hideMessages() {
  document.querySelectorAll(".message").forEach(function (div) {
    div.remove();
  });
}

function Info(props) {
  function render() {
    const style = {
      color: Theme.colors.info,
      backgroundColor: Theme.background.info,
      padding: 20,
      display: "flex",
      justifyContent: "space-between",
      marginBottom: 10,
    };
    return (
      <div style={style}>
        <div>{props.data.text}</div>
        {props.children && <div>{props.children}</div>}
      </div>
    );
  }
  return render();
}

function Instruction(props) {
  function render() {
    const style = {
      color: Theme.colors.info,
      backgroundColor: Theme.background.info,
      padding: 20,
      display: "flex",
      justifyContent: "space-between",
      marginTop: 10,
      marginBottom: 10,
    };
    return (
      <div style={style}>
        <div>
          <Icon
            icon="info-circle"
            style={{ color: Theme.colors.info, marginRight: 20 }}
          />
          {props.data.text}
        </div>
        {props.children && <div>{props.children}</div>}
      </div>
    );
  }
  return render();
}

function Todo(props) {
  function render() {
    const style = {
      color: Theme.colors.info,
      backgroundColor: Theme.background.info,
      padding: 20,
      display: "flex",
      justifyContent: "space-between",
      marginTop: 10,
      marginBottom: 10,
    };
    return props.data.map(function (item) {
      return (
        <div key={Math.random()} style={style}>
          <div>
            <Icon
              icon="warning"
              style={{ color: Theme.colors.info, marginRight: 20 }}
            />
            Há ação pendente de execução. Para executá-la, clique em <strong>
              <Link modal={item.modal} href={item.url}>{item.title.toLowerCase()}</Link>
            </strong>.
          </div>
        </div>
      );
    });
  }
  return render();
}

export { showMessage, hideMessages, Message, Info, Instruction, Todo };
export default Message;
