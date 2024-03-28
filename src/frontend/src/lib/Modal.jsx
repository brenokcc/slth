import { createRoot } from "react-dom/client";
import { useState, useEffect } from "react";
import { ComponentFactory } from "./Factory";
import { Icon } from "./Icon";

function URL(url) {
  return url ? url.replace("/api/", "/app/") : url;
}

function openDialog(url, reloader) {
  hideMessages();
  window.reloader = reloader;
  var dialogs = document.getElementsByTagName("dialog");
  for (var i = 0; i < dialogs.length; i++) dialogs[i].style.display = "none";
  createRoot(document.body.appendChild(document.createElement("div"))).render(
    <Dialog url={URL(url)} />
  );
}

function openIFrameDialog(url) {
  hideMessages();
  createRoot(document.body.appendChild(document.createElement("div"))).render(
    <IDialog url={URL(url)} />
  );
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
        var layer = document.querySelector(".layer");
        if (layer) layer.style.display = "none";
        if (window.reloader) window.reloader();
      } else {
        dialogs[i - 1].style.display = "block";
      }
    }
  }
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
    open(URL(props.url));
    var layer = document.querySelector(".layer");
    if (layer) layer.style.display = "block";
  }, []);

  function open(url) {
    request("GET", URL(url), function (data) {
      setdata(data);
      setkey(key + 1);
    });
  }

  function content() {
    const style = { float: "right", cursor: "pointer" };
    if (data) {
      return (
        <div>
          <div style={style}>
            <Icon icon="x" onClick={() => closeDialog()} />
          </div>
          <ComponentFactory data={data} />
          <a
            className="btn"
            onClick={() => openDialog("/app/cadastrarpessoa/")}
          >
            XXXX
          </a>
        </div>
      );
    }
  }

  return (
    <dialog
      className={"dialog " + (window.innerWidth > 600 ? "small" : "big")}
      key={key}
      style={{
        display: data ? "block" : "none",
        maxWidth: "90%",
        top: window.scrollY + 40,
      }}
    >
      {content()}
    </dialog>
  );
}

function IDialog(props) {
  var key = Math.random();

  useEffect(() => {
    var layer = document.querySelector(".layer");
    if (layer) layer.style.display = "block";
    var dialog = document.getElementById(key);
    $(dialog).css("top", document.documentElement.scrollTop + 100);
  }, []);

  return (
    <dialog
      className={"dialog " + (window.innerWidth > 600 ? "small" : "big")}
      id={key}
    >
      <iframe src={URL(props.url)} width="100%" height={500}></iframe>
    </dialog>
  );
}

export { openDialog, openIFrameDialog, closeDialog, Layer };
export default Layer;
