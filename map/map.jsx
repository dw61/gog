import React, { useState } from "react"
import { createRoot } from "react-dom/client";
import { APIProvider, Map, AdvancedMarker } from "@vis.gl/react-google-maps";
import apartments from "../static/apartments.json"
import dataStatus from "../static/data-status.json"

function dateLabel(value) {
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric", month: "short", day: "numeric", timeZone: "UTC"
  });
}

function Highlight(props) {
  return (
    <div
      role="region"
      aria-label="Apartment details"
      className="fixed bottom-4 right-4 left-4 lg:left-auto lg:top-4 z-10 bg-white p-4 rounded-lg shadow-lg max-w-xs max-h-[calc(100dvh-8rem)] lg:max-h-[calc(100dvh-2rem)] overflow-y-auto font-sans">
      <div className="flex justify-end mb-2">
        <button
          type="button"
          onClick={() => props.setShowHighlight(false)}
          aria-label="Close apartment details"
          className="px-2 py-1 rounded-lg hover:bg-gray-100 focus-visible:outline-2"
        >
          Close &times;
        </button>
      </div>
      <div className="flex justify-between items-baseline">
        <h2 className="text-2xl font-semibold">${props.apartment.rent_per_person}</h2>
        <span className="text-lg text-red-500 font-semibold">
          {props.apartment.rating == null ? "Not rated" : `☆ ${props.apartment.rating}`} ({props.apartment.count})
        </span>
      </div>
      <div className="flex flex-wrap gap-2 mt-2 text-xs font-semibold">
        <span className="text-gray-700 bg-orange-100 rounded-full px-2 py-1">
          {props.apartment.street_address}
        </span>
        <span className="text-gray-700 bg-blue-100 rounded-full px-2 py-1">
          bedrooms,toilets {props.apartment.bed_toilet}
        </span>
        {/* <span className="text-gray-700 bg-gray-100 rounded-full px-2 py-1">
          2 toilets
        </span> */}
      </div>
      <div className="flex flex-wrap gap-2 mt-2 text-xs font-semibold">
        {props.apartment.tags.map((tag, index) =>
          <span key={`${tag}-${index}`} className="text-green-700 bg-green-100 rounded-full px-2 py-1">{tag}</span>
        )}
        {/* <span className="text-blue-700 bg-blue-100 rounded-full px-2 py-1">
          On premise parking: $50-$100 per month
        </span> */}
      </div>
      <div className="border-t border-gray-200 mt-3 pt-2">
        <p className="text-xs mb-2">Good to know</p>
        <p className="text-xs text-gray-600 whitespace-pre-line">{props.apartment.comment}</p>
      </div>
      <br />
      <div className="w-full text-center text-sm">
        <a href="/review/" className="inline-block bg-gray-800 text-white px-4 py-2 rounded-lg hover:bg-gray-700 focus-visible:outline-2">
          review my apartment
        </a>
      </div>
    </div>
  );
};

function Marker(props) {
  return (
    <AdvancedMarker
      position={{ "lat": props.apartment.lat, "lng": props.apartment.lng }}
      onClick={() => {
        props.setApartment(props.apartment);
        props.setShowHighlight(true);
      }}
    >
      <span
        className="
        property text-base px-2 pt-1.5 pb-1 bg-emerald-100 rounded-full border border-black
        hover:bg-gray-800 hover:text-white
        "
        onPointerEnter={() => {
          props.setApartment(props.apartment);
          props.setShowHighlight(true)
        }}
      >
        ${props.apartment.rent_per_person}
      </span>
    </AdvancedMarker>
  )
}

function App() {

  let [apartment, setApartment] = useState(apartments[0])
  let [showHighlight, setShowHighlight] = useState(false)

  return (
    <>
      <aside className="fixed top-3 left-3 z-10 rounded-lg bg-white p-3 shadow-lg font-sans text-xs max-w-[220px]" aria-label="Review data freshness">
        <p className="font-semibold">GetOffGrounds</p>
        <p>Latest review: <time dateTime={dataStatus.latest_review_at}>{dateLabel(dataStatus.latest_review_at)}</time></p>
        <p className="text-gray-600">
          {dataStatus.source === "fillout" && dataStatus.published_at
            ? <>Map updated: <time dateTime={dataStatus.published_at}>{dateLabel(dataStatus.published_at)}</time></>
            : "Archived reviews · automatic sync pending"}
        </p>
        <a href="/review/" className="inline-block mt-2 underline">Add your review</a>
      </aside>
      {showHighlight &&
        <Highlight
          apartment={apartment}
          setShowHighlight={setShowHighlight}
        />}
      <APIProvider apiKey={"AIzaSyCyRQ3xTOLkHkgLjqwg9rCtrgoWcRpzOJA"}>
        <div>
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
                <Marker
                  key={`${apartment.lat},${apartment.lng}`}
                  apartment={apartment}
                  setApartment={setApartment}
                  setShowHighlight={setShowHighlight}
                />
              )
            }
          </Map>
        </div>
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
