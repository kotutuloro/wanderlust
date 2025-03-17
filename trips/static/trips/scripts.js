// destination location call
$(document).on("input", "#destination-location-input", function () {
  if ($(this).val().length < 4) {
    return true;
  }

  $.ajax({
    type: "GET",
    url: $(this).attr("data-url"),
    data: { query: $(this).val() },
    success: function (data) {
      console.log(data);
    },
    error: function (data) {
      console.log(data);
    },
  });
});
