import { useState, useEffect } from "react";
import { ComponentFactory } from "./Factory";
import request from "./Request.jsx";
import { showMessage } from "./Message";

function Application(props) {
  const [content, setContent] = useState();

  useEffect(() => {
    const message = localStorage.getItem("message");
    if (message) {
      localStorage.removeItem("message");
      showMessage(message);
    }
  }, []);

  function logout(e) {
    e.preventDefault();
    localStorage.removeItem("token");
    document.location.href = "/app/login/";
  }

  function renderNavbar() {
    const style = {
      display: "flex",
      width: "100%",
      justifyContent: "space-between",
    };
    return props.data.navbar ? (
      <div>
        <div style={style}>
          <div>
            <a href="/">{props.data.navbar.title}</a>
          </div>
          <div style={{ display: "flex" }}>
            <div>
              <a href="#" onClick={logout}>
                Sair
              </a>
            </div>
            <div>Menu do Usuário</div>
          </div>
        </div>
      </div>
    ) : null;
  }
  function renderContent() {
    return content == null ? (
      <div style={{ minHeight: 400 }}>Loading...</div>
    ) : (
      <ComponentFactory data={content} />
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
      <>
        {renderNavbar()}
        {renderContent()}
        {renderFooter()}
      </>
    );
  }
  return render();
}

export { Application };
export default Application;
