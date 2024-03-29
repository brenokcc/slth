import { openDialog } from "./Modal";

function Action(props) {
  const url = "/app/" + props.data.url.split("/api/")[1];

  function onClick(e) {
    e.preventDefault();
    openDialog(url);
  }

  function render() {
    const style = { padding: 5 };
    return (
      <a href={url} onClick={onClick} style={style}>
        {props.data.name}
      </a>
    );
  }
  return render();
}

export { Action };
export default { Action };
