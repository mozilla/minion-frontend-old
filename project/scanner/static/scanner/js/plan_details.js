// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

$(document).ready(function() {
    // Register for change events on the popup so that we can respond
    // to those by updating the plan details div.
    $("#plan_dropdown").change(function(){
	var selectedValue = $(this).find(":selected").val();
	$.ajax({
            url: "/plan_details",
            data: {plan_name: selectedValue},
            //dataType: 'json',
            success: function(data) {
		$('#plan-details').html(data);
            }
        });
    });
});
