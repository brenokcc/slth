import { useState, useEffect } from "react";

var MAP = {};

function ComponentFactory(props) {
  const func = MAP[props.data.type];
  return func ? func(props.data) : <div>{JSON.stringify(props.data)}</div>;
}

ComponentFactory.register = function (type, func) {
  MAP[type] = func;
};

export { ComponentFactory };
