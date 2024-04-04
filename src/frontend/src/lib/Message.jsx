import { createRoot } from "react-dom/client";
import Icon from "./Icon";

function Message(props) {
  function render() {
    const style = {
      position: "fixed",
      color: "white",
      backgroundColor: props.isError ? "#e52207" : "#168821",
      width: 300,
      top: 10,
      left: (screen.width - 300) / 2,
      padding: 10,
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
  createRoot(document.body.appendChild(div)).render(
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
      color: "#155bcb",
      backgroundColor: "#d4e5ff",
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
            icon="circle-check"
            style={{ color: "#155bcb", marginRight: 20 }}
          />
          {props.data.text}
        </div>
        {props.children && <div>{props.children}</div>}
      </div>
    );
  }
  return render();
}

export { showMessage, hideMessages, Message, Info };
export default Message;
