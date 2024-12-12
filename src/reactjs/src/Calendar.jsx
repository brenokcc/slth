import Icon, { IconButton } from "./Icon";
import Theme from "./Theme";
import StyleCheet from "./StyleSheet";


function Calendar(props){
    StyleCheet(`
        .calendar table{
            width: 100%;
            border-spacing: 0px;
            border-collapse: collapse;
            margin-top: 15px;
            margin-bottom: 15px;
        }
        .calendar .day{
            margin-left: 17px;
            text-align: right;
            padding-right: 2px;
            padding-top: 2px;
            float: right;
            font-size: 0.8rem;
        }
        .calendar td{
            vertical-align: top;
            width: 14.2%;
            height: 55px;
            border: solid 1px #EEE;
        }
        .calendar .number{
            border-radius: 50%;
            color: white;
            display: block;
            width: 30px;
            height: 30px;
            margin: auto;
            cursor: pointer;
            line-height: 2rem;
        }
        .calendar .total{
            padding: 10px;
            text-align: center;
        }
        .calendar .arrows{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
        }
        .calendar h3{
            margin: 0px;
        }       
    `)
    const days = ["DOM", "SEG", "TER", "QUA", "QUI", "SEX", "SAB"];
    const months = [
        "JANEIRO",
        "FEVEVEIRO",
        "MARÇO",
        "ABRIL",
        "MAIO",
        "JUNHO",
        "JULHO",
        "AGOSTO",
        "SETEMRO",
        "OUTUBRO",
        "NOVEMBRO",
        "DEZEMBRO",
    ];
    const today = new Date();
    const selected = props.data.day
        ? new Date(
            props.data.year,
            props.data.month - 1,
            props.data.day
        )
        : null;
    var rows = [[], [], [], [], [], []];
    var month = props.data.month - 1;
    var start = new Date(props.data.year, props.data.month - 1, 1);
    while (start.getDay() > 1) start.setDate(start.getDate() - 1);
    var i = 0;
    while (start.getMonth() <= month || rows[i].length < 7) {
        if (rows[i].length == 7) i += 1;
        if (i == 5) break;
        rows[i].push({
        date: start.getDate(),
        total: props.data.total[start.toLocaleDateString("pt-BR")],
        today: start.getDate() === today.getDate(),
        selected: selected ? start.getDate() == selected.getDate() : false,
        });
        start.setDate(start.getDate() + 1);
    }
    function render(){    
        return (
            <div className="calendar">
                <div className="arrows">
                    <div>
                    <IconButton
                        default
                        icon="arrow-left"
                        onClick={() =>
                        props.onChange(
                            null,
                            props.data.previous.month,
                            props.data.previous.year
                        )
                        }
                    />
                    </div>
                    <div>
                    <h3 align="center">
                        {months[props.data.month - 1]} {props.data.year}
                    </h3>
                    {props.data.day && (
                        <div align="center" className="day">
                        {new Date(
                            props.data.year,
                            props.data.month - 1,
                            props.data.day
                        ).toLocaleDateString("pt-BR")}
                        <Icon
                            default
                            icon="x"
                            onClick={() =>
                            props.onChange(
                                null,
                                props.data.month,
                                props.data.year
                            )
                            }
                            style={{ marginLeft: 10, cursor: "pointer" }}
                        />
                        </div>
                    )}
                    </div>
                    <div>
                    <IconButton
                        default
                        icon="arrow-right"
                        onClick={() =>
                        props.onChange(
                            null,
                            props.data.next.month,
                            props.data.next.year
                        )
                        }
                    />
                    </div>
                </div>
                <table>
                    <thead>
                    <tr>
                        {days.map((day) => (
                        <th key={Math.random()}>{day}</th>
                        ))}
                    </tr>
                    </thead>
                    <tbody>
                    {rows.map((row) => (
                        <tr key={Math.random()}>
                        {row.map((item) => (
                            <td key={Math.random()}>
                            <div className="day">
                                {item.today ? (
                                <span style={{ textDecoration: "underline" }}>
                                    {item.date}
                                </span>
                                ) : (
                                item.date + item.today
                                )}
                            </div>
                            {item.total && (
                                <div
                                className="total"
                                onClick={() =>
                                    props.onChange(
                                    item.date,
                                    props.data.month,
                                    props.data.year
                                    )
                                }
                                >
                                <div className="number" style={{backgroundColor: Theme.colors.primary, textDecoration: item.selected ? "underline" : "normal", display: "inline-block"}}>
      
                                    {item.total}
                                </div>
                                </div>
                            )}
                            {!item.total && <div className="total">&nbsp;</div>}
                            </td>
                        ))}
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>
        );
    }
    return render();
}

export {Calendar};
export default Calendar;
