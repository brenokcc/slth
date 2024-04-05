import { useEffect } from "react";
import { ComponentFactory } from "./Factory";
import { appurl } from "./Request.jsx";
import { showMessage } from "./Message";
import { Dropdown } from "./Action.jsx";
import { Selector } from "./Form.jsx";

function Application(props) {
  useEffect(() => {
    const message = localStorage.getItem("message");
    if (message) {
      localStorage.removeItem("message");
      showMessage(message);
    }
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
    return (
      <div style={style} id="container">
        <ComponentFactory data={props.data.content} />
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
    return (
      <div id="application">
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
