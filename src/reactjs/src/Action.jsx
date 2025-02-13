import { useState } from "react";
import { openDialog } from "./Modal";
import { toLabelCase } from "./Utils";
import { Icon } from "./Icon";
import "./Root";
import { appurl } from "./Request";
import { Theme } from "./Theme";
import StyleSheet from "./StyleSheet";

function Action(props) {
  const id = props.id || Math.random();
  const [label, setLabel] = useState(props.data.name);

  StyleSheet(`
    .action{
      padding: 12px;
      text-decoration: none;
      white-space: nowrap;
      border-radius: 5px;
      margin: 5px;
      min-width: 50px;
    }
  `)

  function onClick(e) {
    e.preventDefault();
    var url = props.data.url;
    if (props.data.urlfunc) url = props.data.urlfunc();
    if (props.onClick) {
      if (label) setLabel("Aguarde....");
      props.onClick(e);
    } else {
      if (props.data.modal == false) {
        window.load(appurl(url));
        //document.location.href = url;
      } else {
        openDialog(url);
      }
    }
  }

  function renderContent() {
    if (props.strech) {
      return props.data.name;
    } else {
      if (props.data.icon) {
        if (props.compact || !props.data.name || window.innerWidth < 800) {
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
  }

  function render() {
    var style = {
      lineHeight: props.data.icon ? "4rem" : "auto",
    };
    if (props.primary) {
      style.backgroundColor = Theme.colors.primary;
      style.color = "white";
    }
    if (props.default) {
      style.border = "solid 1px " + Theme.colors.primary;
      style.color = Theme.colors.primary;
    }
    if (props.style) {
      Object.keys(props.style).map(function (k) {
        style[k] = props.style[k];
      });
    }
    return (
      <a
        id={id}
        className="action"
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

  StyleSheet(`
    .dropdown > div {
      cursor: pointer;
    }
    .dropdown ul{
      padding: 0px;
      position: absolute;
      width: 150px;
      left: 0px;
      text-align: center;
      background-color: white;
      box-shadow: 15px 15px 10px -15px #DDD;
      display: none;
    }
    .dropdown li{
      list-style-type: none;
      padding: 10px;
    }
  `)

  function getListElement(e) {
    var dropdown = e.target.parentNode.querySelector(".dropdown ul");
    if (dropdown == null) {
      dropdown = e.target.parentNode.parentNode.querySelector(".dropdown ul");
    }
    if (dropdown == null) {
      dropdown =
        e.target.parentNode.parentNode.parentNode.querySelector(".dropdown ul");
    }
    return dropdown;
  }
  function onClick(e) {
    const dropdown = getListElement(e);
    if (dropdown.style.display == "block") {
      dropdown.style.display = "none";
    } else {
      const rect = e.target.getBoundingClientRect();
      // the user clicks in the icon
      document
        .querySelectorAll(".dropdown ul")
        .forEach((dropdown) => (dropdown.style.display = "none"));
      dropdown.style.left = rect.left - 150 + rect.width + "px";
      dropdown.style.display = "block";
    }
  }
  function onMouseLeave(e) {
    // the user leaves the LI or A tag
    const dropdown = getListElement(e);
    dropdown.style.display = "none";
  }
  function render() {
    return (
      <div className="dropdown">
        <div
          onClick={onClick}
          data-label={toLabelCase(props.dataLabel)}
        >
          {props.children}
        </div>
        {props.actions && props.actions.length > 0 && (
          <ul onMouseLeave={onMouseLeave}>
            {props.actions.map((action) => (
              <li key={Math.random()}>
                <Action data={action} style={{ padding: 0, whiteSpace: "normal" }} />
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }
  return render();
}

export { Action, Dropdown };
export default { Action };
