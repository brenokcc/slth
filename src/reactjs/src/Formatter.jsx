import { ComponentFactory } from "./Root.jsx";

function format(obj) {
  if (obj === null) return "-";
  if (obj === "") return "-";
  if (obj === true) return "Sim";
  if (obj === false) return "Não";
  if (typeof obj === "number") {
    var tokens = obj.toString().split(".");
    if (tokens.length == 1) {
      return obj.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    } else {
      tokens[0] = tokens[0].toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
      tokens[1] = tokens[1].substring(0, 2);
      if (tokens[1].length == 1) tokens[1] = tokens[1] + "0";
      return tokens[0] + "," + tokens[1];
    }
  }
  if (typeof obj === "string") {
    if (obj.length == 7 && obj[0] == "#") {
      return <ComponentFactory data={{ type: "color", value: obj }} />;
    } else if (obj.length == 19 && obj[13] == ":" && obj[16] == ":") {
      var tokens = obj.split(" ");
      var data = tokens[0];
      var hora = tokens[1];
      return hora == "00:00:00" ? data : data + " " + hora;
    } else if (obj.indexOf('\n') >=0){
      return obj.split('\n').map(function(line, i){
        return <>
          <div key={Math.random()}>{line}</div>
        </>
      });
    }
    return obj;
  }
  if (typeof obj == "object" && obj.type) {
    return <ComponentFactory data={obj} />;
  }
  if (typeof obj == "object" && Array.isArray(obj)) {
    if (obj.length == 0) return "-";
    else if (typeof obj[0] == "object" && obj[0].type != null){
      return <>
        {obj.map(function (item) {
            return <ComponentFactory data={item} />;
        })}
      </>
    } else {
      return (
        <ul style={{ padding: 0 }}>
          {obj.map(function (item) {
            return <li key={Math.random()}>{item}</li>;
          })}
        </ul>
      );
    }
  }
  if (
    typeof obj == "object" &&
    JSON.stringify(Object.keys(obj)) == JSON.stringify(["id", "text"])
  ) {
    return obj.text;
  }
  return JSON.stringify(obj);
}
export { format };
export default format;
