import { useEffect } from "react";
import { Icon } from "./Icon";
import { apiurl, appurl } from "./Request";
import { COLORS } from "./Theme";
import { ComponentFactory } from "./Root.jsx";
import { GridLayout } from "./Layout";
import { toLabelCase } from "./Utils";
import { Link } from "./Link";

function Html(props) {
  return <div dangerouslySetInnerHTML={{ __html: props.data.content }}></div>;
}

function Banner(props) {
  return <img src={props.data.src} style={{ width: "100%" }} />;
}

function Image(props) {
  const style = { width: "100%", textAlign: "center" };
  return (
    <div style={style}>
      <img
        src={props.data.src}
        style={{
          width: props.data.width,
          height: props.data.height,
          borderRadius: props.data.round ? "50%" : 0,
        }}
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
        <Icon style={{ marginTop: 6 }} icon={props.data.icon} />
      ) : (
        <span>&nbsp;</span>
      );
    } else {
      return <div style={{ marginTop: 6 }}>{step.number}</div>;
    }
  }

  function circleStyle(step) {
    return {
      border: "3px solid " + (step.done ? "#1351b4" : "#1151b3"),
      borderRadius: "50%",
      background: step.done ? "#1351b4" : "white",
      color: step.done ? "white" : "#1151b3",
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
      borderBottom: "2px solid #1151b3",
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
    const progress = {
      display: "inline-block",
      width: "100%",
      backgroundColor: "#DDD",
      borderRadius: 5,
      marginTop: 5,
    };
    const percentage = {
      marginLeft: 10,
    };
    const value = {
      display: "block",
      paddingTop: 2,
      paddingBottom: 2,
      color: "white",
      borderRadius: 5,
      width: props.data.value + "%",
      backgroundColor: COLORS[props.data.style],
    };
    return (
      <span style={progress}>
        <span style={value}>
          <span style={percentage}>{props.data.value}%</span>
        </span>
      </span>
    );
  }
  return render();
}

function Status(props) {
  function render() {
    props.data.color = COLORS[props.data.style];
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
    const boxes = {
      padding: 20,
      marginLeft: -20,
      marginRight: -20,
      textAlign: "center",
      backgroundColor: "#f8f8f8",
    };
    const h2 = {
      color: "blue",
      paddingTop: 25,
      fontSize: "1.5rem",
    };
    const box = {
      padding: 20,
      display: "inline-flex",
      flexDirection: "column",
      width: 250,
      height: 250,
      backgroundColor: "white",
      boxShadow: "0px 15px 10px -15px #DDD",
      margin: 10,
      textDecoration: "none",
    };
    const i = {
      marginTop: 30,
      fontSize: "3rem",
      color: "#2670e8",
    };
    const text = {
      marginTop: 40,
      fontWeight: "bold",
      fontSize: "1.2rem",
      textTransform: "uppercase",
      height: 70,
      color: "#0c326f",
    };

    return props.data.items.length ? (
      <div style={boxes}>
        <h2 data-label={toLabelCase(props.data.title)}>{props.data.title}</h2>
        <div>
          {props.data.items.map((item) => (
            <Link
              key={Math.random()}
              href={item.url}
              style={box}
              dataLabel={item.label}
            >
              <div>
                <Icon style={i} icon={item.icon} />
              </div>
              <div style={text}>{item.label}</div>
            </Link>
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
          <div key={Math.random()}>{line}</div>
        ))}
      </div>
    );
  }
  return render();
}

function FileLink(props) {
  function render() {
    return props.data.url ? (
      <Link href={props.data.url} imodal={props.data.modal ? true : false}>
        {props.data.icon ? <Icon icon={props.data.icon} /> : props.data.url}
      </Link>
    ) : (
      <span>-</span>
    );
  }
  return render();
}

function FilePreview(props) {
  function render() {
    return (
      <iframe
        src={props.data.url}
        width="100%"
        height={500}
        style={{ border: 0 }}
      ></iframe>
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
        <h2 data-label={toLabelCase(props.data.title)}>
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
            <Link
              key={Math.random()}
              href={apiurl(action.url)}
              label={action.label}
              modal={action.modal}
            >
              {action.label}
            </Link>
          ))}
        </div>
      </div>
    );
  }
}

function Grid(props) {
  function render() {
    return (
      <GridLayout width={400}>
        {props.data.items.map((data, i) => (
          <div key={Math.random()}>
            <ComponentFactory data={data} />
          </div>
        ))}
      </GridLayout>
    );
  }
  return render();
}

function Counter(props) {
  function render() {
    return (
      <div>
        <h2>{props.data.title}</h2>
        <div
          style={{ fontSize: "12rem", textAlign: "center", color: "#5470c6" }}
        >
          {props.data.value}
        </div>
      </div>
    );
  }
  return render();
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
  FileLink,
  FilePreview,
  Grid,
  Counter,
};
export default Html;
