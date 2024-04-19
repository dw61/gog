import React, { useState } from "react"
import { createRoot } from "react-dom/client";
import { APIProvider, Map, AdvancedMarker } from "@vis.gl/react-google-maps";
import apartments from "../static/apartments.json"

function Highlight({ apartment }) {

  const script = document.createElement('script');
  script.src = 'https://server.fillout.com/embed/v1/';
  script.async = true;
  document.body.appendChild(script);

  return (
    <div className="fixed lg:bottom-4 lg:right-4 lg:top-4 sm:left-4 sm:right-4 sm:bottom-4 z-10 bg-white p-4 rounded-lg shadow-lg max-w-xs font-sans">
      <div className="flex justify-between items-baseline">
        <h2 className="text-2xl font-semibold">${apartment.rent_per_person}</h2>
        <span className="text-lg text-red-500 font-semibold">&#9734; {apartment.rating}({apartment.count})</span>
      </div>
      <div className="flex flex-wrap gap-2 mt-2 text-xs font-semibold">
        <span className="text-gray-700 bg-orange-100 rounded-full px-2 py-1">
          {apartment.street_address}
        </span>
        <span className="text-gray-700 bg-blue-100 rounded-full px-2 py-1">
          bedrooms,toilets {apartment.bed_toilet}
        </span>
        {/* <span className="text-gray-700 bg-gray-100 rounded-full px-2 py-1">
          2 toilets
        </span> */}
      </div>
      <div className="flex flex-wrap gap-2 mt-2 text-xs font-semibold">
        {apartment.tags.map(tag =>
          <span className="text-green-700 bg-green-100 rounded-full px-2 py-1">{tag}</span>
        )}
        {/* <span className="text-blue-700 bg-blue-100 rounded-full px-2 py-1">
          On premise parking: $50-$100 per month
        </span> */}
      </div>
      <div className="border-t border-gray-200 mt-3 pt-2">
        <p className="text-xs mb-2">Good to know</p>
        <p className="text-xs text-gray-600">{apartment.comment}</p>
      </div>
      <br></br>
      <div className="bottom-0 w-full text-center text-sm" data-fillout-id="x29P9cvL4wus" data-fillout-embed-type="popup" data-fillout-button-text="review my apartment" data-fillout-button-size="small" data-fillout-inherit-parameters></div>
    </div>
  );
};

function Marker({ apartment, setApartment }) {
  return (
    <AdvancedMarker
      position={{ "lat": apartment.lat, "lng": apartment.lng }}
      onClick={() => setApartment(apartment)}
    >
      <span className="property text-base px-2 pt-1.5 pb-1 bg-emerald-100 rounded-full border border-black"
      onMouseOver={() => setApartment(apartment)}
      >
        ${apartment.rent_per_person}
      </span>
    </AdvancedMarker>
  )
}

function App() {

  let [apartment, setApartment] = useState(apartments[1])

  return (
    <>
      <Highlight apartment={apartment} />
      <APIProvider apiKey={"AIzaSyCyRQ3xTOLkHkgLjqwg9rCtrgoWcRpzOJA"}>
        <Map
          style={{ height: '100vh' }}
          defaultCenter={{ lat: 38.034, lng: -78.507 }}
          mapId="9c2a7d18fe4584e5" // airbnb, or "cec037ac6a1784e1"
          defaultZoom={15}
          gestureHandling="greedy"
          isFractionalZoomEnabled
          scaleControl
          disableDefaultUI
        >
          {
            apartments.map(apartment =>
              <Marker apartment={apartment} setApartment={setApartment} />
            )
          }
        </Map>
      </APIProvider>
    </>
  );
}

const root = createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
