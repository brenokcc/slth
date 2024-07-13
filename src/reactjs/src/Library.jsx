import { useEffect, useState } from "react";
import { Icon } from "./Icon";
import { apiurl, request } from "./Request";
import { Theme } from "./Theme";
import { add_form_params } from "./Form";
import { ComponentFactory } from "./Root.jsx";
import { GridLayout } from "./Layout";
import { toLabelCase } from "./Utils";
import { Link } from "./Link";
import format from "./Formatter.jsx";
import { StyleSheet} from "./StyleSheet.jsx"

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
        src={props.data.src || props.data.placeholder}
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
  return props.data.latitude && props.data.longitude && (
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
      border: "3px solid " + Theme.colors.primary,
      borderRadius: "50%",
      background: step.done ? Theme.colors.primary : "white",
      color: step.done ? "white" : Theme.colors.primary,
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
      backgroundColor: Theme.colors[props.data.style],
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
    props.data.color = Theme.colors[props.data.style];
    return <Badge data={props.data} />;
  }
  return render();
}

function Badge(props) {
  function render() {
    const style = {
      color: "white",
      width: "fit-content",
      borderRadius: 0,
      textWrap: "nowrap",
      padding: 10,
      whiteSpace: "nowrap",
      backgroundColor: props.data.color,
      display: "inline-flex",
      border: "solid 3px white",
      lineHeight: "1rem"
    };
    return <div style={style}>
      {props.data.icon && <Icon icon={props.data.icon} style={{marginRight: 5}}/>}
      {props.data.label}
    </div>;
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
      color: Theme.colors.auxiliary,
    };
    const text = {
      marginTop: 40,
      fontWeight: "bold",
      fontSize: "1.2rem",
      textTransform: "uppercase",
      height: 70,
      color: Theme.colors.primary,
    };

    return props.data.items.length ? (
      <div style={boxes}>
        <h2
          data-label={toLabelCase(props.data.title)}
          style={{ color: Theme.colors.primary }}
        >
          {props.data.title}
        </h2>
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
  function render() {
    const style = {
      color: "white",
      backgroundColor: Theme.colors.highlight,
      margin: -20,
      textAlign: "center",
      paddingTop: 20,
      paddingBottom: 70,
    };
    const number = {
      fontSize: "4rem",
      fontWeight: "bold",
      marginTop: 25,
    };
    const text = {
      fontSize: "1.2rem",
      maxWidth: 200,
      margin: "auto",
    };
    if (props.data) {
      return (
        <div className="indicators" style={style}>
          <h1 data-label={toLabelCase(props.data.title)}>{props.data.title}</h1>
          <GridLayout key={Math.random()} width={300}>
            {props.data.items.map((item) => (
              <div key={Math.random()}>
                <div style={number}>{format(item.value)}</div>
                <div style={text}>{item.name}</div>
              </div>
            ))}
          </GridLayout>
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
  return render();
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
        <h2 align="center">{props.data.title}</h2>
        <div
          style={{ fontSize: "8rem", textAlign: "center", color: "#5470c6" }}
        >
          {props.data.value}
        </div>
      </div>
    );
  }
  return render();
}

function Scheduler(props) {
  const id = Math.random();
  var mouseDown = false;
  const FREE = "rgb(219, 237, 255)";
  const SELECTED = "rgb(89, 154, 242)";
  const BLOCKED = "rgb(246, 123, 135)";
  const SELECTABLE = "rgb(100, 163, 127)";
  const SELECT = [];
  const DESELECT = []
  const WEEKDAYS = ["DOM", "SEG", "TER", "QAR", "QUI", "SEX", "SAB"]
  const [data, setData] = useState(props.data);


  StyleSheet(`
    .scheduler .periods span{
      margin-right: 30px;
    }
    .scheduler .hidden{
      display: none;
    }
  `)
  
  useEffect(() => {
    document.getElementById(id).querySelector(".input-periodo-2").checked = true;
    document.getElementById(id).querySelector(".input-periodo-3").checked = true;
    window['reload-'+props.data.input_name+'-field'] = function(){
      const form = document.getElementsByName(props.data.input_name)[0].closest("form");
        request("GET", add_form_params(props.data.url, form, props.data.input_name), function(data){
          setData(data);
      });
    }
  }, []);

  function bgColor(value, dataLabel) {
    if (data.readonly){
      return value == null ? FREE : SELECTED;
    } else {
      if (value == null){
        if(data.selectable == null) return FREE;
        else return data.selectable.indexOf(dataLabel) >= 0 ? SELECTABLE : FREE
      }
      if (value.text == null) return SELECTED;
      return BLOCKED;
    }
  }

  function onMouseDown(e) {
    mouseDown = true;
  }

  function onMouseUp(e) {
    mouseDown = false;
    document.getElementById("input" + id).value = JSON.stringify(
      {select: SELECT, deselect: DESELECT}
    );
  }

  function pauseEvent(e){
      if(e.stopPropagation) e.stopPropagation();
      if(e.preventDefault) e.preventDefault();
      e.cancelBubble=true;
      e.returnValue=false;
      return false;
  }

  function onMouseOver(e) {
    if (data.readonly) return;
    if (
      props.data.single_selection &&
      getSelections().length > 0 &&
      e.target.style.backgroundColor != SELECTED
    ) {
      return;
    }
    if (mouseDown && e.target.tagName != "I" && e.target.style.backgroundColor != BLOCKED) {
      const dayTokens = e.target.dataset.day.split("/");
      const timeTokens = e.target.dataset.time.split(":");
      const dataLabel = e.target.dataset.day + " " +e.target.dataset.time;
      const date = new Date(parseInt(dayTokens[2], 10), parseInt(dayTokens[1], 10) -1 , parseInt(dayTokens[0], 10), parseInt(timeTokens[0], 10), parseInt(timeTokens[1], 10));
      if (date > new Date() || props.data.weekly) {
        if(props.data.single_selection){
          while(DESELECT.length > 0) DESELECT.pop();
          while(SELECT.length > 0) SELECT.pop();
        }
        if ((e.target.style.backgroundColor == FREE || e.target.style.backgroundColor == SELECTABLE) && (data.selectable == null || data.selectable.indexOf(dataLabel)>=0)){
          e.target.style.backgroundColor = SELECTED;
          console.log('MARCOU', e.target.dataset.day, e.target.dataset.time);
          SELECT.push([e.target.dataset.day, e.target.dataset.time]);
        } else {
          if (data.selectable == null) e.target.style.backgroundColor = FREE;
          else e.target.style.backgroundColor = data.selectable.indexOf(dataLabel)>=0 ? SELECTABLE : FREE;
          console.log('DEMARCOU', e.target.dataset.day, e.target.dataset.time);
          DESELECT.push([e.target.dataset.day, e.target.dataset.time]);
        }
      }
    }
  }

  function getWeekDay(date){
    const tokens = date.split("/");
    return WEEKDAYS[new Date(parseInt(tokens[2], 10), parseInt(tokens[1], 10) -1 , parseInt(tokens[0], 10)).getDay()]
  }

  function getSelections() {
    const selections = [];
    document
      .getElementById(id)
      .querySelectorAll("td")
      .forEach(function (td) {
        if (td.style.backgroundColor == SELECTED)
          selections.push(td.dataset.day, td.dataset.time);
      });
    return selections;
  }

  function period(hour){
    hour = parseInt(hour.split(":")[0]);
    if(hour >= 0 && hour < 6) return 1;
    if(hour >= 6 && hour < 12) return 2;
    if(hour >= 12 && hour < 18) return 3;
    if(hour >= 18 && hour < 24) return 4;
  }

  function periodClass(hour){
    const number = period(hour);
    var className = "period-"+number;
    if(!showPeriod(number)) className+=" hidden";
    return className;
  }

  function checkPeriod(period, checked){
    document
      .getElementById(id)
      .querySelectorAll(".period-"+period)
      .forEach(function (tr) {
        tr.style.display = checked ? "table-row" : "none";
      });
  }

  function showPeriod(period){
    return period == 2 || period == 3 
  }

  function render() {
    const style = {
      overflowX: "auto",
    };
    const table = {
      width: "100%",
      borderSpacing: 0,
      borderCollapse: "collapse",
      marginTop: 15,
      marginBottom: 15,
    };
    const cell = {
      border: "solid 4px white",
      userSelect: "none",
    };
    return (
      <div id={id} style={style} className="scheduler">
        {props.data.title && <h2>{ props.data.title }</h2>}
        <input id={"input" + id} type="hidden" name={props.data.input_name} />
        <div className="periods">
          <input className="input-periodo-1" type="checkbox" data-label="madrugada" onChange={(e)=>checkPeriod(1, e.target.checked)}/> <span>Madrugada</span>
          <input className="input-periodo-2" type="checkbox" data-label="manha" onChange={(e)=>checkPeriod(2, e.target.checked)}/> <span>Manhã</span>
          <input className="input-periodo-3" type="checkbox" data-label="tarde" onChange={(e)=>checkPeriod(3, e.target.checked)}/> <span>Tarde</span>
          <input className="input-periodo-4" type="checkbox" data-label="noite" onChange={(e)=>checkPeriod(4, e.target.checked)}/> <span>Noite</span>
        </div>
        <table style={table} onMouseDown={onMouseDown} onMouseUp={onMouseUp}>
          <thead>
            <tr>
              {data.matrix[0].map(function (value) {
                return (
                  <th className="bold" key={Math.random()} style={cell}>
                    {getWeekDay(value.text)}
                    {!props.data.weekly && <br/>}
                    {!props.data.weekly && value.text}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {data.matrix.map(function (row, i) {
              if (i > 0) {
                return (
                  <tr key={Math.random()} className={periodClass(row[0].text)}>
                    {row.map(function (value, j) {
                      if (j == 0)
                        return (
                          <th
                            className="bold"
                            key={Math.random()}
                            align="center"
                            style={cell}
                          >
                            {value.text}
                          </th>
                        );
                      else {
                        const dataLabel = data.matrix[0][j].text+ " " +row[0].text;
                        const td = {
                          backgroundColor: bgColor(value, dataLabel),
                          border: "solid 4px white",
                        };
                        return (
                          <td
                            key={Math.random()}
                            align="center"
                            style={td}
                            onMouseDown={onMouseOver}
                            onMouseLeave={onMouseOver}
                            onMouseUp={onMouseOver}
                            data-day={data.matrix[0][j].text}
                            data-time={row[0].text}
                            data-label={dataLabel}
                          >
                            {value && value.text && <Tooltip text={value.text}><Icon icon={value.icon || "x"} style={{color: "white", cursor: "help"}}/></Tooltip>}
                          </td>
                        );
                      }
                    })}
                  </tr>
                );
              }
            })}
          </tbody>
        </table>
      </div>
    );
  }
  return render();
}

function Tooltip(props){

  function render(){
    StyleSheet(`
      .tooltip {
        position: relative;
        display: inline-block;
      }
      .tooltip .tooltiptext {
        visibility: hidden;
        width: 220px;
        background-color: ${Theme.colors.highlight};
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px 0;
        position: absolute;
        z-index: 1;
        bottom: 150%;
        left: 50%;
        margin-left: -60px;
        z-index: 9999;
      }
      .tooltip:hover .tooltiptext {
        visibility: visible;
      }
    `)
    return (
      <div className="tooltip">{props.children}
        <div className="tooltiptext">{format(props.text)}</div>
      </div>
    )
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
  Scheduler,
  Tooltip,
};
export default Html;
