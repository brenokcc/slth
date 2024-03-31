import { useState } from "react";
import { openDialog } from "./Modal";

function Action(props) {
  const url = "/app/" + props.data.url.split("/api/")[1];

  function onClick(e) {
    e.preventDefault();
    props.data.modal == false
      ? (document.location.href = url)
      : openDialog(url);
  }

  function render() {
    const style = { padding: 5, textDecoration: "none" };
    return (
      <a href={url} onClick={onClick} style={style}>
        {props.data.name}
      </a>
    );
  }
  return render();
}

function Dropdown(props) {
  const [active, setActive] = useState(false);
  function onClick() {
    setActive(true);
  }
  function onMouseLeave() {
    setActive(false);
  }
  function render() {
    const url = {
      position: "absolute",
      width: 150,
      right: 0,
      textAlign: "center",
      border: "solid 1px #DDD",
    };
    const li = { listStyleType: "none", padding: 5 };
    return (
      <>
        <div onClick={onClick} style={{ cursor: "pointer" }}>
          {props.children}
        </div>
        {active && props.actions && props.actions.length > 0 && (
          <ul style={url} onMouseLeave={onMouseLeave}>
            {props.actions.map((action) => (
              <li style={li} key={Math.random()}>
                <Action data={action} />
              </li>
            ))}
          </ul>
        )}
      </>
    );
  }
  return render();
}

export { Action, Dropdown };
export default { Action };
