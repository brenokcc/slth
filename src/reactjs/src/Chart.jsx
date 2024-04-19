import React from "react";

function Echarts(props) {
  var id = Math.random();

  function init() {
    var element = document.getElementById(id);
    if (element) {
      var chart = echarts.init(element);
      chart.setOption(props.option);
    } else {
      setTimeout(init, 1000);
    }
  }

  setTimeout(init, 1000);

  return <div id={id} style={{ width: "100%", height: 300 }}></div>;
}

function Pie(props) {
  var radius = [
    ["70%", "78%"],
    ["60%", "68%"],
    ["50%", "58%"],
    ["40%", "48%"],
    ["30%", "48%"],
    ["20%", "28%"],
    ["10%", "18%"],
  ];

  function series() {
    if (props.headers) {
      return props.headers.slice(1).map(function (header, i) {
        return {
          name: header,
          type: "pie",
          radius: radius[i],
          emphasis: {
            label: {
              show: true,
              formatter: function (params) {
                return params.value.toLocaleString("pt-BR");
              },
              fontWeight: "bold",
            },
          },
          roseType: null,
          data: props.rows.map(function (row) {
            return { name: row[0], value: row[i + 1] };
          }),
        };
      });
    } else {
      return {
        name: null,
        type: "pie",
        radius: props.donut ? ["25%", "65%"] : ["0%", "75%"],
        emphasis: {
          label: {
            show: true,
            formatter: function (params) {
              return params.value.toLocaleString("pt-BR");
            },
            fontWeight: "bold",
          },
        },
        roseType: props.area ? "area" : null,
        data: props.rows.map(function (row, i) {
          return { name: row[0], value: row[1] };
        }),
      };
    }
  }

  function render() {
    var option = {
      tooltip: {
        trigger: "item",
        formatter: function (params) {
          return `${params.name}: <b>${params.data.value.toLocaleString(
            "pt-BR"
          )}</b> (${params.percent.toLocaleString("pt-BR")}%)`;
        },
      },
      legend: {},
      label: {
        show: true,
        formatter(param) {
          return (
            param.name + " (" + param.percent.toLocaleString("pt-BR") + "%)"
          );
        },
      },
      series: series(),
    };
    return <Echarts option={option} />;
  }

  return render();
}

function Donut(props) {
  return <Pie donut={true} headers={props.headers} rows={props.rows} />;
}

function Polar(props) {
  return <Pie area={true} headers={props.headers} rows={props.rows} />;
}

function Chart(props) {
  var invert = props.invert || false;
  var type = props.type || "bar";
  var stack = props.stack;
  var yAxis = { type: "value" };
  var toolbox = {
    show: true,
    feature: { mark: { show: true }, saveAsImage: { show: true } },
  };
  var areaStyle = props.area ? {} : null;

  function xAxis() {
    if (props.headers) {
      return { type: "category", data: props.headers.slice(1) };
    } else {
      return {
        type: "category",
        data: props.rows.map(function (row) {
          return row[0];
        }),
      };
    }
  }

  function series() {
    if (props.headers) {
      return props.rows.map(function (row) {
        return {
          name: row[0],
          data: row.slice(1),
          type: type,
          stack: stack,
          areaStyle: areaStyle,
        };
      });
    } else {
      return [
        {
          name: null,
          data: props.rows.map(function (row) {
            return row[1];
          }),
          type: type,
          stack: stack,
          areaStyle: areaStyle,
        },
      ];
    }
  }

  function render() {
    var option = {
      toolbox: toolbox,
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: function (params) {
          return `${params[0].name}: <b>${params[0].value.toLocaleString(
            "pt-BR"
          )}</b>`;
        },
      },
      legend: {},
      label: {
        show: true,
        formatter: function (params) {
          return params.value.toLocaleString("pt-BR");
        },
      },
      xAxis: invert ? yAxis : xAxis(),
      yAxis: invert ? xAxis() : yAxis,
      series: series(),
    };
    return <Echarts option={option} />;
  }

  return render();
}

function Bar(props) {
  return <Chart headers={props.headers} rows={props.rows} />;
}

function Line(props) {
  return <Chart type="line" headers={props.headers} rows={props.rows} />;
}

function Area(props) {
  return (
    <Chart area={true} type="line" headers={props.headers} rows={props.rows} />
  );
}

function StackedBar(props) {
  return <Chart stack="1" headers={props.headers} rows={props.rows} />;
}

function Column(props) {
  return <Chart invert={true} headers={props.headers} rows={props.rows} />;
}

function StackedColumn(props) {
  return (
    <Chart invert={true} stack="1" headers={props.headers} rows={props.rows} />
  );
}

function TreeMap(props) {
  function series() {
    if (props.headers) {
      return [
        {
          type: "treemap",
          roam: "move",
          nodeClick: true,
          data: props.headers.slice(1).map(function (header, i) {
            return {
              name: header,
              type: "pie",
              children: props.rows.map(function (row) {
                return { name: row[0], value: row[i + 1] };
              }),
            };
          }),
        },
      ];
    } else {
      return [
        {
          type: "treemap",
          roam: "move",
          nodeClick: false,
          data: props.rows.map(function (row) {
            return {
              name: row[0],
              value: row[1],
            };
          }),
        },
      ];
    }
  }

  function render() {
    var option = {
      tooltip: { trigger: "item" },
      legend: {},
      label: {
        show: true,
        formatter(param) {
          return param.name + " (" + param.value.toLocaleString("pt-BR") + ")";
        },
      },
      series: series(),
    };
    return <Echarts option={option} />;
  }

  return render();
}

function Progress(props) {
  function render() {
    var option = {
      series: [
        {
          type: "gauge",
          startAngle: 0,
          endAngle: 360,
          min: 0,
          max: 100,
          progress: {
            show: true,
            width: 38,
          },
          pointer: null,
          axisTick: null,
          splitLine: {
            length: 0,
          },
          axisLine: {
            lineStyle: {
              width: 38,
            },
          },
          axisLabel: null,
          detail: {
            backgroundColor: "#fff",
            fontSize: "2.5rem",
            width: "60%",
            lineHeight: 40,
            height: 40,
            borderRadius: 8,
            offsetCenter: [0, "0%"],
            valueAnimation: true,
            formatter: function (value) {
              return value.toFixed(0) + "%";
            },
          },
          data: [
            {
              value: props.value,
            },
          ],
        },
      ],
    };
    return <Echarts option={option} />;
  }
  return render();
}

function ChartFactory(props) {
  function chart() {
    switch (props.type) {
      case "pie":
        return <Pie headers={props.headers} rows={props.rows} />;
      case "polar":
        return <Polar headers={props.headers} rows={props.rows} />;
      case "donut":
        return <Donut headers={props.headers} rows={props.rows} />;
      case "bar":
        return <Bar headers={props.headers} rows={props.rows} />;
      case "stacked_bar":
        return <StackedBar headers={props.headers} rows={props.rows} />;
      case "column":
        return <Column headers={props.headers} rows={props.rows} />;
      case "stacked_column":
        return <StackedColumn headers={props.headers} rows={props.rows} />;
      case "tree_map":
        return <TreeMap headers={props.headers} rows={props.rows} />;
      case "line":
        return <Line headers={props.headers} rows={props.rows} />;
      case "area":
        return <Area headers={props.headers} rows={props.rows} />;
      case "progress":
        return <Progress headers={props.headers} rows={props.rows} />;
      default:
        return <Chart headers={props.headers} rows={props.rows} />;
    }
  }
  function render() {
    return (
      <div style={{ width: 300, margin: "auto" }}>
        {props.title && <h2 className="title">{props.title}</h2>}
        {chart()}
      </div>
    );
  }
  return render();
}

function Example(props) {
  function render2D() {
    var headers = ["", "Não", "Sim"];
    var rows = [
      ["EM_CURSO", 93, 383],
      ["ABANDONO", 227, 61],
      ["DESLIGADA", 1, 0],
      ["CONCLUÍDA", 260, 94],
    ];
    return (
      <>
        <Donut headers={headers} rows={rows} />
        <Bar headers={headers} rows={rows} />
        <StackedBar headers={headers} rows={rows} />
        <Column headers={headers} rows={rows} />
        <StackedColumn headers={headers} rows={rows} />
        <TreeMap headers={headers} rows={rows} />
        <Line headers={headers} rows={rows} />
        <Area headers={headers} rows={rows} />
      </>
    );
  }

  function render1D() {
    var rows = [
      ["EM_CURSO", 476],
      ["ABANDONO", 288],
      ["DESLIGADA", 1],
      ["CONCLUÍDA", 354],
    ];
    return (
      <>
        <Pie rows={rows} />
        <Polar rows={rows} />
        <Donut rows={rows} />
        <Bar rows={rows} />
        <Column rows={rows} />
        <TreeMap rows={rows} />
        <Line rows={rows} />
        <Area rows={rows} />
        <Progress value={90} />
      </>
    );
  }

  function render() {
    return (
      <div>
        <h1>Chart 1D</h1>
        {render1D()}
        <h1>Chart 2D</h1>
        {render2D()}
      </div>
    );
  }

  return render();
}

export {
  Pie,
  Polar,
  Donut,
  Bar,
  StackedBar,
  Column,
  StackedColumn,
  TreeMap,
  Line,
  Area,
  Progress,
  ChartFactory,
  Example,
};
export default ChartFactory;
