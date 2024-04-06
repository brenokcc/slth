import { loadurl, loaddata } from "./Root";
import { appurl } from "./Request";
import Icon from "./Icon";

function Menu() {
  function renderUser() {
    const img = {
      width: 200,
      height: 200,
      borderRadius: "50%",
    };
    return (
      <div align="center">
        <div>
          <img src="/images/user.png" style={img} />
        </div>
        <div>Breno Silva</div>
      </div>
    );
  }

  function toggleItem(e) {
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
      e.preventDefault();
      e.stopPropagation();
      e.cancelBubble = true;
      return false;
    }
  }

  function renderItem(item, level) {
    const style = {
      display: level == 0 ? "block" : "none",
      cursor: "pointer",
      paddingLeft: 15,
      paddingTop: 5,
      paddingBottom: 5,
    };
    if (item.url) {
      return (
        <li key={Math.random()} style={style}>
          <a
            onClick={function (e) {
              e.preventDefault();
              loaddata(e.target.href);
            }}
            href={appurl(item.url)}
          >
            {level == 0 && (
              <Icon icon={item.icon || "dot-circle"} style={{ padding: 5 }} />
            )}
            {item.label}
          </a>
        </li>
      );
    } else {
      return (
        <li key={Math.random()} onClick={toggleItem} style={style}>
          {level == 0 && (
            <Icon icon={item.icon || "dot-circle"} style={{ padding: 5 }} />
          )}
          {item.label}
          <ul style={{ display: "none", paddingLeft: 15 }}>
            {item.items.map(function (subitem) {
              return renderItem(subitem, level + 1);
            })}
          </ul>
        </li>
      );
    }
  }

  function renderItems() {
    const style = { padding: 0 };
    return (
      <ul style={style}>
        {window.application.menu.items.map(function (item) {
          return renderItem(item, 0);
        })}
      </ul>
    );
  }

  function render() {
    const style = { padding: 25 };
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
