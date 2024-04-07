(g => { var h, a, k, p = "The Google Maps JavaScript API", c = "google", l = "importLibrary", q = "__ib__", m = document, b = window; b = b[c] || (b[c] = {}); var d = b.maps || (b.maps = {}), r = new Set, e = new URLSearchParams, u = () => h || (h = new Promise(async (f, n) => { await (a = m.createElement("script")); e.set("libraries", [...r] + ""); for (k in g) e.set(k.replace(/[A-Z]/g, t => "_" + t[0].toLowerCase()), g[k]); e.set("callback", c + ".maps." + q); a.src = `https://maps.${c}apis.com/maps/api/js?` + e; d[q] = f; a.onerror = () => h = n(Error(p + " could not load.")); a.nonce = m.querySelector("script[nonce]")?.nonce || ""; m.head.append(a) })); d[l] ? console.warn(p + " only loads once. Ignoring:", g) : d[l] = (f, ...n) => r.add(f) && u().then(() => d[l](f, ...n)) })({
  key: "AIzaSyCyRQ3xTOLkHkgLjqwg9rCtrgoWcRpzOJA",
  v: "beta",
});

function isMobileDevice() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

let apartments;
fetch("static/apartments.json")
  .then(response => response.json())
  .then(data => {
    apartments = data;
    initMap();
  });

async function initMap() {
  // Request needed libraries.
  const { Map } = await google.maps.importLibrary("maps");
  const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
  const center = { lat: 38.034, lng: -78.507 };
  const map = new Map(document.getElementById("map"), {
    zoom: 15,
    center,
    zoomControl: false,
    mapTypeControl: false,
    scaleControl: true,
    streetViewControl: false,
    fullscreenControl: false,
    isFractionalZoomEnabled: true,
    gestureHandling: "auto",
    mapId: "9c2a7d18fe4584e5", // airbnb, or "cec037ac6a1784e1"
  });

  for (const property of apartments) {
    const marker = new google.maps.marker.AdvancedMarkerElement({
      map,
      content: buildContent(property),
      position: property.position,
      title: property.address1,
      collisionBehavior: "OPTIONAL_AND_HIDES_LOWER_PRIORITY",
    });
    if (isMobileDevice()) {
      marker.content.addEventListener("pointerover", () => {
        marker.content.classList.toggle("highlight");
        marker.zIndex = 1;
      });
    } else {
      marker.content.addEventListener("pointerover", () => {
        marker.content.classList.add("highlight");
        marker.zIndex = 1;
      });
      marker.content.addEventListener("pointerout", () => {
        marker.content.classList.remove("highlight");
      });
    }
  }
}

function buildContent(property) {
  const content = document.createElement("div");

  content.classList.add("property");
  content.innerHTML = `
    <span>$${property.price}</span>
    <div class="details">
        <div class="address">${property.address1}</div>
        <div class="features">
            <span>${property.bedroom} bd</span>
            <span>${property.bathroom} ba</span>
            <p>parking ${property.parking}</p>
            <p>furnished ${property.furnished}</p>
            <p>safety ${property.safety}</p>
            <p>quietness ${property.quietness}</p>
            <p>overall ${property.overall}</p>
        </div>
    </div>
    `;
  return content;
}

// const highlightContainer = document.getElementById('highlightContainer');
// highlightContainer.innerHTML = buildContent(apartments[0]);