import { useState, useEffect } from "react";
import { ComponentFactory } from "./Root";
import { appurl } from "./Request.jsx";
import { showMessage } from "./Message";
import { Dropdown } from "./Action.jsx";
import { Selector } from "./Form.jsx";
import { SystemLayout } from "./Layout.jsx";
import { Menu } from "./Menu.jsx";
import { Icon } from "./Icon.jsx";
import { PushWebNotification } from "./Notification.jsx";
import toLabelCase from "./Utils.jsx";

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
  const SMALL_WIDTH = 800;

  useEffect(() => {
    const message = localStorage.getItem("message");
    if (message) {
      localStorage.removeItem("message");
      showMessage(message);
    }
    window.addEventListener("resize", () => {
      const menu = document.querySelector("aside");
      menu.style.display = window.innerWidth < SMALL_WIDTH ? "none" : "block";
    });
  }, []);

  function toggleMenu() {
    const menu = document.querySelector("aside");
    menu.style.display = menu.style.display == "none" ? "block" : "none";
  }

  function renderHeader() {
    const style = {
      display: "flex",
      width: "100%",
      justifyContent: "space-between",
      boxShadow: "0px 15px 10px -15px #DDD",
      overflowX: "hidden",
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
          <Icon
            icon="navicon"
            style={{ fontSize: "1.5rem", marginRight: 10, cursor: "pointer" }}
            onClick={toggleMenu}
          />
          <a href="/" style={{ fontSize: "1.5rem" }}>
            {props.data.navbar.logo && (
              <img src={props.data.navbar.logo} height={20} />
            )}
            {props.data.navbar.title}
          </a>
        </div>
        <div style={{ display: "flex", alignItems: "center" }}>
          {props.data.navbar.adder.length > 0 && (
            <div style={{ padding: 10 }}>
              <Dropdown
                actions={props.data.navbar.adder}
                position={{}}
                dataLabel="plus"
              >
                <Icon icon="plus" />
              </Dropdown>
            </div>
          )}
          <div style={{ padding: 10 }}>
            <PushWebNotification />
          </div>
          {props.data.navbar.tools.length > 0 && (
            <div style={{ padding: 10 }}>
              <Dropdown
                actions={props.data.navbar.tools}
                position={{}}
                dataLabel="tools"
              >
                <Icon icon="tools" />
              </Dropdown>
            </div>
          )}
          {props.data.navbar.settings.length > 0 && (
            <div style={{ padding: 10 }}>
              <Dropdown
                actions={props.data.navbar.settings}
                position={{}}
                dataLabel="gear"
              >
                <Icon icon="gear" />
              </Dropdown>
            </div>
          )}
          {window.innerWidth > 800 && (
            <Selector
              data={selector}
              style={{ padding: 10 }}
              onSelect={(option) =>
                (document.location.href = appurl(option.id))
              }
            />
          )}
          {props.data.navbar.usermenu.length > 0 && (
            <div style={{ padding: 10 }}>
              <Dropdown
                actions={props.data.navbar.usermenu}
                position={{}}
                dataLabel={toLabelCase(props.data.navbar.user)}
              >
                {props.data.navbar.user}
              </Dropdown>
            </div>
          )}
        </div>
      </div>
    ) : null;
  }
  function renderAside() {
    return (
      window.application.menu && (
        <aside
          style={{
            flexGrow: 2,
            maxWidth: "350px",
            minWidth: "350px",
            display: window.innerWidth < SMALL_WIDTH ? "none" : "block",
          }}
        >
          <Menu />
        </aside>
      )
    );
  }
  function renderMain() {
    return (
      <main style={{ flexGrow: 6, minWidth: "400px" }}>
        <Content data={props.data.content} />
        <footer>{renderFooter()}</footer>
      </main>
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
      <div>
        <header>{renderHeader()}</header>
        <div
          style={{
            overflowX: "hide",
            width: "100%",
            display: "flex",
            overflow: "hidden",
            minHeight: window.innerHeight - 70,
          }}
        >
          {renderAside()}
          {renderMain()}
        </div>
      </div>
    );
  }
  return render();
  return render();
}

export { Application };
export default Application;
