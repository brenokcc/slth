
import { useEffect } from "react";

function GeoMap(props){
    const id = Math.random().toString();

    useEffect(() => {
        const map = L.map(id).setView([props.data.long, props.data.lat], props.data.zoom);
        //map.dragging.disable();
        //map.touchZoom.disable();
        map.doubleClickZoom.disable();
        map.scrollWheelZoom.disable();
        map.boxZoom.disable();
        map.keyboard.disable();
        
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            maxZoom: props.data.max_zoom,
            minZoom: props.data.min_zoom,
            noWrap: true,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);
        const features = []
        props.data.polygons.map(function(feature){features.push(feature);});
        
        const points = {"type": "FeatureCollection", "features": []}
        props.data.points.map(function(feature){points.features.push(feature);});
        features.push(points);

        L.geoJSON(features, {
            style(feature) {
                return feature.properties.style ;
            },
            onEachFeature(feature, layer) {
                layer.on('mouseover', function (e) {
                    if(feature.properties.info) layer.bindPopup(feature.properties.info).openPopup(e.latlng);
                    L.DomEvent.preventDefault(e);
                });
                layer.on('mouseout', function (e) {
                    if(feature.properties.info) layer.closePopup();
                    L.DomEvent.preventDefault(e);
                });
                if(feature.geometry.type=="Point" && feature.properties.label){
                    //L.marker(feature.geometry.coordinates.reverse()).addTo(map).bindPopup(feature.properties.info,{autoClose: false, closeOnClick: false}).openPopup();
                    layer.bindTooltip(feature.properties.label, { permanent: true, offset: [0, 0] });
                }
            },
            pointToLayer(feature, latlng) { return L.circleMarker(latlng); }
        }).addTo(map);
    
      }, []);

    function renderTitle(){
        if(props.data.title) return <h2>{props.data.title}</h2>
    }

    function render(){
        return (
            <div>
                {renderTitle()}
                <div id={id} style={{ height: 600, width: "100%", maxWidth: "100%", maxHeight: "100%"}}></div>
            </div>
        )
    }

    return render()
}

export default GeoMap;

export {GeoMap}
