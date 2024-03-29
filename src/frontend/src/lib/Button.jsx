import { openDialog } from "./Modal";

function Button(props) {
  const url = "/app/" + props.data.url.split("/api/")[1];

  function onClick(e) {
    e.preventDefault();
    openDialog(url);
  }

  function render() {
    return (
      <a href={url} onClick={onClick}>
        {props.data.name}
      </a>
    );
  }
  return render();
}

export { Button };
export default { Button };
