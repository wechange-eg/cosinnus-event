
// reading out the selected dates, formatting then and putting them into the form for django
$('#form-event').submit(function() {
  var totalForms = 0;
  var newFormIdx = $('#id_suggestions-INITIAL_FORMS').val();
  var formEvent = $(this);

  var addSuggestionToForm = function(idx, datum, time) {
    if (!idx) { // no form index, so a new suggestion form needs creating
      idx = newFormIdx;
      newFormIdx++;
    }
    console.log(idx);

    var name = 'suggestions-' + idx + '-from_date'
    var dateTime = moment(datum + ' ' + time).format(cosinnus_datetime_format);
    console.log('datetime', dateTime);

    // the from_date input
    $('<input />')
      .attr('type', 'hidden')
      .attr('id', 'id_' + name)
      .attr('name', name)
      .attr('value', dateTime)
      .appendTo(formEvent);

    // to_date unused atm; to_date == from_date
    name = name.replace('from_date', 'to_date');
    $('<input />')
      .attr('type', 'hidden')
      .attr('id', 'id_' + name)
      .attr('name', name)
      .attr('value', dateTime)
      .appendTo(formEvent);

    // increase number of forms for management form
    totalForms++;
  };
  
  var dateList = [];
  var hasErrors = false;
  
  $('#calendar-doodle-days-selector-list table tbody tr').each(function() {
    var datum = $(this).attr('data-date');
    if (!datum) return;

    var time1 = $(this).find('input').first();
    //var time2 = $(this).find('input').last();
    
    // support entries like '2130' and empty entries
    var time_val = time1.val() || '00:00';
    if (isNaN(time_val.replace(':',''))) {
        // some item was entered incorrectly
        hasErrors = true;
    }
    
    if (time_val.length <=2 && time_val.length >= 1) {
        time_val = time_val + ':00';
    }
    if (time_val.length >=3 && time_val.length <=4) {
        time_val = time_val.slice(0,time_val.length-2) + ':' + time_val.slice(time_val.length-2);
    }
    dateList.push([time1.attr('data-form-idx'), datum, time_val]);
  });
  
  if (hasErrors) {
      alert("Eine oder mehrere der Zeitangaben haben ein ungültiges Format!");
      return false;
  }
  
  // deduplication of selected dates and adding them to the actual django form
  for (i = dateList.length-1; i >= 0; i--) {
    var dateItem = dateList[i];
    var hasDuplicate = false;
    
    for (j = dateList.length-1; j >= 0; j--) {
        var dateItem2 = dateList[j];
        if (dateItem !== dateItem2 && dateItem[1] == dateItem2[1] && dateItem[2] == dateItem2[2]) { 
          hasDuplicate = true;
          break;
        }
    }
    
    if (hasDuplicate) {
      dateList.splice(i, 1);
    } else {
        // adding the date item to the actual django form
      addSuggestionToForm(dateItem[0], dateItem[1], dateItem[2]);
    }
  }
  
  $('#id_suggestions-TOTAL_FORMS').val(totalForms);
  
  return true; // now submit
});
