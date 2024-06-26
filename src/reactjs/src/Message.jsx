import { React } from "react";
import ReactDOM from "react-dom/client";
import Icon from "./Icon";
import Theme from "./Theme";

function Message(props) {
  function render() {
    const style = {
      position: "fixed",
      color: "white",
      backgroundColor: props.isError ? "#e52207" : Theme.colors.success,
      width: 300,
      top: 10,
      left: (window.innerWidth - 320) / 2,
      padding: 15,
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
  }, 3000);
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
      marginTop: 10,
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

export { showMessage, hideMessages, Message, Info };
export default Message;
