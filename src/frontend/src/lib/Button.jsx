import { Icon } from "./Icon";

function Button({ id, onClick, icon, label, display, primary }) {
  function render() {
    const style = {
      padding: 12,
      textDecoration: "none",
      whiteSpace: "nowrap",
      borderRadius: 5,
      margin: 5,
      cursor: "pointer",
      display: display || "block",
      width: "fit-content",
    };
    if (primary) {
      style.backgroundColor = "#1351b4";
      style.color = "white";
    } else {
      style.border = "solid 1px #1351b4";
      style.color = "#1351b4";
    }
    return (
      <a
        id={id}
        style={style}
        onClick={(e) => {
          e.preventDefault();
          onClick();
        }}
      >
        {icon && <Icon icon={icon} style={{ marginRight: 10 }} />}
        {label || ""}
      </a>
    );
  }
  return render();
}

export { Button };
export default Button;
