import { React } from "react";
import ReactDOM from "react-dom/client";
import { useState, useEffect } from "react";
import { ComponentFactory } from "./Root.jsx";
import { hideMessages } from "./Message";
import { Icon } from "./Icon";
import { request, apiurl } from "./Request.jsx";
import { Action } from "./Action.jsx";

function createLayer() {
  if (document.querySelector(".layer") == null) {
    ReactDOM.createRoot(
      document.body.appendChild(document.createElement("div"))
    ).render(<Layer />);
  }
}

function openDialog(url, reloader) {
  hideMessages();
  createLayer();
  window.reloader = reloader;
  var dialogs = document.getElementsByTagName("dialog");
  for (var i = 0; i < dialogs.length; i++) dialogs[i].style.display = "none";
  ReactDOM.createRoot(
    document.body.appendChild(document.createElement("div"))
  ).render(<Dialog url={apiurl(url)} />);
}

function openIFrameDialog(url) {
  hideMessages();
  createLayer();
  ReactDOM.createRoot(
    document.body.appendChild(document.createElement("div"))
  ).render(<IDialog url={apiurl(url)} />);
}

function closeDialog(message) {
  if (message != null) showMessage(message);
  var dialogs = document.getElementsByTagName("dialog");
  for (var i = 0; i < dialogs.length; i++) {
    if (i == dialogs.length - 1) {
      var dialog = dialogs[i];
      dialog.close();
      dialog.classList.remove("opened");
      dialog.remove();
      if (i == 0) {
        document.querySelector(".layer").style.display = "none";
        if (window.reloader) window.reloader();
      } else {
        dialogs[i - 1].style.display = "block";
      }
    }
  }
}

function openActionDialog(actions) {
  hideMessages();
  createLayer();
  ReactDOM.createRoot(
    document.body.appendChild(document.createElement("div"))
  ).render(<ActionDialog actions={actions} />);
}

function Layer(props) {
  const style = {
    backgroundColor: "black",
    bottom: 0,
    left: 0,
    position: "fixed",
    right: 0,
    top: 0,
    opacity: 0.7,
    display: "none",
  };
  return (
    <div
      className="layer"
      onClick={function () {
        closeDialog();
      }}
      style={style}
    ></div>
  );
}

function Dialog(props) {
  const [data, setdata] = useState(null);
  const [key, setkey] = useState(0);

  useEffect(() => {
    open(apiurl(props.url));
    document.querySelector(".layer").style.display = "block";
  }, []);

  function open(url) {
    request("GET", apiurl(url), function (data) {
      setdata(data);
      setkey(key + 1);
    });
  }

  function content() {
    const style = { maxWidth: 800 };
    const close = { textAlign: "right", cursor: "pointer", marginTop: -15 };
    if (data) {
      return (
        <div style={style}>
          <div style={close}>
            <Icon icon="x" onClick={() => closeDialog()} />
          </div>
          <ComponentFactory data={data} />
        </div>
      );
    }
  }

  const style = {
    minWidth: window.innerWidth < 800 ? "calc(100% - 60px)" : 800,
    display: data ? "block" : "none",
    maxWidth: 800,
    top: window.scrollY + 40,
    border: 0,
  };

  return (
    <dialog style={style} key={key}>
      {content()}
    </dialog>
  );
}

function IDialog(props) {
  var key = Math.random();

  useEffect(() => {
    document.querySelector(".layer").style.display = "block";
    var dialog = document.getElementById(key);
    dialog.style.top = document.documentElement.scrollTop + 100;
  }, []);

  function render() {
    const style = {
      minWidth: window.innerWidth < 800 ? "calc(100% - 60px)" : 800,
      display: "block",
      maxWidth: 800,
      top: window.scrollY + 40,
      border: 0,
    };
    const close = { float: "right", cursor: "pointer", marginTop: -20 };
    return (
      <dialog style={style} id={key}>
        <div style={close}>
          <Icon icon="x" onClick={() => closeDialog()} />
        </div>
        <iframe
          src={apiurl(props.url)}
          width="100%"
          height={500}
          style={{ border: 0 }}
        ></iframe>
      </dialog>
    );
  }

  return render();
}

function ActionDialog(props) {
  const key = Math.random();

  useEffect(() => {
    document.querySelector(".layer").style.display = "block";
  }, []);

  function content() {
    const style = {
      width: "100%",
      borderBottom: "solid 1px #DDDD",
      padding: 20,
    };
    return (
      <div align="center" style={{}}>
        {props.actions.map(function (action) {
          return (
            <div key={Math.random()} style={style} onClick={close}>
              <Action data={action} strech />
            </div>
          );
        })}
      </div>
    );
  }

  function close() {
    const dialog = document.getElementById(key);
    dialog.close();
    dialog.classList.remove("opened");
    dialog.remove();
    document.querySelector(".layer").style.display = "none";
  }

  const style = {
    width: "auto",
    display: "block",
    position: "fixed",
    bottom: 0,
    border: 0,
    padding: 0,
  };

  return (
    <dialog id={key} style={style}>
      {content()}
    </dialog>
  );
}

export { openDialog, openIFrameDialog, closeDialog, Layer, openActionDialog };
export default Layer;
