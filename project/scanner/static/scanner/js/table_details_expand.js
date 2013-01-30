// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

$(document).ready(function() {
    //toggle the componeent with class msg_body
    $(".details_table_expander").click(function()
    {
        $(this).next(".details_table_area").toggle();
        if($(this).find($('.plus_minus')).text() == "+") {
            $(this).find($('.plus_minus')).text("-");
        } else {
            $(this).find($('.plus_minus')).text("+");
        }
    });
});
