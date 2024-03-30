import { useState, useEffect } from "react";
import { ComponentFactory } from "./Factory";
import { request } from "./Request.jsx";

function Field(props) {
  function render() {
    const style = { width: props.width + "%", marginTop: 5, marginBottom: 5 };
    return (
      <>
        <div style={style}>
          <strong>{props.data.label}</strong>
          <br></br>
          <span>{props.data.value}</span>
        </div>
      </>
    );
  }
  return render();
}

function Fieldset(props) {
  const id = Math.random();
  const [content, setContent] = useState(props.data);

  function getTitle() {
    return <h2>{content.title}</h2>;
  }

  function getContent() {
    if (Array.isArray(content.data)) {
      return content.data.map(function (item) {
        if (Array.isArray(item)) {
          return (
            <div key={Math.random()} style={{ display: "flex" }}>
              {item.map((field) => (
                <Field
                  key={Math.random()}
                  data={field}
                  width={100 / item.length}
                />
              ))}
            </div>
          );
        } else {
          return (
            <div key={Math.random()}>
              <Field data={item} width={100} />
            </div>
          );
        }
      });
    } else {
      return <ComponentFactory data={content.data} />;
    }
  }

  function loadContent(url) {
    console.log(url);
    request("GET", url, function (data) {
      console.log(data);
      setContent(data);
    });
  }

  function render() {
    window[id] = () => loadContent(props.data.url);
    return (
      <div className="reloadable" id={id}>
        {getTitle()}
        {getContent()}
      </div>
    );
  }
  return render();
}
//<div>{JSON.stringify(props.data.data)}</div>
function Object(props) {
  function renderTitle() {
    return <h1>{props.data.title}</h1>;
  }

  function renderContent() {
    return props.data.data.map(function (item, i) {
      return <ComponentFactory key={Math.random()} data={item} />;
    });
  }

  function render() {
    return (
      <>
        {renderTitle()}
        {renderContent()}
      </>
    );
  }
  return render();
}

function Section(props) {
  function renderTitle() {
    return <h2>{props.data.title}</h2>;
  }

  function renderContent() {
    return props.data.data.map(function (item, i) {
      return <ComponentFactory key={Math.random()} data={item} />;
    });
  }

  function render() {
    return (
      <>
        {renderTitle()}
        {renderContent()}
      </>
    );
  }
  return render();
}

function Tabs(props) {
  const [active, setActive] = useState(0);
  function render() {
    return (
      <div
        style={{
          display: "inline-block",
          textAlign: "center",
          width: "100%",
          margin: "auto",
        }}
      >
        {props.data.map(function (item, i) {
          return (
            <a
              key={Math.random()}
              href={item.url}
              style={{
                padding: 5,
                fontWeight: active == i ? "bold" : "normal",
                textDecoration: active == i ? "underline" : "none",
              }}
              onClick={function (e) {
                setActive(i);
                e.preventDefault();
                props.loadContent(item.url);
              }}
            >
              {item.title}
            </a>
          );
        })}
      </div>
    );
  }
  return render();
}

function Group(props) {
  var id = Math.random();
  const [content, setContent] = useState(props.data.data[0]);

  function renderTitle() {
    return <h2>{props.data.title}</h2>;
  }

  function renderTabs() {
    return <Tabs data={props.data.data} loadContent={loadContent} />;
  }

  function renderContent() {
    var clone = { ...content };
    clone.title = null;
    return <ComponentFactory key={Math.random()} data={clone} />;
  }

  function loadContent(url) {
    request("GET", url, function (data) {
      setContent(data);
    });
  }

  function render() {
    window[id] = () => loadContent(content.url);
    return (
      <div className="reloadable" id={id}>
        {renderTitle()}
        {renderTabs()}
        {renderContent()}
      </div>
    );
  }
  return render();
}

function Dimension(props) {
  var id = Math.random();
  const [content, setContent] = useState(props.data.data[0]);

  function renderTitle() {
    return <h2>{props.data.title}</h2>;
  }

  function renderTabs() {
    return <Tabs data={props.data.data} loadContent={loadContent} />;
  }

  function renderContent() {
    var clone = { ...content };
    clone.title = null;
    return <ComponentFactory key={Math.random()} data={clone} />;
  }

  function loadContent(url) {
    request("GET", url, function (data) {
      setContent(data);
    });
  }

  function render() {
    window[id] = () => loadContent(content.url);
    return (
      <div className="reloadable" id={id}>
        {renderTitle()}
        {renderTabs()}
        {renderContent()}
      </div>
    );
  }
  return render();
}

export { Fieldset, Object, Section, Group, Dimension };
export default Object;
