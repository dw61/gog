import React, { useState } from "react"
import { createRoot } from "react-dom/client";
import { APIProvider, Map, AdvancedMarker } from "@vis.gl/react-google-maps";
import data from "../static/data.json"

const NoteCard = () => {
  return (
    <div className="fixed bottom-4 right-4 top-4  z-10 bg-white p-4 rounded-lg shadow-lg max-w-xs font-sans">
      <div className="flex justify-between items-baseline">
        <h2 className="text-2xl font-semibold">$750</h2>
        <span className="text-lg text-red-500 font-semibold">&#9734; 4.5</span> {/* Outlined star */}
      </div>
      {/* Separate div for address and details tags */}
      <div className="flex flex-wrap gap-2 mt-2">
        <span className="text-xs font-semibold text-gray-700 bg-gray-100 rounded-full px-2 py-1">
          2101 Jefferson Park Ave
        </span>
        <span className="text-xs font-semibold text-gray-700 bg-gray-100 rounded-full px-2 py-1">
          4 bedrooms
        </span>
        <span className="text-xs font-semibold text-gray-700 bg-gray-100 rounded-full px-2 py-1">
          2 toilets
        </span>
      </div>
      <div className="flex flex-wrap gap-2 mt-2">
        {/* Tags for features and amenities */}
        <span className="text-xs font-semibold text-green-700 bg-green-100 rounded-full px-2 py-1">GOOD DEAL</span>
        <span className="text-xs font-semibold text-blue-700 bg-blue-100 rounded-full px-2 py-1">
          On premise parking: $50-$100 per month
        </span>
        {/* ... other feature tags as needed ... */}
      </div>
      <div className="border-t border-gray-200 mt-3 pt-2">
        <p className="text-xs text-gray-600">Nice but unresponsive management, rent increase after 1st year.</p>
      </div>
    </div>
  );
};

function Highlight({ detail }) {
  return (
    <div className="fixed bottom-4 right-4 inset-y-0 mx-auto z-10
                    rounded-3xl p-2 w-96
                    border border-solid border-black
                    font-sans bg-emerald-100"
    >
      <span>${detail["How much rent + utility do you pay per month?"]}</span>
      <div>
        <table className="text-xs text-gray-500">
          <tbody>
            <tr>
              <td>What is the street address of your apartment?</td>
              <td className="text-large text-gray-950">{detail["What is the street address of your apartment?"]}</td>
            </tr>
            <tr>
              <td>How many bedrooms do you have?</td>
              <td className="text-large text-gray-950">{detail["How many bedrooms do you have?"]} bd</td>
            </tr>
            <tr>
              <td>How many toilets do you have in total?</td>
              <td className="text-large text-gray-950">{detail["How many toilets do you have in total?"]} ba</td>
            </tr>
            <tr>
              <td>Which month did you sign your lease?</td>
              <td className="text-large text-gray-950">{detail["Which month did you sign your lease?"]}</td>
            </tr>
            <tr>
              <td>How much was your security deposit?</td>
              <td className="text-large text-gray-950">{detail["How much was your security deposit?"]}</td>
            </tr>
            <tr>
              <td>How many people are in your apartment / suite / hall?</td>
              <td className="text-large text-gray-950">{detail["How many people are in your apartment / suite / hall?"]}</td>
            </tr>
            <tr>
              <td>Do you think you got a good deal?</td>
              <td className="text-large text-gray-950">{detail["Do you think you got a good deal?"]}</td>
            </tr>
            <tr>
              <td>Where do you park your car?</td>
              <td className="text-large text-gray-950">{detail["Where do you park your car?"]}</td>
            </tr>
            <tr>
              <td>How much do you pay for parking per month?</td>
              <td className="text-large text-gray-950">{detail["How much do you pay for parking per month?"]}</td>
            </tr>
            <tr>
              <td>Do you have a pet?</td>
              <td className="text-large text-gray-950">{detail["Do you have a pet?"]}</td>
            </tr>
            <tr>
              <td>Was your apartment furnished?</td>
              <td className="text-large text-gray-950">{detail["Was your apartment furnished?"]}</td>
            </tr>
            <tr>
              <td>Does your room get too hot or cold?</td>
              <td className="text-large text-gray-950">{detail["Does your room get too hot or cold?"]}</td>
            </tr>
            <tr>
              <td>Do you suffer from noise?</td>
              <td className="text-large text-gray-950">{detail["Do you suffer from noise?"]}</td>
            </tr>
            <tr>
              <td>Any problems in your room?</td>
              <td className="text-large text-gray-950">{detail["Any problems in your room?"]}</td>
            </tr>
            <tr>
              <td>Any problems with your apartment?</td>
              <td className="text-large text-gray-950">{detail["Any problems with your apartment?"]}</td>
            </tr>
            <tr>
              <td>Any problems with management?</td>
              <td className="text-large text-gray-950">{detail["Any problems with management?"]}</td>
            </tr>
            <tr>
              <td>Overall rating of your apartment</td>
              <td className="text-large text-gray-950">{detail["Overall rating of your apartment"]}</td>
            </tr>
            <tr>
              <td>What do you wish you had known before moving in?</td>
              <td className="text-large text-gray-950">{detail["What do you wish you had known before moving in?"]}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Marker({ detail, setDetail }) {
  return (
    <AdvancedMarker
      position={{ "lat": detail.lat, "lng": detail.lng }}
      onClick={() => setDetail(detail)}
    >
      <span className="property text-base px-2 pt-1.5 pb-1 bg-emerald-100 rounded-full border border-black">${detail["How much rent + utility do you pay per month?"]}</span>
    </AdvancedMarker>
  )
}

function App() {

  let [detail, setDetail] = useState(data[0])

  return (
    <>
      <Highlight detail={detail} />
      {/* <NoteCard /> */}
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
            data.map(apartment =>
              <Marker detail={apartment} setDetail={setDetail} />
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
