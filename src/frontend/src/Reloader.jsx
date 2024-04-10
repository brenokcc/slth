function reloadState() {
  document.querySelectorAll(".reloadable").forEach(function (element) {
    window[element.id]();
  });
}

export { reloadState };
export default reloadState;
