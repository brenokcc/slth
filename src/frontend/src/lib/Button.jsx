import { Icon } from "./Icon";

function Button({ id, onClick, icon, label, display }) {
  function render() {
    const style = {
      padding: 12,
      textDecoration: "none",
      whiteSpace: "nowrap",
      borderRadius: 5,
      margin: 5,
      backgroundColor: "#1351b4",
      color: "white",
      cursor: "pointer",
      display: display || "block",
    };
    return (
      <a
        id={id}
        style={style}
        onClick={(e) => {
          e.preventDefault();
          onClick();
        }}
      >
        {icon && <Icon icon={icon} />}
        {label || ""}
      </a>
    );
  }
  return render();
}

export { Button };
export default Button;
