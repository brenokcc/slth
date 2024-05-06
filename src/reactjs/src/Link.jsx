import { openDialog, openIFrameDialog } from "./Modal";
import { appurl } from "./Request";
import { toLabelCase } from "./Utils";

function Link({
  id,
  href,
  modal,
  imodal,
  children,
  onClick,
  dataLabel,
  style,
}) {
  const url = href && href.indexOf("/media/") < 0 ? appurl(href) : href;

  function onClickDefault(e) {
    if (url.indexOf("http") == 0) {
      document.location.href = url;
    } else {
      e.preventDefault();
      if (modal) openDialog(url);
      else if (imodal) openIFrameDialog(url);
      else window.load(url);
    }
  }

  function render() {
    return (
      <a
        id={id}
        onClick={onClick || onClickDefault}
        href={url || "#"}
        data-label={toLabelCase(dataLabel)}
        style={style}
      >
        {children}
      </a>
    );
  }

  return render();
}

export { Link };
export default Link;
