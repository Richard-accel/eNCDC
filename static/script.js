const patientCasesData = JSON.parse(document.getElementById("patient-cases-json").textContent);

function handleDropdownSelection() {
  const selected = document.getElementById("dropdownSelector").value;

  if (selected === "facilities") {
      showFacilities();
      document.getElementById("map-toggle-container").style.display = "flex";
      document.getElementById("patient-filter-buttons").style.display = "none";
      showNormalKPI();
  } else if (selected === "covid") {
      showCovid();
      document.getElementById("map-toggle-container").style.display = "none";
      document.getElementById("patient-filter-buttons").style.display = "none";
      showNormalKPI();
  } else if (selected === "patientcases") {
      showPatientCases(); // ✅ Already load map + fetch KPI + show correct KPI
      document.getElementById("map-toggle-container").style.display = "none";
      document.getElementById("patient-filter-buttons").style.display = "flex";

  }
}






function refreshMap() {
  const selected = document.getElementById("dropdownSelector").value;
  const isPolygon = document.getElementById("mapToggle").checked;

  // ✅ Only run when in Facilities mode
  if (selected === "facilities") {
      if (isPolygon) {
          // Polygon view
          document.getElementById("mapFrame").src = "/map/polygon?" + new Date().getTime();
      } else {
          // POI view
          document.getElementById("mapFrame").src = "/map/facilities?" + new Date().getTime();
      }
  }
}



function showFacilities() {
    // Load the map
    document.getElementById("mapFrame").src = "/map/facilities?" + new Date().getTime();
    document.getElementById("page-title").textContent = "Facilities in Malaysia - " + getTodayString();

    // Show filter buttons
    document.getElementById("button-container1").style.display = "block";

    // Hide COVID charts
    document.getElementById("covid-charts").style.display = "none";

    // Show the facility donut chart
    document.getElementById("facility-chart").style.display = "block";

    // Update KPI box labels
    document.getElementById("new_case-label").textContent = "Total Facilities";
    document.getElementById("hospitalized-label").textContent = "Clinic Count";
    document.getElementById("discharged-label").textContent = "Pharmacy Count";
    document.getElementById("deaths-label").textContent = ""; // Hide or clear if unused

    // Update KPI box values
    document.getElementById("new-cases").textContent = covidData.facility_total;
    document.getElementById("hospitalized").textContent = covidData.clinic_count;
    document.getElementById("discharged").textContent = covidData.pharmacy_count;
    document.getElementById("deaths").textContent = ""; // Clear content for unused KPI
    // Hide 4th KPI box (Deaths)
    document.querySelectorAll('.stat-box')[3].style.display = "none";

    document.getElementById("fullscreen-map-btn").style.display = "none";

}

function showClinics() {
    document.getElementById("mapFrame").src = "/map/clinic?" + new Date().getTime();
    document.getElementById("page-title").textContent = "Clinics in Malaysia - " + getTodayString();

}
function showPharmacy() {
    document.getElementById("mapFrame").src = "/map/pharmacy?" + new Date().getTime();
    document.getElementById("page-title").textContent = "Pharmacy in Malaysia - " + getTodayString();

}

function showCovid() {
  document.getElementById("mapFrame").src = "/map/covid?" + new Date().getTime();
  document.getElementById("page-title").textContent = "COVID-19 Malaysia - " + covidData.latest_case_date;

  // Update KPI box labels
  document.getElementById("new_case-label").textContent = "New Cases";
  document.getElementById("hospitalized-label").textContent = "Hospitalized";
  document.getElementById("discharged-label").textContent = "Discharged";
  document.getElementById("deaths-label").textContent = "Deaths";

  // Update KPI values
  document.getElementById("new-cases").textContent = covidData.new_cases;
  document.getElementById("hospitalized").textContent = covidData.hospitalized;
  document.getElementById("discharged").textContent = covidData.discharged;
  document.getElementById("deaths").textContent = covidData.deaths;

  // Show 4 KPI boxes
  document.querySelectorAll('.stat-box')[3].style.display = "block";

  // Hide map filter buttons
  document.getElementById("button-container1").style.display = "none";

  // Show COVID charts
  document.getElementById("covid-charts").style.display = "block";
  
  // Hide donut chart
  document.getElementById("facility-chart").style.display = "none";

  document.getElementById("fullscreen-map-btn").style.display = "none";
}


function getTodayString() {
    const today = new Date();
    return today.toLocaleDateString("en-GB", {
        year: "numeric",
        month: "long",
        day: "numeric"
    });
}

// === JS for toggleMapFastapi ===
function toggleMapFastapi() {
    const toggle = document.getElementById('mapToggle');
    const iframe = document.getElementById('mapFrame');
    const buttons = document.getElementById('button-container1');
  
    if (toggle.checked) {
      iframe.src = "/map/polygon?" + new Date().getTime();
      buttons.style.display = "none";
    } else {
      iframe.src = "/map/facilities?" + new Date().getTime();
      buttons.style.display = "block";
    }
  }

  function updatePatientCasesKPI(conditionFilter = "") {
    let submitted = 0;
    let closed = 0;
    let notSubmitted = 0;
  
    patientCasesData.forEach(item => {
        if (conditionFilter && item.conditionname && item.conditionname.toLowerCase() !== conditionFilter.toLowerCase()) {
            return; // Skip not matched condition
        }
  
        if (item.casestatus) {
            const status = item.casestatus.toLowerCase();
            if (status === "submitted") submitted++;
            else if (status === "closed") closed++;
            else if (status === "not submitted") notSubmitted++;
        }
    });
  
    document.getElementById("submitted-count").textContent = submitted;
    document.getElementById("closed-count").textContent = closed;
    document.getElementById("not-submitted-count").textContent = notSubmitted;
  }
  
  let currentConditionFilter = ""; // track condition filter

  function showPatientCases() {
    document.getElementById("mapFrame").src = "/map/patientcases?" + new Date().getTime();
    document.getElementById("page-title").textContent = "Patient Cases in Malaysia - " + getTodayString();

    // Hide other sections
    document.getElementById("covid-charts").style.display = "none";
    document.getElementById("facility-chart").style.display = "none";
    document.getElementById("button-container1").style.display = "none";

    // Show patient filter buttons
    document.getElementById("patient-filter-buttons").style.display = "flex";

    // 🚀 Force update patient cases KPI immediately (even no filter)
    fetchPatientCasesKPI();

    // Show patient KPI box, hide old KPI box
    showPatientKPI();

    document.getElementById("fullscreen-map-btn").style.display = "inline-block";

}
  
function showDengueCases() {
  document.getElementById("mapFrame").src = "/map/patientcases/dengue?" + new Date().getTime();
  document.getElementById("page-title").textContent = "Patient Cases - Dengue";
  fetchPatientCasesKPI();  // ✅ Fetch fresh from backend
}

function showInfluenzaCases() {
  document.getElementById("mapFrame").src = "/map/patientcases/influenza?" + new Date().getTime();
  document.getElementById("page-title").textContent = "Patient Cases - Influenza";
  fetchPatientCasesKPI();  // ✅ Fetch fresh from backend
}


function showNormalKPI() {
  document.querySelector('.stats-overview').style.display = "flex";   // show old 4 box
  document.getElementById('patient-stats-overview').style.display = "none"; // hide patient 3 box
}

function showPatientKPI() {
  document.querySelector('.stats-overview').style.display = "none";   // hide old 4 box
  document.getElementById('patient-stats-overview').style.display = "flex"; // show patient 3 box
}

async function fetchPatientCasesKPI() {
  const response = await fetch('/kpi/patientcases');
  const data = await response.json();

  document.getElementById("submitted-count").textContent = data.submitted;
  document.getElementById("closed-count").textContent = data.closed;
  document.getElementById("not-submitted-count").textContent = data.not_submitted;
}



function openFullscreenMap() {
  const iframeSrc = document.getElementById("mapFrame").src;
  document.getElementById("fullscreen-map-frame").src = iframeSrc;
  document.getElementById("fullscreen-map-overlay").style.display = "block";
}

function closeFullscreenMap() {
  document.getElementById("fullscreen-map-overlay").style.display = "none";
}

