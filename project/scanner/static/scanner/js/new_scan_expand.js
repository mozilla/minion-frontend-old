// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

$(document).ready(function() {
    $("#new_scan_advanced_options_hidden").hide();
    //toggle the componenet with class msg_body
    jQuery("#new_scan_advanced_options_expander").click(function()
    {
        $("#new_scan_advanced_options_hidden").slideToggle(500);
    });
});
