import { useState, useEffect } from "react";
import { ComponentFactory } from "./Factory";
import { appurl } from "./Request.jsx";
import { showMessage } from "./Message";
import { Dropdown } from "./Action.jsx";
import { Selector } from "./Form.jsx";
import { SystemLayout } from "./Layout.jsx";
import { Menu } from "./Menu.jsx";

function Content(props) {
  const [data, setData] = useState(props.data);

  window.loaddata = (data) => setData(data);

  function render() {
    const style = { minHeight: 400, margin: 20 };
    return (
      <div style={style} id="container">
        <ComponentFactory key={Math.random()} data={data} />
      </div>
    );
  }

  return render();
}

function Application(props) {
  useEffect(() => {
    const message = localStorage.getItem("message");
    if (message) {
      localStorage.removeItem("message");
      showMessage(message);
    }
  }, []);

  function renderHeader() {
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
  function renderAside() {
    return window.application.menu && <Menu />;
  }
  function renderMain() {
    return <Content data={props.data.content} />;
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
      <SystemLayout
        header={renderHeader()}
        aside={renderAside()}
        main={renderMain()}
        footer={renderFooter()}
      />
    );
  }
  return render();
}

export { Application };
export default Application;
