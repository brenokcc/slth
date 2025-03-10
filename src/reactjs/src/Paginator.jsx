import Button from "./Button";
import StyleSheet from "./StyleSheet";

function Paginator(props){
    StyleSheet(`
      .paginator{
        display: flex;
        justify-content: space-between;
        line-height: 4rem;
        align-items: baseline;
        background: var(--fieldset-background);
        padding: 10px;
        border-radius: var(--border-radius);
      }
      .paginator .inline{
        display: inline;
        padding-right: 10px;
      }
      .paginator select{
        margin-left: 10px;
        margin-right: 10px;
        height: 2.5rem;
        padding-left: 5px;
        padding-right: 5px;
        text-align: center;
        background-color: var(--default-background)
      }
      .paginator input{
        background-color: var(--input-background);
        border: var(--input-border)
      }
    `)
    
    function render(){
        return (
            props.data.page.total > 1 && (
              <div className="paginator">
                <div>
                  {window.innerWidth > 800 && (
                    <div className="inline">
                      Exibir
                      <select
                        name="page_size"
                        onChange={() => props.onChange(1)}
                        value={props.data.page.size}
                      >
                        {props.data.page.sizes.map(function (size) {
                          return <option key={Math.random()}>{size}</option>;
                        })}
                      </select>
                    </div>
                  )}
                  {window.innerWidth > 800 && <div className="inline">|</div>}
      
                  <div className="inline">
                    {props.data.start} - {props.data.end} de {props.total}
                  </div>
                </div>
                <div>
                  <div className="inline">
                    <span>Página</span>
                    <input
                      type="text"
                      name="page"
                      defaultValue={props.data.page.current}
                      style={{
                        width: 30,
                        marginLeft: 10,
                        marginRight: 10,
                        height: "2rem",
                        textAlign: "center",
                      }}
                      onKeyDown={function (e) {
                        if (e.key == "Enter") {
                          e.preventDefault();
                          props.onChange(
                            e.target.value < 0
                              ? 1
                              : Math.min(e.target.value, props.data.page.total)
                          );
                        }
                      }}
                    />
                    <div className="inline">|</div>
                    {props.data.page.previous && (
                      <Button
                        icon="chevron-left"
                        default
                        display="inline"
                        onClick={() => props.onChange(props.data.page.previous)}
                      />
                    )}
                    {props.data.page.next && (
                      <Button
                        icon="chevron-right"
                        default
                        display="inline"
                        onClick={() => props.onChange(props.data.page.next)}
                      />
                    )}
                  </div>
                </div>
              </div>
            )
          );
    }
    return render();
}

export {Paginator};
export default Paginator;
