import { useState, useEffect } from "react";
import { format } from "./Formatter.jsx";
import { Action } from "./Action";
import { Field } from "./Form.jsx";
import { request } from "./Request.jsx";

function QuerySet(props) {
  var id = Math.random();
  const [data, setData] = useState(props.data);

  function renderTitle() {
    if (data.attrname) {
      return <h2>{data.title}</h2>;
    } else {
      return <h1>{data.title}</h1>;
    }
  }

  function renderHeader(data) {
    const style = {
      textAlign: "left",
      backgroundColor: "#EEE",
      verticalAlign: "middle",
    };
    return (
      <tr>
        {data.map(function (item) {
          return (
            <th key={Math.random()} style={style}>
              {item.label}
            </th>
          );
        })}
        <th style={style}></th>
      </tr>
    );
  }

  function renderRow(row) {
    return (
      <tr key={Math.random()}>
        {row.data.map(function (field) {
          return <td key={Math.random()}>{format(field.value)}</td>;
        })}
        <td>
          {row.actions.map(function (action) {
            return <Action key={Math.random()} data={action} />;
          })}
        </td>
      </tr>
    );
  }

  function renderRows() {
    if (data.data.length > 0) {
      return (
        <table
          style={{
            width: "100%",
            lineHeight: "2rem",
            borderSpacing: 0,
            overflowX: "scroll",
          }}
        >
          <thead>{renderHeader(data.data[0].data)}</thead>
          <tbody>
            {data.data.map(function (item) {
              return renderRow(item);
            })}
          </tbody>
        </table>
      );
    } else {
      return <center>Nenhum registro encontrado.</center>;
    }
  }

  function renderActions() {
    return (
      <div align="right" style={{ margin: 10 }}>
        {data.actions.map(function (action) {
          return <Action key={Math.random()} data={action} />;
        })}
      </div>
    );
  }

  function renderSearchFilterPanel() {
    const style = {
      display: "inline-block",
      width: 250,
      marginRight: 5,
      verticalAlign: "middle",
    };
    const searching = data.search.length > 0;
    const filtering = data.filters.length > 0;
    if (searching || filtering) {
      const field = {
        name: "q",
        value: "",
        mask: null,
        type: "text",
        label: "Palavras-chaves",
      };
      return (
        <div>
          <div style={style}>{searching && <Field data={field} />}</div>
          {filtering &&
            data.filters.map(function (field) {
              return (
                <div key={Math.random()} style={style}>
                  <Field data={field} />
                </div>
              );
            })}
          <div style={style}>
            <button type="button" onClick={reload}>
              Filtrar
            </button>
          </div>
        </div>
      );
    }
  }

  function reload() {
    const queryString = new URLSearchParams(
      new FormData(document.getElementById("form-" + id))
    ).toString();
    const url = props.data.url.split("?")[0] + "?" + queryString;
    request("GET", url, function (data) {
      setData(data);
    });
  }

  function render() {
    window[id] = () => reload();
    return (
      <div className="reloadable" id={id}>
        <form id={"form-" + id}>
          <div>{false && JSON.stringify(data)}</div>
          {renderTitle()}
          {renderActions()}
          {renderSearchFilterPanel()}
          {renderRows()}
        </form>
      </div>
    );
  }

  return render();
}

export { QuerySet };
export default QuerySet;
