import React, { useState, useEffect } from "react";

function GridLayout(props) {
  function render() {
    const width = props.width || 200;
    const style = {
      display: "grid",
      gridGap: 0,
      gridTemplateColumns: "repeat(auto-fit, minmax(" + width + "px, 1fr))",
      alignItems: "end",
    };
    return <div style={style}>{props.children}</div>;
  }
  return render();
}

function SystemLayout({ header, main, aside, footer }) {
  const [matches, setMatches] = useState(getMediaQuery().matches);

  useEffect(() => {
    getMediaQuery().addEventListener("change", (e) => setMatches(e.matches));
  }, []);

  function getMediaQuery() {
    return window.matchMedia("(min-width: 1200px)");
  }

  function getGridTemplateColumns() {
    if (getMediaQuery().matches) {
      return aside && main ? "1fr 3fr" : "4fr";
    } else {
      return "4fr";
    }
  }

  function getDisplay() {
    return getMediaQuery().matches && aside ? "grid" : "block";
  }

  function getMarginBottom() {
    return getMediaQuery().matches && aside ? 0 : -20;
  }

  function gridTemplateAreas() {
    var areas = [];
    if (getMediaQuery().matches) {
      if (aside) {
        areas.push("'header  header'");
        areas.push("'aside main'");
        areas.push("'footer  footer'");
      } else {
        areas.push("'header'");
        areas.push("'main'");
        areas.push("'footer'");
      }
    } else {
      areas.push("'header'");
      areas.push("'aside'");
      areas.push("'main'");
      areas.push("'footer'");
    }
    return areas.join(" ");
  }

  function render() {
    const headerStyle = {
      gridArea: "header",
      //backgroundColor: "#fed330",
      marginBottom: getMarginBottom(),
    };
    const mainStyle = {
      gridArea: "main",
      //backgroundColor: "#20bf6b",
      marginBottom: getMarginBottom(),
    };
    const asideStyle = {
      gridArea: "aside",
      //backgroundColor: "#45aaf2",
      marginBottom: getMarginBottom(),
    };
    const footerStyle = {
      gridArea: "footer",
      //backgroundColor: "#fd9644",
      marginBottom: getMarginBottom(),
    };
    const wrapper = {
      display: getDisplay(),
      gridTemplateColumns: getGridTemplateColumns(),
      gridTemplateAreas: gridTemplateAreas(),
    };
    return (
      <div style={wrapper}>
        <header style={headerStyle}>{header}</header>
        <aside style={asideStyle}>{aside}</aside>
        <main style={mainStyle}>{main}</main>
        <footer style={footerStyle}>{footer}</footer>
      </div>
    );
  }
  return render();
}

export { GridLayout, SystemLayout };
export default GridLayout;
