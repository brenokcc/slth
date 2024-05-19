import React, { useState, useEffect } from "react";

function GridLayout(props) {
  function render() {
    const width = props.width || 200;
    const style = {
      display: "grid",
      gridGap: 0,
      gridTemplateColumns: "repeat(auto-fit, minmax(" + width + "px, 1fr))",
      //gridTemplateColumns: "repeat(auto-fit, minmax(" + width + "px, " + (width + 100) + "px))",
      alignItems: props.alignItems || "end",
    };
    return <div key={Math.random()} style={style}>{props.children}</div>;
  }
  return render();
}

function SystemLayout({ header, main, aside, footer }) {
  useEffect(() => {
    window.addEventListener("resize", (e) => {
      const menu = document.querySelector("aside");
      menu.style.display = window.innerWidth < 800 ? "none" : "block";
    });
  }, []);

  function render() {
    return (
      <div>
        <header>{header}</header>
        <div
          style={{
            overflowX: "hide",
            width: "100%",
            display: "flex",
            overflow: "hidden",
          }}
        >
          <aside
            style={{
              flexGrow: 2,
              maxWidth: "350px",
              minWidth: "350px",
              display: "inherite",
              height: window.innerHeight - 70,
            }}
          >
            {aside}
          </aside>
          <main style={{ flexGrow: 6, minWidth: "400px" }}>
            {main}
            <footer>{footer}</footer>
          </main>
        </div>
      </div>
    );
  }
  return render();
}

export { GridLayout, SystemLayout };
export default GridLayout;
