function handleDropdownSelection() {
    const selected = document.getElementById("dropdownSelector").value;
    if (selected === "facilities") {
    showFacilities();
    } else if (selected === "covid") {
    showCovid();
    }
}

function refreshMap() {
    document.getElementById("mapFrame").src = "/empty_map?" + new Date().getTime();
    document.getElementById("page-title").textContent = "Overview - " + getTodayString();
    document.getElementById("new-cases").textContent = "0";
    document.getElementById("hospitalized").textContent = "0";
    document.getElementById("discharged").textContent = "0";
    document.getElementById("deaths").textContent = "0";
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
    document.getElementById("new-cases").textContent = covidData.new_cases;
    document.getElementById("hospitalized").textContent = covidData.hospitalized;
    document.getElementById("discharged").textContent = covidData.discharged;
    document.getElementById("deaths").textContent = covidData.deaths;


    // Hide map filter buttons
    document.getElementById("button-container1").style.display = "none";

    // Show COVID charts
    document.getElementById("covid-charts").style.display = "block";
    // Hide donut chart
    document.getElementById("facility-chart").style.display = "none";
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
  
  // Modify this to show/hide toggle only for facilities
  function handleDropdownSelection() {
    const selected = document.getElementById("dropdownSelector").value;
  
    if (selected === "facilities") {
      showFacilities();
      document.getElementById("map-toggle-container").style.display = "flex";
    } else if (selected === "covid") {
      showCovid();
      document.getElementById("map-toggle-container").style.display = "none";
    }
  }
  