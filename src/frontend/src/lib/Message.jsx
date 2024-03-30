import { createRoot } from "react-dom/client";

function Message(props) {
  function render() {
    const style = {
      position: "fixed",
      color: "white",
      backgroundColor: props.isError ? "red" : "green",
      width: 300,
      top: 10,
      left: (screen.width - 300) / 2,
      padding: 10,
    };
    return <div style={style}>{props.text}</div>;
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

export { showMessage, hideMessages };
export default Message;
