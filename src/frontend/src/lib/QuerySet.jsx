import { useState, useEffect } from "react";
import { Button } from "./Button";

function QuerySet(props) {
  function renderRows() {
    return (
      <ul>
        {props.data.data.map(function (item) {
          return <li key={Math.random()}>{item.title}</li>;
        })}
      </ul>
    );
  }

  function renderActions() {
    return (
      <ul>
        {props.data.actions.map(function (action) {
          return <Button key={Math.random()} data={action} />;
        })}
      </ul>
    );
  }

  function render() {
    return (
      <>
        <div>{JSON.stringify(props.data)}</div>
        <h1>{props.data.title}</h1>
        <div>{renderRows()}</div>
        <div>{renderActions()}</div>
      </>
    );
  }

  return render();
}

export { QuerySet };
export default QuerySet;
