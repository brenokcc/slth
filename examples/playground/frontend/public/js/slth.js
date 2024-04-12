function reloadAll() {
  document.querySelectorAll(".reloadable").forEach(function (element) {
    window[element.id]();
  });
}
