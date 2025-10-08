import { useState, useEffect } from "react";
import { ComponentFactory } from "./Root";
import { appurl } from "./Request.jsx";
import { showMessage } from "./Message";
import { Dropdown, Action } from "./Action.jsx";
import { Selector } from "./Form.jsx";
import { Menu } from "./Menu.jsx";
import { Icon } from "./Icon.jsx";
import { PushWebNotification } from "./Notification.jsx";
import toLabelCase from "./Utils.jsx";
import Link from "./Link.jsx";
import { Theme, ThemeToggle } from "./Theme";
import detectSwipe from "./Gestures.jsx";

function Floating(props) {
  function render() {
    if (window.innerWidth > 800) return;
    const style = {
      position: "fixed",
      display: "flex",
      width: 50,
      height: 50,
      backgroundColor: "var(--primary-background)",
      color: "var(--default-background)",
      right: 10,
      borderRadius: "50%",
      cursor: "pointer",
    };
    const icon = { paddingLeft: 14, paddingTop: 12, fontSize: "1.8rem" };
    return (
      <>
        <div
          style={{ ...style, ...{ bottom: 100 } }}
          onClick={() => history.back()}
        >
          <Icon icon="arrow-left" style={icon} />
        </div>
        <div
          style={{ ...style, ...{ bottom: 20 } }}
          onClick={() => window.scrollTo({ top: 0,  behavior: 'smooth' })}
        >
          <Icon icon="arrow-up" style={icon} />
        </div>
      </>
    );
  }
  return render();
}

function Content(props) {
  const [data, setData] = useState(props.data);

  window.loaddata = (data) => setData(data);

  function render() {
    const style = { minHeight: 400, margin: window.innerWidth > 800 ? 20 : 5 };
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
      if (menu) {
        menu.style.display = window.innerWidth < SMALL_WIDTH ? "none" : "inline-block";
      }
    });

    detectSwipe(document.querySelector('main'), function(e, direction){
      console.log(e, direction);
    });

  }, []);

  function toggleMenu() {
    const menu = document.querySelector("aside");
    if(menu){
      menu.style.display = menu.style.display == "none" ? "inline-block" : "none";
      localStorage.setItem('menuDisplay', menu.style.display);
    }
  }

  function onLogoClick(e) {
    const link = e.target.tagName == "A" ? e.target : e.target.closest('a');
    e.preventDefault();
    window.load(link.href);
  }

  function renderHeader() {
    const style = {
      display: "flex",
      width: "100%",
      justifyContent: "space-between",
      //boxShadow: "0px 15px 10px -15px #DDD",
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
      icon: "search",
    };
    return props.data.navbar ? (
      <div style={style}>
        <div style={{ padding: 20 }}>
          {props.data.menu && props.data.menu.items.length > 0 && (
            <Icon
              icon="navicon"
              style={{ fontSize: "1.5rem", marginRight: 10, cursor: "pointer" }}
              onClick={toggleMenu}
            />
          )}
          <a
            className="brand"
            href="/app/home/"
            onClick={onLogoClick}
            style={{ fontSize: "1.5rem", textDecoration: "none" }}
          >
            {props.data.navbar.logo && (
              <img
                src={props.data.navbar.logo}
                height={20}
                style={{ marginRight: 10 }}
              />
            )}
            <span>{props.data.navbar.title}</span>
          </a>
          <div>{props.data.navbar.subtitle}</div>
        </div>
        <div style={{ display: "flex", alignItems: "center" }}>
          {props.data.navbar.adder.length > 0 && (
            <div style={{ padding: 10 }}>
              <Dropdown
                actions={props.data.navbar.adder}
                position={{}}
                dataLabel="plus"
                name="plus"
              >
                <Icon icon="plus" style={{ cursor: "pointer", color: Theme.colors.primary }}/>
              </Dropdown>
            </div>
          )}
          {props.data.navbar.name && 
          <div style={{ padding: 10 }}>
            Olá, { props.data.navbar.name }!
          </div>
          }
          <div style={{ padding: 10 }}>
            <PushWebNotification />
          </div>
          <div style={{ padding: 10 }}>
            <ThemeToggle />
          </div>

          {props.data.navbar.toolbar && window.innerWidth > 800 &&
            props.data.navbar.toolbar.length > 0 &&
            (
              <div className="toolbar">
                {props.data.navbar.toolbar.map(function (action) {
                  return (
                   
                      <Action key={Math.random()} data={action} compact/>
                 
                  );
                })}
              </div>
            )
          }

          {props.data.oauth &&
            props.data.oauth.length > 0 &&
            props.data.navbar.user == null &&
            props.data.oauth.map(function (oauth) {
              return <Link key={Math.random()} href={oauth.url} style={{marginRight: 10}}>{oauth.label}</Link>;
            })}

          {props.data.navbar.tools.length > 0 && (
            <div style={{ padding: 10 }}>
              <Dropdown
                actions={props.data.navbar.tools}
                position={{}}
                dataLabel="tools"
                name="tools"
              >
                <Icon icon="tools" style={{ cursor: "pointer", color: Theme.colors.primary }}/>
              </Dropdown>
            </div>
          )}
          {props.data.navbar.settings.length > 0 && (
            <div style={{ padding: 10 }}>
              <Dropdown
                actions={props.data.navbar.settings}
                position={{}}
                dataLabel="gear"
                name="gear"
              >
                <Icon icon="gear" style={{ cursor: "pointer", color: Theme.colors.primary }}/>
              </Dropdown>
            </div>
          )}
          {window.innerWidth > 800 && props.data.navbar.user && props.data.navbar.search && (
            <div>
              <Selector
                data={selector}
                style={{ padding: 10 }}
                onSelect={(option) =>
                  (document.location.href = appurl(option.id))
                }
              />
            </div>
          )}
          {props.data.navbar.user && props.data.navbar.usermenu.length > 0 && (
            <div style={{ padding: 10 }}>
              <Dropdown
                actions={props.data.navbar.usermenu}
                position={{}}
                dataLabel={toLabelCase(props.data.navbar.user)}
                name="usermenu"
              >
                <img
                  src={props.data.navbar.photo || "/static/images/user.svg"}
                  style={{
                    width: 30,
                    height: 30,
                    borderRadius: "50%",
                    objectFit: "cover",
                    backgroundColor: "var(--primary-background)",
                  }}
                />
              </Dropdown>
            </div>
          )}
        </div>
      </div>
    ) : null;
  }
  function renderAside() {
    return (
      window.application.menu &&
      window.application.menu.items.length > 0 && (
        <aside
          style={{
            verticalAlign: "top",
            maxWidth: "350px",
            minWidth: "350px",
            display: localStorage.getItem('menuDisplay') || window.innerWidth < SMALL_WIDTH ? "none" : "block",
            float: "left",
            minHeight: window.innerHeight+"px",
          }}
        >
          <Menu />
        </aside>
      )
    );
  }

  function renderBreadcrumbs() {
    const style = { margin: 15, display: "flex", justifyContent: "space-between" };
    const icon = { color: Theme.colors.primary };
    return (
      props.data.navbar &&
      props.data.navbar.user && (
        <div style={style}>
          <div>
            <Link href="/app/dashboard/" style={{ marginRight: 10 }}>
              <Icon icon="home" style={icon} />
            </Link>
            Área Administrativa
          </div>
          <div title={props.data.navbar.roles}>
            {props.data.navbar.user}
          </div>
        </div>
      )
    );
  }

  function renderTopActions(){
    return (
      <div style={{textAlign: "right"}}>
        {props.data.top &&
            props.data.top.length > 0 &&
            (
              <div className="top">
                {props.data.top.map(function (action) {
                  return (
                   
                      <Action key={Math.random()} data={action} compact={window.innerWidth < 800}/>
                 
                  );
                })}
              </div>
            )
          }
      </div>
    )
  }

  function renderMain() {
    return (
      <main id="main" style={{width:"100%", overflowX:"auto"}}>
        {renderBreadcrumbs()}
        {renderTopActions()}
        <Content data={props.data.content} />
        <footer>{renderFooter()}</footer>
        <Floating />
      </main>
    );
  }
  function renderFooter() {
    const marginBottom = window.innerWidth > 800 ? 300 : 50;
    return props.data.footer ? (
      <div align="center" style={{marginBottom: marginBottom}}>
        <div>
          {window.application.sponsors && window.application.sponsors.length > 0 && (
          <div>
            {window.application.sponsors.map(function (url) {
              return <img key={Math.random()} src={url} style={{height: 30, padding: 5}}/>;
            })}
            </div>)
          }
        </div>
        <div>{"Etc/GMT"+(new Date().getTimezoneOffset()/-60)}</div>
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
            width: "100%",
            minHeight: window.innerHeight - 70,
            display: "flex",
          }}
        >
          {renderAside()}
          {renderMain()}
        </div>
      </div>
    );
  }
  return render();
}

export { Application };
export default Application;
