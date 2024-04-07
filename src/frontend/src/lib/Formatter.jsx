import { ComponentFactory } from "./Factory";

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
      var tokens = obj.split("T");
      var data = tokens[0].split("-");
      var hora = tokens[1];
      var date = new Date(data[0], data[1] - 1, data[2]).toLocaleDateString();
      if (hora == "00:00:00") return date;
      else return date + " " + hora.substr(0, 5);
    }
    return obj;
  }
  if (typeof obj == "object" && obj.type) {
    return <ComponentFactory data={obj} />;
  }
  if (typeof obj == "object" && Array.isArray(obj)) {
    if (obj.length == 0) return "-";
    else
      return (
        <ul style={{ padding: 0 }}>
          {obj.map(function (item) {
            return <li key={Math.random()}>{item}</li>;
          })}
        </ul>
      );
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
