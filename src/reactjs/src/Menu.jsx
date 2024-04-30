import Link from "./Link";
import Icon from "./Icon";
import { toLabelCase } from "./Utils";

function Menu() {
  function renderUser() {
    const img = {
      width: 150,
      height: 150,
      borderRadius: "50%",
      objectFit: "cover",
    };
    return (
      window.application.menu.user && (
        <div align="center">
          {window.application.menu.image && (
            <div>
              <img src={window.application.menu.image} style={img} />
            </div>
          )}
          <div>
            <Link
              dataLabel="Editar Perfil"
              href="/api/editprofile/"
              style={{ textDecoration: "none" }}
            >
              {window.application.menu.user}
            </Link>
          </div>
        </div>
      )
    );
  }

  function onClick(e) {
    var item = e.target;
    const child = item.querySelector(":scope > ul, :scope > li");
    if (child) {
      if (child.offsetParent === null) {
        item
          .querySelectorAll(":scope > ul, :scope > li, :scope > ul > li")
          .forEach(function (subitem) {
            subitem.style.display = "block";
          });
      } else {
        item
          .querySelectorAll(":scope > ul, :scope > li")
          .forEach(function (subitem) {
            subitem.style.display = "none";
          });
      }
      const right = item.querySelector(":scope > i.fa-solid.fa-chevron-right");
      const up = item.querySelector(":scope > i.fa-solid.fa-chevron-up");
      if (right) {
        right.classList.remove("fa-chevron-right");
        right.classList.add("fa-chevron-up");
      }
      if (up) {
        up.classList.remove("fa-chevron-up");
        up.classList.add("fa-chevron-right");
      }

      e.preventDefault();
      e.stopPropagation();
      e.cancelBubble = true;
      return false;
    } else {
      const menu = document.querySelector("aside");
      menu.style.display = window.innerWidth < 800 ? "none" : "block";
    }
  }

  function renderItem(item, level) {
    const style = {
      display: level == 0 ? "block" : "none",
      cursor: "pointer",
      paddingLeft: 5,
      paddingTop: 10,
      paddingBottom: 10,
      lineHeight: "2rem",
      color: "#1351b4",
    };
    const iconStyle = { padding: 5, fontSize: "1.2rem" };
    if (item.url) {
      return (
        <li key={Math.random()} style={style} onClick={onClick}>
          <Link
            href={item.url}
            dataLabel={toLabelCase(item.label)}
            style={{ textDecoration: "none" }}
          >
            {level == 0 && (
              <Icon icon={item.icon || "dot-circle"} style={iconStyle} />
            )}
            {item.label}
          </Link>
        </li>
      );
    } else {
      return (
        item.items.length > 0 && (
          <li
            key={Math.random()}
            onClick={onClick}
            style={style}
            data-label={toLabelCase(item.label)}
          >
            {level == 0 && (
              <Icon icon={item.icon || "dot-circle"} style={iconStyle} />
            )}
            {item.label}
            <Icon
              icon="chevron-right"
              style={{ float: "right", paddingTop: 8 }}
            />
            <ul style={{ display: "none", paddingLeft: 15 }}>
              {item.items.map(function (subitem) {
                return renderItem(subitem, level + 1);
              })}
            </ul>
          </li>
        )
      );
    }
  }

  function renderItems() {
    const style = { padding: 0 };
    return (
      window.application.menu.items.length > 0 && (
        <ul style={style}>
          {window.application.menu.items.map(function (item) {
            return renderItem(item, 0);
          })}
        </ul>
      )
    );
  }

  function render() {
    const style = {
      padding: 25,
      height: "100%",
      borderRight: "solid 1px #EEE",
    };
    return (
      <div style={style}>
        {renderUser()}
        {renderItems()}
      </div>
    );
  }
  return render();
}

export { Menu };
export default Menu;
