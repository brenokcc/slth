import { useEffect } from "react";
import { Icon } from "./Icon";
import { apiurl } from "./Request";

function Html(props) {
  return <div dangerouslySetInnerHTML={{ __html: props.data.content }}></div>;
}

function Banner(props) {
  return <img src={props.data.src} style={{ width: "100%" }} />;
}

function Image(props) {
  return (
    <div style={{ width: "100%", textAlign: "center" }}>
      <img
        src={props.data.src}
        style={{ width: props.data.width, height: props.data.height }}
      />
    </div>
  );
}

function Map(props) {
  return (
    <iframe
      width={props.data.width || "100%"}
      height={props.data.height || "400px"}
      id="gmap_canvas"
      src={
        "https://maps.google.com/maps?q=" +
        props.data.latitude +
        "," +
        props.data.longitude +
        "&t=&z=13&ie=UTF8&iwloc=&output=embed"
      }
      frameBorder="0"
      scrolling="no"
      marginHeight="0"
      marginWidth="0"
    ></iframe>
  );
}

function Steps(props) {
  function renderIcon(step) {
    if (props.data.icon) {
      return step.done ? (
        <Icon style={{ marginTop: 12 }} icon={props.data.icon} />
      ) : (
        <span>&nbsp;</span>
      );
    } else {
      return <div style={{ marginTop: 12 }}>{step.number}</div>;
    }
  }

  function circleStyle(step) {
    return {
      border: "2px solid " + (step.done ? "green" : "#EEE"),
      borderRadius: "50%",
      background: step.done ? "green" : "white",
      color: step.done ? "white" : "black",
      textAlign: "center",
      width: 50,
      height: 50,
      margin: "auto",
      fontSize: "1.5rem",
    };
  }

  function ulStyle(steps) {
    return {
      listStyleType: "none",
      display: "flex",
      justifyContent: "center",
      minWidth: steps.length * 100,
    };
  }

  function render() {
    const container = {
      width: "100%",
      margin: "auto",
      overflowX: "auto",
      "&::WebkitScrollbar": { width: 0 },
    };
    const li = {
      width: 100,
      marginWidth: 100,
      textAlign: "center",
    };
    const divider = {
      position: "relative",
      borderBottom: "2px solid #EEE",
      top: -28,
      width: 45,
      left: 77,
    };
    return (
      <div>
        <div style={container}>
          <ul style={ulStyle(props.data.steps)}>
            {props.data.steps.map((step, i) => (
              <li key={Math.random()} style={li}>
                <div style={circleStyle(step)}>{renderIcon(step)}</div>
                {i < props.data.steps.length - 1 && <div style={divider}></div>}
                <div>{step.name}</div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  }

  return render();
}

function Progress(props) {
  function render() {
    return (
      <span className="progress ">
        <span
          style={{ width: props.data.value + "%" }}
          className={"value " + (props.data.style || "primary")}
        >
          <span className="percentage">{props.data.value}%</span>
        </span>
      </span>
    );
  }
  return render();
}

function Status(props) {
  function render() {
    const colors = {
      success: "green",
      warning: "orange",
      info: "blue",
      danger: "red",
    };
    props.data.color = colors[props.data.style];
    return <Badge data={props.data} />;
  }
  return render();
}

function Badge(props) {
  function render() {
    const style = {
      color: "white",
      width: "fit-content",
      borderRadius: 5,
      textWrap: "nowrap",
      padding: 10,
      whiteSpace: "nowrap",
      backgroundColor: props.data.color,
    };
    return <div style={style}>{props.data.label}</div>;
  }
  return render();
}

function Boxes(props) {
  function render() {
    return props.data.items.length ? (
      <div className="boxes">
        <h2>{props.data.title}</h2>
        <div>
          {props.data.items.map((item) => (
            <a
              key={Math.random()}
              href={apiurl(item.url)}
              className="item"
              data-label={toLabelCase(item.label)}
            >
              <div className={"icon " + (item.style || "primary")}>
                <Icon icon={item.icon} />
              </div>
              <div className={"text " + (item.style || "primary")}>
                {item.label}
              </div>
            </a>
          ))}
        </div>
      </div>
    ) : null;
  }
  return render();
}

function Shell(props) {
  function render() {
    return (
      <div
        style={{
          backgroundColor: "black",
          color: "white",
          padding: "10px",
          minHeight: "300px",
          fontFamily: "monospace, monospace",
          marginBottom: "30px",
        }}
      >
        {props.data.output.split("\n").map((line) => (
          <div>{line}</div>
        ))}
      </div>
    );
  }
  return render();
}

function Link(props) {
  function content() {
    if (props.data.icon)
      return apiurl(props.data.url) ? <Icon icon={props.data.icon} /> : "-";
    else return props.data.url ? apiurl(props.data.url) : "-";
  }

  function onClick() {
    imodal(apiurl(props.data.url));
    event.preventDefault();
  }

  function render() {
    return (
      <a
        href={apiurl(props.data.url)}
        target={props.data.target}
        onClick={onClick}
      >
        {content()}
      </a>
    );
  }
  return render();
}

function QrCode(props) {
  const key = Math.random();

  useEffect(() => {
    var qrcode = new QRCode(document.getElementById(key), {
      text: props.data.text,
      width: 128,
      height: 128,
      colorDark: "#333333",
      colorLight: "#ffffff",
      correctLevel: QRCode.CorrectLevel.H,
    });
  }, []);

  function render() {
    return <div id={key}></div>;
  }
  return render();
}

function Indicators(props) {
  if (props.data) {
    return (
      <div className="indicators">
        <h2>
          <TitleCase text={props.data.title} />
        </h2>
        <div>
          {props.data.items.map((item) => (
            <div key={Math.random()} className="item">
              <div className="value">{Format(item.value)}</div>
              <div className="text">
                <TitleCase text={item.name} />
              </div>
            </div>
          ))}
        </div>
        <div className="actions">
          {props.data.actions.map((action) => (
            <Action
              key={Math.random()}
              href={apiurl(action.url)}
              label={action.label}
              modal={action.modal}
            >
              {action.label}
            </Action>
          ))}
        </div>
      </div>
    );
  }
}

export {
  Banner,
  Image,
  Map,
  Steps,
  Progress,
  Status,
  Badge,
  Boxes,
  Html,
  Shell,
  QrCode,
  Indicators,
};
export default Html;
