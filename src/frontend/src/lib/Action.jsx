import { useState } from "react";
import { openDialog } from "./Modal";
import { toLabelCase } from "./Utils";
import { Icon } from "./Icon";

function Action(props) {
  const id = props.id || Math.random();
  const [label, setLabel] = useState(props.data.name);
  const url = props.data.url
    ? "/app/" + props.data.url.split("/api/")[1]
    : null;

  function onClick(e) {
    e.preventDefault();
    if (props.onClick) {
      if (label) setLabel("Aguarde....");
      props.onClick(e);
    } else {
      props.data.modal == false
        ? (document.location.href = url)
        : openDialog(url);
    }
  }

  function render() {
    var style = {
      padding: 12,
      textDecoration: "none",
      whiteSpace: "nowrap",
      borderRadius: 5,
      backgroundColor: "#1351b4",
      color: "white",
      margin: 5,
    };
    if (props.style) {
      Object.keys(props.style).map(function (k) {
        style[k] = props.style[k];
      });
    }
    return (
      <a
        id={id}
        href={url || "#"}
        onClick={onClick}
        style={style}
        data-label={toLabelCase(props.data.name)}
      >
        {props.data.icon && <Icon icon={props.data.icon} />}
        {label && label}
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
      backgroundColor: "white",
      boxShadow: "0px 15px 10px -15px #DDD",
    };
    const li = { listStyleType: "none", padding: 10 };
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
