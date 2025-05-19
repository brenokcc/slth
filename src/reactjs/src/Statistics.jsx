import { ChartFactory } from "./Chart";
import format from "./Formatter";
import StyleSheet from "./StyleSheet";
import toLabelCase from "./Utils";

function Statistics(props) {
  StyleSheet(`
    .statistics .odd {
      background-color: #EEE;
    }
  `);
  function render1D() {
    var rows = [];
    for (var i = 0; i < props.data.series.length; i++) {
      rows.push([props.data.series[i][0], props.data.series[i][1], props.data.series[i][2]]);
    }
    if (props.data.chart)
      return (
        <ChartFactory
          type={props.data.chart}
          title={props.data.title}
          rows={rows}
        />
      );

    return (
      <div className="statistics">
        {props.data.title && (
          <h2 data-label={toLabelCase(props.data.title)}>{props.data.title}</h2>
        )}
        <table style={{ width: "100%", borderSpacing:0 }}>
          <tbody>
            {rows.map((row, j) => (
              <tr key={Math.random()}>
                {row.map((v, i) =>
                  i == 0 ? (
                    <th
                      key={Math.random()}
                      style={{ textAlign: "left", lineHeight: "2rem", padding: 5 }}
                      className={j % 2 == 0 ? "even" : "odd"}
                    >
                      {v}
                    </th>
                  ) : (
                    <td key={Math.random()} className={j % 2 == 0 ? "even" : "odd"}>
                      {format(v)}
                    </td>
                  )
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
  function render2D() {
    var headers = [];
    var rows = [];
    var keys = Object.keys(props.data.series);
    var tfoot = [];
    for (var i = 0; i < keys.length; i++) {
      if (i == 0) headers.push("");
      var row = [keys[i]];
      var total = 0;
      for (var j = 0; j < props.data.series[keys[i]].length; j++) {
        var serie = props.data.series[keys[i]];
        if (i == 0) headers.push(serie[j][0]);
        row.push(serie[j][1]);
        total += serie[j][1];
        if (keys.length > 1) {
          if (i == 0) tfoot.push(serie[j][1]);
          else tfoot[j] += serie[j][1];
          if (j > 0 && j == props.data.series[keys[i]].length - 1) {
            if (i == 0) tfoot.push(total);
            else tfoot[j + 1] += total;
          }
        }
      }
      if (row.length > 2) {
        if (i == 0) headers.push("");
        row.push(total);
      }
      rows.push(row);
    }
    if (props.data.chart)
      return (
        <ChartFactory
          type={props.data.chart}
          title={props.data.title}
          headers={headers}
          rows={rows}
        />
      );

    return (
      <div className="statistics">
        {props.data.title && (
          <h2 data-label={toLabelCase(props.data.title)}>{props.data.title}</h2>
        )}
        <table style={{ width: "100%", borderSpacing: 0 }}>
          {headers && (
            <thead>
              <tr>
                {headers.map((k) => (
                  <th className="bold" key={Math.random()} style={{textAlign: "left", padding: 5}}>{k}</th>
                ))}
              </tr>
            </thead>
          )}
          <tbody>
            {rows.map((row, j) => (
              <tr key={Math.random()}>
                {row.map((v, i) =>
                  i == 0 ? (
                    <th className={j % 2 == 0 ? "even" : "odd"} key={Math.random()} style={{textAlign: "left", padding: 5}}>{v}</th>
                  ) : (
                    <td
                      align="center"
                      className={
                        (i == row.length - 1 &&
                        headers &&
                        headers[headers.length - 1] == "" ? "bold" : "") + " " + (j % 2 == 0 ? "even" : "odd")
                      }
                      key={Math.random()}
                    >
                      {format(v)}
                    </td>
                  )
                )}
              </tr>
            ))}
            {tfoot.length > 0 && (
              <tr key={Math.random()}>
                <th></th>
                {tfoot.map((total) => (
                  <td
                    align="center"
                    className="bold"
                    key={Math.random()}
                  >
                    {format(total)}{" "}
                  </td>
                ))}
              </tr>
            )}
          </tbody>
        </table>
      </div>
    );
  }

  return Array.isArray(props.data.series) ? render1D() : render2D();
}

export { Statistics };
export default Statistics;
