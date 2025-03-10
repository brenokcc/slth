function reloadState() {
  document.querySelectorAll(".reloadable").forEach(function (element) {
    if(element.querySelectorAll(".reloadable").length==0) window[element.id]();
  });
}

export { reloadState };
export default reloadState;
