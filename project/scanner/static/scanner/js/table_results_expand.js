// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

$(document).ready(function() {
    $(".results_table_area").hide();
    //toggle the componenet with class msg_body
    $(".results_table_expander").click(function()
    {
        $(this).next(".results_table_area").toggle();
        if($(this).find($('.plus_minus')).text() == "+") {
            $(this).find($('.plus_minus')).text("-");
        } else {
            $(this).find($('.plus_minus')).text("+");
        }
    });
});
