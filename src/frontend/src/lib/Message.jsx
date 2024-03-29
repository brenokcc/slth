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
  createRoot(document.body.appendChild(div)).render(
    <Message text={text} isError={isError} />
  );
  setTimeout(function () {
    div.remove();
  }, 3000);
}

export { showMessage };
export default Message;
