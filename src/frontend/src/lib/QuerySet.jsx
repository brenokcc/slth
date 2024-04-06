import { useState, useEffect } from "react";
import { format } from "./Formatter.jsx";
import { Action } from "./Action";
import { Field } from "./Form.jsx";
import { request } from "./Request.jsx";
import { Info } from "./Message.jsx";
import { GridLayout } from "./Layout.jsx";

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
      verticalAlign: "top",
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
    const td = { paddingBottom: 15 };
    return (
      <tr key={Math.random()}>
        {row.data.map(function (field) {
          return <td key={Math.random()}>{format(field.value)}</td>;
        })}
        <td style={td}>
          {row.actions.map(function (action) {
            return <Action key={Math.random()} data={action} />;
          })}
        </td>
      </tr>
    );
  }

  function renderRows() {
    const div = {
      width: "100%",
      overflowX: "auto",
    };
    const table = {
      width: "100%",
      lineHeight: "2rem",
      borderSpacing: 0,
      backgroundColor: "white",
      padding: 20,
    };
    if (data.data.length > 0) {
      return (
        <div style={div}>
          <table style={table}>
            <thead>{renderHeader(data.data[0].data)}</thead>
            <tbody>
              {data.data.map(function (item) {
                return renderRow(item);
              })}
            </tbody>
          </table>
        </div>
      );
    } else {
      return (
        <Info
          data={{
            text: "Nenhum registro encontrado.",
          }}
        ></Info>
      );
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
        <GridLayout width={250}>
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
            <div style={{ paddingBottom: 15, paddingTop: 15 }}>
              <Action onClick={reload} data={{ name: "Filtrar" }} />
            </div>
          </div>
        </GridLayout>
      );
    }
  }

  function reload() {
    var url;
    const queryString = new URLSearchParams(
      new FormData(document.getElementById("form-" + id))
    ).toString();
    if (props.data.url.indexOf("?") > 0)
      url = props.data.url + "&" + queryString;
    else url = props.data.url + "?" + queryString;
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
