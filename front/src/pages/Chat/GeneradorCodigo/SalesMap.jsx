import React from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const SalesMap = ({ mapData }) => {
  const { title, markers } = mapData; // Desestructuramos los datos del mapa

  if (!markers || markers.length === 0) {
    return <p></p>;
  }

  return (
    <div style={{ marginBottom: "20px" }}>
      <h4>{title}</h4>
      <MapContainer
        center={markers[0]?.coordinates || [0, 0]} // Centra en el primer marcador
        zoom={5}
        style={{ height: "180px", width: "340px" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />
        {markers.map((marker, index) => (
          <Marker key={index} position={marker.coordinates}>
            <Popup>{marker.popup_text}</Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
};

export default SalesMap;