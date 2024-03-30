import { useState, useEffect } from "react";
import { Action } from "./Action";

function QuerySet(props) {
  function renderTitle() {
    if (props.data.attrname) {
      return <h2>{props.data.title}</h2>;
    } else {
      return <h1>{props.data.title}</h1>;
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
          return <td key={Math.random()}>{field.value}</td>;
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
    if (props.data.data.length > 0) {
      return (
        <table
          style={{
            width: "100%",
            lineHeight: "2rem",
            borderSpacing: 0,
            overflowX: "scroll",
          }}
        >
          <thead>{renderHeader(props.data.data[0].data)}</thead>
          <tbody>
            {props.data.data.map(function (item) {
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
        {props.data.actions.map(function (action) {
          return <Action key={Math.random()} data={action} />;
        })}
      </div>
    );
  }

  function render() {
    return (
      <>
        <div>{false && JSON.stringify(props.data)}</div>
        {renderTitle()}
        {renderActions()}
        {renderRows()}
      </>
    );
  }

  return render();
}

export { QuerySet };
export default QuerySet;
