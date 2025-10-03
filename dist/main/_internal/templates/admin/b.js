document.addEventListener('DOMContentLoaded', function () {
    const regionSelect = document.getElementById('region');
    const siteSelect = document.getElementById('site');
    const locationSelect = document.getElementById('location');

    function loadSites(regionId, selectedSiteId = null) {
        siteSelect.innerHTML = '<option value="" disabled>تحميل المواقع...</option>';
        siteSelect.disabled = true;
        locationSelect.innerHTML = '<option value="" disabled>اختر المكان</option>';
        locationSelect.disabled = true;

        fetch('/get_sites/' + regionId)
            .then(response => response.json())
            .then(data => {
                siteSelect.innerHTML = '<option value="" disabled selected>اختر الموقع</option>';
                data.forEach(site => {
                    const option = document.createElement('option');
                    option.value = site.id;
                    option.textContent = site.name;
                    siteSelect.appendChild(option);
                });
                siteSelect.disabled = false;
                if (selectedSiteId) {
                    siteSelect.value = selectedSiteId;
                    loadPlaces(selectedSiteId, "{{ selected_place_id or '' }}");
                }
            });
    }

    function loadPlaces(siteId, selectedPlaceId = null) {
        locationSelect.innerHTML = '<option value="" disabled>تحميل الأماكن...</option>';
        locationSelect.disabled = true;

        fetch('/get_places/' + siteId)
            .then(response => response.json())
            .then(data => {
                locationSelect.innerHTML = '<option value="" disabled selected>اختر المكان</option>';
                data.forEach(place => {
                    const option = document.createElement('option');
                    option.value = place.id;
                    option.textContent = place.name;
                    locationSelect.appendChild(option);
                });
                locationSelect.disabled = false;
                if (selectedPlaceId) {
                    locationSelect.value = selectedPlaceId;
                }
            });
    }

    regionSelect.addEventListener('change', function () {
        const regionId = this.value;
        if (regionId) {
            loadSites(regionId);
        }
    });

    siteSelect.addEventListener('change', function () {
        const siteId = this.value;
        if (siteId) {
            loadPlaces(siteId);
        }
    });

    // عند تحميل الصفحة - تعيين القيم المختارة وتحميل القوائم بشكل متسلسل
    {% if selected_regions_id %}
        loadSites("{{ selected_regions_id }}", "{{ selected_site_id or '' }}");
    {% endif %}
});
