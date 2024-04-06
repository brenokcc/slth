import loadurl from "./Root";
import { appurl } from "./Request";

const APPLICATION_DATA = localStorage.getItem("application");

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

  function renderItem(item) {
    if (item.url) {
      return (
        <li key={Math.random()}>
          <a
            onClick={function (e) {
              e.preventDefault();
              loadurl(e.target.href);
            }}
            href={appurl(item.url)}
          >
            {item.label}
          </a>
        </li>
      );
    } else {
      return (
        <li key={Math.random()}>
          {item.label}
          <ul>
            {item.items.map(function (subitem) {
              return renderItem(subitem);
            })}
          </ul>
        </li>
      );
    }
  }

  function renderItems() {
    return (
      APPLICATION_DATA && (
        <ul>
          {JSON.parse(APPLICATION_DATA).menu.items.map(function (item) {
            return renderItem(item);
          })}
        </ul>
      )
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
