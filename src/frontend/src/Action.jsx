import { useState } from "react";
import { openDialog } from "./Modal";
import { toLabelCase } from "./Utils";
import { Icon } from "./Icon";
import "./Root";
import { appurl } from "./Request";

function Action(props) {
  const id = props.id || Math.random();
  const [label, setLabel] = useState(props.data.name);

  function onClick(e) {
    e.preventDefault();
    if (props.onClick) {
      if (label) setLabel("Aguarde....");
      props.onClick(e);
    } else {
      if (props.data.modal == false) {
        window.load(appurl(props.data.url));
        //document.location.href = url;
      } else {
        openDialog(props.data.url);
      }
    }
  }

  function renderContent() {
    if (props.data.icon) {
      if (props.compact || !props.data.name) {
        return <Icon icon={props.data.icon} />;
      } else {
        return (
          <>
            <Icon icon={props.data.icon} style={{ paddingRight: 10 }} />
            {props.data.name || ""}
          </>
        );
      }
    } else {
      return props.data.name;
    }
  }

  function render() {
    var style = {
      padding: 12,
      textDecoration: "none",
      //whiteSpace: "nowrap",
      borderRadius: 5,
      margin: 5,
    };
    if (props.primary) {
      style.backgroundColor = "#1351b4";
      style.color = "white";
    }
    if (props.default) {
      style.border = "solid 1px #1351b4";
      style.color = "#1351b4";
    }
    if (props.style) {
      Object.keys(props.style).map(function (k) {
        style[k] = props.style[k];
      });
    }
    return (
      <a
        id={id}
        href={appurl(props.data.url) || "#"}
        onClick={onClick}
        style={style}
        data-label={toLabelCase(props.data.name)}
      >
        {renderContent()}
      </a>
    );
  }
  return render();
}

function Dropdown(props) {
  function getListElement(e) {
    var dropdown = e.target.parentNode.querySelector(".dropdown");
    if (dropdown == null) {
      dropdown = e.target.parentNode.parentNode.querySelector(".dropdown");
    }
    if (dropdown == null) {
      dropdown =
        e.target.parentNode.parentNode.parentNode.querySelector(".dropdown");
    }
    return dropdown;
  }
  function onClick(e) {
    const rect = e.target.getBoundingClientRect();
    // the user clicks in the icon
    const dropdown = getListElement(e);
    document
      .querySelectorAll(".dropdown")
      .forEach((dropdown) => (dropdown.style.display = "none"));
    dropdown.style.left = rect.left - 150 + rect.width + "px";
    dropdown.style.display = "block";
  }
  function onMouseLeave(e) {
    // the user leaves the LI or A tag
    const dropdown = getListElement(e);
    dropdown.style.display = "none";
  }
  function render() {
    const ul = {
      padding: 0,
      position: "absolute",
      width: 150,
      left: 0,
      textAlign: "center",
      backgroundColor: "white",
      boxShadow: "15px 15px 10px -15px #DDD",
      display: "none",
    };
    const li = { listStyleType: "none", padding: 10 };
    return (
      <>
        <div onClick={onClick} style={{ cursor: "pointer" }}>
          {props.children}
        </div>
        {props.actions && props.actions.length > 0 && (
          <ul style={ul} onMouseLeave={onMouseLeave} className="dropdown">
            {props.actions.map((action) => (
              <li style={li} key={Math.random()}>
                <Action data={action} style={{ padding: 0 }} />
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
