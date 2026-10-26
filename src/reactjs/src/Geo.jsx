
import { useEffect } from "react";

function GeoMap(props){
    const id = Math.random().toString();
    let marker = null;
    const icon = L.divIcon({
        className: 'geo-icon',
        html: '<span style="font-size:2rem;padding-top:-20px">📍</span>',
        iconSize: [40, 40]
    });

    useEffect(() => {
        const map = L.map(id).setView([props.data.long, props.data.lat], props.data.zoom);
        //map.dragging.disable();
        //map.touchZoom.disable();
        map.doubleClickZoom.disable();
        map.scrollWheelZoom.disable();
        map.boxZoom.disable();
        map.keyboard.disable();
        
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=cb1_3p4p_1_06f6a50c23755fb1e9dc5226', {
            maxZoom: props.data.max_zoom,
            minZoom: props.data.min_zoom,
            noWrap: true,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);
        const features = []
        props.data.polygons.map(function(feature){features.push(feature);});
        
        const points = {"type": "FeatureCollection", "features": []}
        if(!props.data.heatmap) props.data.points.map(function(feature){points.features.push(feature);});
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

        var cfg = {
            // radius should be small ONLY if scaleRadius is true (or small radius is intended)
            // if scaleRadius is false it will be the constant radius used in pixels
            "radius": .003,
            "maxOpacity": .8,
            // scales the radius based on map zoom
            "scaleRadius": true,
            // if set to false the heatmap uses the global maximum for colorization
            // if activated: uses the data maximum within the current map boundaries
            //   (there will always be a red spot with useLocalExtremas true)
            "useLocalExtrema": true,
            // which field name in your data represents the latitude - default "lat"
            latField: 'lat',
            // which field name in your data represents the longitude - default "lng"
            lngField: 'lng',
            // which field name in your data represents the data value - default "value"
            valueField: 'count'
        };
        const heatpoints = [];
        props.data.points.map(function(point){heatpoints.push({"lng": Number(point.geometry.coordinates[0]), "lat": Number(point.geometry.coordinates[1]), "count": 1});});
        const heatmapLayer = new HeatmapOverlay(cfg);
        // heatpoints = [{lat: -22.2441487, lng:-54.8082846, count: 20},{lat: -22.218248, lng:-54.7838213, count: 1}]
        const testData = {max: 10, data: heatpoints};
        heatmapLayer.setData(testData);
        if (props.data.heatmap){
            heatmapLayer.addTo(map);
        }
        if(props.data.latlng){
            marker = L.marker(props.data.latlng, {icon: icon});
            marker.addTo(map);
            if(props.data.onMapClick){
                props.data.onMapClick(props.data.latlng)
            }
        }

        function onMapClick(e) {
            if(props.data.latlng==null){
                if(marker) marker.remove()
                var latlng = e.latlng;
                marker = L.marker(latlng, {icon: icon});
                marker.addTo(map);
                props.data.onMapClick(e.latlng);
            }
        }
        if(props.data.onMapClick) map.on('click', onMapClick);
    
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
