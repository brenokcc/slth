import { ComponentFactory } from "./Factory";

function Field(props) {
  function render() {
    const style = { width: props.width + "%", marginTop: 5, marginBottom: 5 };
    return (
      <>
        <div style={style}>
          <strong>{props.data.label}</strong>
          <br></br>
          <span>{props.data.value}</span>
        </div>
      </>
    );
  }
  return render();
}

function Fieldset(props) {
  function getTitle() {
    return <h2>{props.data.title}</h2>;
  }

  function getContent() {
    if (Array.isArray(props.data.data)) {
      return props.data.data.map(function (item) {
        if (Array.isArray(item)) {
          return (
            <div key={Math.random()} style={{ display: "flex" }}>
              {item.map((field) => (
                <Field
                  key={Math.random()}
                  data={field}
                  width={100 / item.length}
                />
              ))}
            </div>
          );
        } else {
          return (
            <div key={Math.random()}>
              <Field data={item} width={100} />
            </div>
          );
        }
      });
    } else {
      return <ComponentFactory data={props.data.data} />;
    }
  }

  function render() {
    return (
      <>
        {getTitle()}
        {getContent()}
      </>
    );
  }
  return render();
}
//<div>{JSON.stringify(props.data.data)}</div>
function Object(props) {
  function render() {
    return (
      <>
        <h1>{props.data.title}</h1>
        {props.data.data.map(function (item, i) {
          return <ComponentFactory key={Math.random()} data={item} />;
        })}
      </>
    );
  }
  return render();
}

export { Fieldset, Object };
export default Object;
