import { useState, useEffect } from "react";
import { format } from "./Formatter.jsx";
import { Action } from "./Action";
import { Field } from "./Form.jsx";
import { request } from "./Request.jsx";
import { Info } from "./Message.jsx";
import { GridLayout } from "./Layout.jsx";
import { Button } from "./Button.jsx";
import Icon from "./Icon.jsx";

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
      backgroundColor: "#f0f0f0",
      lineHeight: "3rem",
      //borderBottom: "solid 1px #1351b4",
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
    const td = { borderBottom: "solid 1px #DDD" };
    const actions = { borderBottom: "solid 1px #DDD", lineHeight: "3rem" };
    return (
      <tr key={Math.random()}>
        {row.data.map(function (field) {
          return (
            <td key={Math.random()} style={td}>
              {format(field.value)}
            </td>
          );
        })}
        <td style={actions}>
          <div style={{ verticalAlign: "center" }}>
            {row.actions.map(function (action) {
              return (
                <Action key={Math.random()} data={action} default compact />
              );
            })}
          </div>
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

  function setPage(page) {
    const form = document.getElementById("form-" + id);
    const input = form.querySelector("input[name=page]");
    input.value = page;
    reload();
  }

  function renderPaginator() {
    const style = {
      display: "flex",
      justifyContent: "space-between",
      lineHeight: "4rem",
      alignItems: "baseline",
    };
    const inline = {
      display: "inline",
      paddingRight: 10,
    };
    const select = {
      marginLeft: 10,
      marginRight: 10,
      height: "2.5rem",
      textAlign: "center",
    };
    return (
      <div style={style}>
        <div>
          <div style={inline}>
            Exibir
            <select
              style={select}
              name="page_size"
              onChange={() => setPage(1)}
              value={data.page_size}
            >
              {data.page_sizes.map(function (size) {
                return <option key={Math.random()}>{size}</option>;
              })}
            </select>
          </div>
          <div style={inline}>|</div>
          <div style={inline}>
            {data.start} - {data.end} de {data.total}
          </div>
        </div>
        <div>
          <div style={inline}>
            {data.total > data.count ? (
              <span>Página</span>
            ) : (
              <span>Página 1</span>
            )}
            <input
              type={data.total > data.count ? "text" : "hidden"}
              name="page"
              defaultValue={data.page}
              style={{
                width: 30,
                marginLeft: 10,
                marginRight: 10,
                height: "2rem",
                textAlign: "center",
              }}
            />
            {data.total > data.count && <div style={inline}>|</div>}
            {data.total > data.count && data.previous && (
              <Button
                icon="chevron-left"
                default
                display="inline"
                onClick={() => setPage(data.previous)}
              />
            )}
            {data.total > data.count && data.next && (
              <Button
                icon="chevron-right"
                default
                display="inline"
                onClick={() => setPage(data.next)}
              />
            )}
          </div>
        </div>
      </div>
    );
  }

  function renderActions() {
    return (
      <div align="right" style={{ margin: 10 }}>
        {data.actions.map(function (action) {
          return <Action key={Math.random()} data={action} primary />;
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
              <Button onClick={reload} label="Filtrar" default />
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
    const sytle = { backgroundColor: "white", padding: 20 };
    return (
      <div className="reloadable" id={id} sytle={sytle}>
        <form id={"form-" + id}>
          <div>{false && JSON.stringify(data)}</div>
          {renderTitle()}
          {renderActions()}
          {renderSearchFilterPanel()}
          {renderRows()}
          {renderPaginator()}
        </form>
      </div>
    );
  }

  return render();
}

export { QuerySet };
export default QuerySet;
