import { useState, useEffect } from "react";
import { ComponentFactory } from "./Root.jsx";
import { request } from "./Request.jsx";
import { format } from "./Formatter.jsx";
import { Action } from "./Action.jsx";
import { Link } from "./Link.jsx";
import { GridLayout } from "./Layout";
import toLabelCase from "./Utils";

function Field(props) {
  function render() {
    if (props.data.url) {
      return <WrappedField data={props.data} />;
    } else {
      return <StaticField data={props.data} />;
    }
  }
  return render();
}

function StaticField(props) {
  function render() {
    const style = {
      minWidth: props.width + "%",
      marginTop: 5,
      marginBottom: 5,
    };
    return (
      <div style={style}>
        <strong>{props.data.label}</strong>
        <br></br>
        {format(props.data.value)}
      </div>
    );
  }
  return render();
}

function WrappedField(props) {
  const id = Math.random();
  const [data, setData] = useState(props.data);

  function loadData(url) {
    request("GET", url, function (data) {
      setData(data);
    });
  }

  function render() {
    window[id] = () => loadData(props.data.url);
    return (
      <div className={props.data.url && "reloadable"} id={id}>
        <StaticField data={data} width={100} />
      </div>
    );
  }

  return render();
}

function Fieldset(props) {
  const id = Math.random();
  const [content, setContent] = useState(props.data);

  function renderTitle() {
    return <Subtitle data={content} />;
  }

  function renderContent() {
    if (Array.isArray(content.data)) {
      if (content.data.length == 0) {
        return <div>Nenhum registro encontrado.</div>;
      }
      return content.data.map(function (item) {
        if (Array.isArray(item)) {
          return (
            <GridLayout width={300} key={Math.random()}>
              {item.map((field) => (
                <Field
                  key={Math.random()}
                  data={field}
                  width={100 / item.length}
                />
              ))}
            </GridLayout>
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
    request("GET", url, function (data) {
      setContent(data);
    });
  }

  function render() {
    if (props.data.url) {
      window[id] = () => loadContent(props.data.url);
      return (
        <div className={props.data.url && "reloadable"} id={id}>
          {renderTitle()}
          {renderContent()}
        </div>
      );
    } else {
      return (
        <div>
          {renderTitle()}
          {renderContent()}
        </div>
      );
    }
  }
  return render();
}

function ObjectActions(props) {
  const id = Math.random();
  const [data, setData] = useState(props.data.actions);

  function getUrl() {
    const sep = props.data.url.indexOf("?") < 0 ? "?" : "&";
    return props.data.url + sep + "only=actions";
  }

  function loadData() {
    request("GET", getUrl(), function (data) {
      setData(data);
    });
  }

  function render() {
    window[id] = () => loadData();
    return (
      <div className="reloadable" id={id}>
        {data.map(function (action) {
          return <Action key={Math.random()} data={action} default />;
        })}
      </div>
    );
  }

  return render();
}

function Title(props) {
  function render() {
    const div = {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "baseline",
    };
    const h1 = { margin: 0 };
    return (
      <div style={div}>
        {props.data.title && (
          <h1 style={h1} data-label={toLabelCase(props.data.title)}>
            {props.data.title}
          </h1>
        )}
        <ObjectActions data={props.data} />
      </div>
    );
  }
  return render();
}

function Subtitle(props) {
  function render() {
    const div = {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "baseline",
    };
    const h2 = { marginBottom: 0, marginTop: 15 };
    return (
      <div style={div}>
        {props.data.title && (
          <h2 style={h2} data-label={toLabelCase(props.data.title)}>
            {props.data.title}
          </h2>
        )}
        {props.data.actions.length > 0 && (
          <div>
            {props.data.actions.map(function (action) {
              return <Action key={Math.random()} data={action} default />;
            })}
          </div>
        )}
      </div>
    );
  }
  return render();
}

//<div>{JSON.stringify(props.data.data)}</div>
function Object(props) {
  function renderTitle() {
    return <Title data={props.data} />;
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
    return <Subtitle data={props.data} />;
  }

  function renderContent() {
    const style = { backgroundColor: "white" };
    return props.data.data.map(function (item, i) {
      return (
        <div style={style}>
          <ComponentFactory key={Math.random()} data={item} />
        </div>
      );
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
          marginBottom: 20,
        }}
      >
        {props.data.map(function (item, i) {
          return (
            <Link
              key={Math.random()}
              href={item.url}
              style={{
                padding: 5,
                fontWeight: active == i ? "bold" : "normal",
                borderBottom:
                  active == i ? "solid 3px #2670e8" : "solid 3px inherite",
                textDecoration: "none",
                color: "#0c326f",
                margin: 15,
              }}
              onClick={function (e) {
                e.preventDefault();
                setActive(i);
                props.loadContent(item.url);
              }}
            >
              {item.title}
            </Link>
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
    return (
      props.data.title != "Top" && (
        <h2 data-label={toLabelCase(props.data.title)}>{props.data.title}</h2>
      )
    );
  }

  function renderTabs() {
    return <Tabs data={props.data.data} loadContent={loadContent} />;
  }

  function renderContent() {
    var clone = { ...content };
    clone.title = null;
    const style = { padding: 0 };
    return (
      <div style={style}>
        <ComponentFactory key={Math.random()} data={clone} />
      </div>
    );
  }

  function renderSeparator() {
    const style = {
      width: "50%",
      margin: "auto",
      border: "solid 0.5px #DDD",
      marginTop: 30,
      marginBottom: 30,
    };
    return <div style={style}></div>;
  }

  function loadContent(url) {
    request("GET", url, function (data) {
      setContent(data);
    });
  }

  function render() {
    window[id] = () => loadContent(content.url);
    return (
      props.data.data.length > 0 && (
        <div className="reloadable" id={id}>
          {renderTitle()}
          {renderTabs()}
          {renderContent()}
          {renderSeparator()}
        </div>
      )
    );
  }
  return render();
}

export { Fieldset, Field, Object, Section, Group };
export default Object;
