import { useState, useEffect } from "react";
import { ComponentFactory } from "./Factory";
import { request, appurl } from "./Request.jsx";
import { showMessage } from "./Message";
import { Dropdown } from "./Action.jsx";
import { Selector } from "./Form.jsx";

function Application(props) {
  const [content, setContent] = useState();

  useEffect(() => {
    const message = localStorage.getItem("message");
    if (message) {
      localStorage.removeItem("message");
      showMessage(message);
    }
    setTimeout(
      () => (document.getElementById("application").style.display = "block"),
      500
    );
  }, []);

  function renderNavbar() {
    const style = {
      display: "flex",
      width: "100%",
      justifyContent: "space-between",
      boxShadow: "0px 15px 10px -15px #DDD",
    };
    const selector = {
      choices: "/api/search/",
      help_text: null,
      label: null,
      mask: null,
      name: "search",
      required: false,
      type: "choice",
    };
    return props.data.navbar ? (
      <div style={style}>
        <div style={{ padding: 20 }}>
          <a href="/">{props.data.navbar.title}</a>
        </div>
        <div style={{ display: "flex", alignItems: "center" }}>
          <Selector
            data={selector}
            style={{ padding: 10 }}
            onSelect={(option) => (document.location.href = appurl(option.id))}
          />
          <div style={{ padding: 20 }}>
            <Dropdown actions={props.data.navbar.actions}>
              {props.data.navbar.user}
            </Dropdown>
          </div>
        </div>
      </div>
    ) : null;
  }
  function renderContent() {
    const style = { minHeight: 400, margin: 20 };
    return content == null ? (
      <div style={style}>Loading...</div>
    ) : (
      <div style={style}>
        <ComponentFactory data={content} />
      </div>
    );
  }
  function renderFooter() {
    return props.data.footer ? (
      <div align="center">
        <div>Todos os direitos reservados</div>
        <div>{props.data.footer.version}</div>
      </div>
    ) : null;
  }
  function render() {
    if (content == null) {
      const url = document.location.pathname.replace("/app/", "/api/");
      request("GET", url, function callback(data) {
        setContent(data);
      });
    }
    return (
      <div id="application" style={{ display: "none" }}>
        {renderNavbar()}
        {renderContent()}
        {renderFooter()}
      </div>
    );
  }
  return render();
}

export { Application };
export default Application;
