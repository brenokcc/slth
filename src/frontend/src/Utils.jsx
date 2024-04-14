function toLabelCase(text) {
  if (text != null)
    text = text
      .toString()
      .replace("-", "")
      .normalize("NFD")
      .replace("_", "")
      .toLowerCase();
  return text;
}

export default toLabelCase;
export { toLabelCase };
