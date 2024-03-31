import { useState, useEffect } from "react";
import { ComponentFactory } from "./Factory";
import request from "./Request.jsx";

function Application(props) {
  const [content, setContent] = useState();

  function renderNavbar() {
    const style = {
      display: "flex",
      width: "100%",
      justifyContent: "space-between",
    };
    return (
      <div>
        <div style={style}>
          <div>
            <a href="/">{props.data.navbar.title}</a>
          </div>
          <div>Menu do Usuário</div>
        </div>
      </div>
    );
  }
  function renderContent() {
    return content == null ? (
      <div>Loading...</div>
    ) : (
      <ComponentFactory data={content} />
    );
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
      </>
    );
  }
  return render();
}

export { Application };
export default Application;
