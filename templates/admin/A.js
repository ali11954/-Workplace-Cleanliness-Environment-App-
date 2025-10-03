document.getElementById('location').addEventListener('change', function(){
  const locationId = this.value;
  window.location.href = `{{ url_for('evaluations') }}?region=${locationId}`;
});

document.getElementById('site').addEventListener('change', function(){
  const locationId = document.getElementById('location').value;
  const siteId = this.value;
  window.location.href = `{{ url_for('evaluations') }}?region=${locationId}&site=${siteId}`;
});

document.getElementById('place').addEventListener('change', function(){
  const locationId = document.getElementById('location').value;
  const siteId = document.getElementById('site').value;
  const placeId = this.value;
  window.location.href = `{{ url_for('evaluations') }}?region=${locationId}&site=${siteId}&place=${placeId}`;
});

$('#region_id').change(function() {
    var regionId = $(this).val();
    $.getJSON('/get_sites/' + regionId, function(sites) {
        var siteSelect = $('#site_id').empty();
        siteSelect.append('<option value="">اختر الموقع</option>');
        $.each(sites, function(i, site) {
            siteSelect.append('<option value="' + site.id + '">' + site.name + '</option>');
        });
        $('#place_id').empty().append('<option value="">اختر المكان</option>');
    });
});

$('#site_id').change(function() {
    var siteId = $(this).val();
    $.getJSON('/get_places/' + siteId, function(places) {
        var placeSelect = $('#place_id').empty();
        placeSelect.append('<option value="">اختر المكان</option>');
        $.each(places, function(i, place) {
            placeSelect.append('<option value="' + place.id + '">' + place.name + '</option>');
        });
    });
});
